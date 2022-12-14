from django.contrib.auth import get_user_model
from django.core.cache import cache
from app.celery import celery_app
from app.settings import BINANCE_PRIVATE_STREAM, BINANCE_KEEP_ALIVE_PERIOD,\
    TELEGRAM_API_TOKEN, TELEGRAM_DEBUG_API_TOKEN
from core.models import Order, TargetOrder, Signal, Precision
from core.telegram_bot import BotHandler
from core.utils import get_signiture
from core.endpoints import ORDER_ENDPOINT, EXCHANGE_INFO, SYMBOLS,\
    CHANGE_INITIAL_LEVERAGE, CHANGE_MARGIN_TYPE, CHANGE_POSITION_MODE,\
    CANCEL_OPEN_ORDERS, USER_DATA_STREAM, POSITIONS
from core.messages import order_created_message, order_cancelled_message,\
    order_closed_message, target_created_message, stoploss_set_message,\
    not_reduce_only_message, closed_due_tp, closed_due_manually, blue_circle,\
    green_circle, red_circle, money_bag, money_with_wings, woman_shrugging,\
    order_creation_failed_message, cant_open_position_due_qty,\
    cant_open_position_due_black_list
from urllib.parse import urlencode
import requests
import logging
import time
import websocket
import json
import threading


User = get_user_model()
logger = logging.getLogger(__name__)


@celery_app.task
def open_new_position(user_id, signal_id, precision_qty_step):
    user = User.objects.get(id=user_id)
    signal = Signal.objects.get(id=signal_id)
    if not signal.precision.is_blacklisted:
        headers = {'X-MBX-APIKEY': user.api_key}
        params = {
            'symbol': signal.symbol,
            'timestamp': int(time.time() * 1000)
        }

        query_string = urlencode(params)
        params['signature'] = get_signiture(user.api_secret, query_string)
        res = requests.get(
            POSITIONS,
            params=params,
            headers=headers
        )

        content = json.loads(res.content.decode('utf-8'))
        entry_price = float(content[0]['entryPrice'])

        if entry_price > 0:
            quantity = float(content[0]['positionAmt'])
            position_side = content[0]['positionSide']

            if quantity > 0:
                side = 'SELL'
            elif quantity < 0:
                side = 'BUY'

            params = {
                'symbol': signal.symbol,
                'side': side,
                'type': 'MARKET',
                'positionSide': position_side,
                'quantity': abs(quantity),
                'reduceOnly': True,
                'timestamp': int(time.time() * 1000)
            }

            query_string = urlencode(params)
            params['signature'] = get_signiture(user.api_secret, query_string)
            res = requests.post(
                ORDER_ENDPOINT,
                params=params,
                headers=headers
            )

            content = json.loads(res.content.decode('utf-8'))

            try:
                order_status = content['status']
                order_id = content['orderId']

            except KeyError:
                print("Order Didn't Close")

            time.sleep(0.5)

        params = {
            'symbol': signal.symbol,
            'timestamp': int(time.time() * 1000)
        }

        query_string = urlencode(params)
        params['signature'] = get_signiture(user.api_secret, query_string)
        requests.delete(
            CANCEL_OPEN_ORDERS,
            params=params,
            headers=headers
        )

        # clinet percentage / 100 * balance / entry

        quantity_client = round(
            (user.usage_percentage / 100 * user.balance)
            * 10 / signal.entry, precision_qty_step)

        if quantity_client > signal.precision.max_trading_qty:
            quantity_client = signal.precision.max_trading_qty

        target_qty = round(
            15 / 100 * quantity_client, signal.precision.qty_step)

        can_open_position = target_qty >= signal.precision.min_trading_qty

        if can_open_position:
            params = {
                'symbol': signal.symbol,
                'side': signal.side,
                'positionSide': signal.position_side,
                'type': signal.order_type,
                'quantity': quantity_client,
                'reduceOnly': signal.reduce_only,
                'price': signal.entry,
                'timeInForce': signal.time_in_force,
                'timestamp': int(time.time() * 1000)
            }

            query_string = urlencode(params)
            params['signature'] = get_signiture(user.api_secret, query_string)
            res = requests.post(
                ORDER_ENDPOINT,
                params=params,
                headers=headers
            )

            content = json.loads(res.content.decode('utf-8'))

            try:
                order_status = content['status']
                order_id = content['orderId']

                Order.objects.create(
                    id=order_id,
                    user=user,
                    signal=signal,
                    type=signal.order_type,
                    qty=quantity_client
                )

                if order_status == 'NEW':
                    logger.info(order_created_message.format(
                        symbol=signal.symbol,
                        user=user.user_name
                    ))

                    celery_app.send_task(
                        'core.tasks.is_filled_or_cancel',
                        [user.id, order_id, signal.symbol],
                        countdown=14400,
                        queue=user.main_queue.name
                    )

                logger.info('Cancel Count Down Setted')

            except KeyError:
                logger.warn(order_creation_failed_message.format(
                    symbol=signal.symbol,
                    user=user.user_name
                ))
                print(content)
        else:
            logger.info(
                cant_open_position_due_qty.format(
                    symbol=signal.symbol,
                    user=user.user_name
                ))

    else:
        logger.info(
            cant_open_position_due_black_list.format(
                symbol=signal.symbol,
                user=user.user_name
            ))


@celery_app.task
def set_precision():
    logger.info('Setting Precisions ..')
    res = requests.get(EXCHANGE_INFO)
    symbols = json.loads(res.content.decode('utf-8'))['symbols']
    for symbol in symbols:
        filters = symbol['filters']
        name = symbol['symbol']
        tick_size = str(filters[0]['tickSize'])
        max_trading_qty = filters[1]['maxQty']
        min_trading_qty = filters[1]['minQty']
        qty_step = str(filters[1]['stepSize'])

        precision, _ = Precision.objects.get_or_create(symbol=name)
        precision.tick_size = len(tick_size.replace('.', '')) - 1
        precision.max_trading_qty = max_trading_qty
        precision.min_trading_qty = min_trading_qty
        precision.qty_step = len(qty_step.replace('.', '')) - 1
        precision.save()

    logger.info('Precisions Set')


@celery_app.task
def set_leverage():
    logger.info('Setting Leverage ..')
    users = User.objects.filter(is_active=True)
    res = requests.get(EXCHANGE_INFO)
    symbols = json.loads(res.content.decode('utf-8'))['symbols']
    for user in users:
        celery_app.send_task(
            'core.tasks.user_set_leverage',
            [user.id, symbols],
            queue=user.main_queue.name
        )

    logger.info('Leverage Set')


@celery_app.task
def user_set_leverage(user_id, symbols):
    user = User.objects.get(id=user_id)
    headers = {'X-MBX-APIKEY': user.api_key}
    res = requests.get(SYMBOLS)
    symbols = json.loads(res.content.decode('utf-8'))

    params = {
        'dualSidePosition': False,
        'timestamp': int(time.time() * 1000)
    }

    query_string = urlencode(params)
    params['signature'] = get_signiture(user.api_secret, query_string)
    requests.post(
        CHANGE_POSITION_MODE,
        params=params,
        headers=headers
    )

    for symbol in symbols:
        name = symbol['symbol']
        params = {
            'symbol': name,
            'leverage': 10,
            'timestamp': int(time.time() * 1000)
        }

        query_string = urlencode(params)
        params['signature'] = get_signiture(user.api_secret, query_string)
        requests.post(
            CHANGE_INITIAL_LEVERAGE,
            params=params,
            headers=headers
        )

        params = {
            'symbol': name,
            'marginType': 'CROSSED',
            'timestamp': int(time.time() * 1000)
        }

        query_string = urlencode(params)
        params['signature'] = get_signiture(user.api_secret, query_string)
        requests.post(
            CHANGE_MARGIN_TYPE,
            params=params,
            headers=headers
        )


@celery_app.task
def is_filled_or_cancel(user_id, order_id, symbol):
    user = User.objects.get(id=user_id)
    headers = {'X-MBX-APIKEY': user.api_key}
    params = {
        'symbol': symbol,
        'orderId': order_id,
        'timestamp': int(time.time() * 1000)
    }

    query_string = urlencode(params)
    params['signature'] = get_signiture(user.api_secret, query_string)
    res = requests.delete(
        ORDER_ENDPOINT,
        params=params,
        headers=headers
    )

    logger.info(f'#{symbol} is_filled_or_cancel {res}')


@celery_app.task
def cancel_order(user_id, symbol):
    user = User.objects.get(id=user_id)
    headers = {'X-MBX-APIKEY': user.api_key}
    params = {
        'symbol': symbol,
        'timestamp': int(time.time() * 1000)
    }

    query_string = urlencode(params)
    params['signature'] = get_signiture(user.api_secret, query_string)
    res = requests.delete(
        CANCEL_OPEN_ORDERS,
        params=params,
        headers=headers
    )
    content = json.loads(res.content.decode('utf-8'))
    cancelled = content['code'] == 200

    if cancelled:
        order = Order.objects.filter(
            user=user,
            is_cancelled=False,
            signal__symbol=symbol
        ).first()

        if order is not None:
            order.is_cancelled = True
            order.save()

        logger.warn(order_cancelled_message.format(
            symbol=symbol,
            user=user.user_name
        ))


@celery_app.task
def close_and_cancel_order(user_id, symbol):
    user = User.objects.get(id=user_id)
    headers = {'X-MBX-APIKEY': user.api_key}
    params = {
        'symbol': symbol,
        'timestamp': int(time.time() * 1000)
    }

    query_string = urlencode(params)
    params['signature'] = get_signiture(user.api_secret, query_string)
    res = requests.get(
        POSITIONS,
        params=params,
        headers=headers
    )

    content = json.loads(res.content.decode('utf-8'))
    entry_price = float(content[0]['entryPrice'])

    if entry_price > 0:
        quantity = float(content[0]['positionAmt'])
        position_side = content[0]['positionSide']

        if quantity > 0:
            side = 'SELL'
        elif quantity < 0:
            side = 'BUY'

        params = {
            'symbol': symbol,
            'side': side,
            'positionSide': position_side,
            'type': 'MARKET',
            'quantity': abs(quantity),
            'reduceOnly': True,
            'timestamp': int(time.time() * 1000)
        }

        query_string = urlencode(params)
        params['signature'] = get_signiture(user.api_secret, query_string)
        res = requests.post(
            ORDER_ENDPOINT,
            params=params,
            headers=headers
        )

        content = json.loads(res.content.decode('utf-8'))

        try:
            content['status']
            content['orderId']

        except KeyError:
            print("Order Didn't Close")

        order = Order.objects.filter(
            user=user,
            is_closed=False,
            signal__symbol=symbol
        ).first()

        if order is not None:
            order.is_closed = True
            order.save()

        logger.warn(order_closed_message.format(
            symbol=symbol,
            user=user.user_name
        ))

    params = {
        'symbol': symbol,
        'timestamp': int(time.time() * 1000)
    }

    query_string = urlencode(params)
    params['signature'] = get_signiture(user.api_secret, query_string)
    res = requests.delete(
        CANCEL_OPEN_ORDERS,
        params=params,
        headers=headers
    )


@celery_app.task
def user_data_stream(user_id):
    user = User.objects.get(id=user_id)
    headers = {'X-MBX-APIKEY': user.api_key}
    res = requests.post(
        USER_DATA_STREAM,
        headers=headers
    )

    listen_key = json.loads(res.content.decode('utf-8'))['listenKey']

    if user.bot_token is not None:
        bot = BotHandler(user.bot_token)
    else:
        bot = BotHandler(TELEGRAM_API_TOKEN)

    inspectors = [847873714, 1815923016, 104789594, user.telegram_id]
    user_inspectors = user.inspector_set.all()

    for inspector in user_inspectors:
        inspectors.append(inspector.code)

    def analyze_message(message, bot):
        symbol = message['o']['s']
        side = message['o']['S']
        create_type = message['o']['ot']
        qty = float(message['o']['q'])
        order_id = message['o']['i']
        price = float(message['o']['L'])
        reduce_only = message['o']['R']
        profit = round(float(message['o']['rp']), 4)
        percent_profit = round(profit * 100 / user.balance, 4)

        if reduce_only:
            if percent_profit > 0:
                emoji = green_circle
                second_emoji = money_bag
            elif percent_profit < -0.06:
                emoji = red_circle
                second_emoji = money_with_wings
            else:
                emoji = blue_circle
                second_emoji = woman_shrugging

            side = 'Short' if side == 'BUY' else 'Long'
            try:
                target_order = TargetOrder.objects.get(id=order_id)
                if target_order.target.num == 4:
                    is_target_hitted = False
                    closed_due = closed_due_tp
                else:
                    is_target_hitted = True
                    closed_due = None

                message = user.get_notifier_message(
                    is_target_hitted=is_target_hitted,
                    emoji=emoji,
                    symbol=symbol,
                    side=side,
                    price=price,
                    qty=qty,
                    profit=profit,
                    second_emoji=second_emoji,
                    target_number=target_order.target.num,
                    closed_due=closed_due
                )

            except TargetOrder.DoesNotExist:
                if create_type == 'TAKE_PROFIT_MARKET':
                    closed_due = closed_due_tp
                elif create_type == 'STOP_MARKET'\
                        or create_type == 'MARKET':
                    closed_due = ''
                else:
                    closed_due = closed_due_manually

                message = user.get_notifier_message(
                    is_target_hitted=False,
                    emoji=emoji,
                    symbol=symbol,
                    side=side,
                    price=price,
                    qty=qty,
                    profit=profit,
                    second_emoji=second_emoji,
                    target_number=None,
                    closed_due=closed_due
                )

        elif not reduce_only:
            side = 'Longed' if side == 'BUY' else 'Shorted'
            message = not_reduce_only_message.format(
                user_name=user.user_name,
                side=side,
                qty=qty,
                symbol=symbol,
                price=price
            )

        for inspector in inspectors:
            time.sleep(1)
            bot.send_message(inspector, message)

    def keep_alive():
        while True:
            requests.put(USER_DATA_STREAM, headers=headers)
            time.sleep(BINANCE_KEEP_ALIVE_PERIOD)

    def on_error(ws, error):
        bot = BotHandler(TELEGRAM_DEBUG_API_TOKEN)
        bot.send_message(
            847873714,
            f'{user.user_name} Binance Stream error \n {error}'
        )

    def on_close(ws, close_status_code, close_msg):
        bot = BotHandler(TELEGRAM_DEBUG_API_TOKEN)
        bot.send_message(
            847873714,
            f'{user.user_name} Binance Stream got closed \n {close_msg}'
        )

        requests.delete(USER_DATA_STREAM, headers=headers)
        time.sleep(10)
        stream_task = celery_app.send_task(
            'core.tasks.user_data_stream',
            [user.id],
            time_limit=31536000,
            queue=user.stream_queue.name
        )

        task_id = cache.get(user.id)
        cache.set(user.id, stream_task.task_id, 31536000)
        celery_app.control.terminate(task_id)

    def on_open(ws):
        bot = BotHandler(TELEGRAM_DEBUG_API_TOKEN)
        bot.send_message(
            847873714,
            f'Opened Stream Connection {user.user_name}'
        )

        logger.info(f'Opened Stream Connection {user.user_name}')
        threading.Thread(target=keep_alive).start()

    def on_message(ws, message):
        message = json.loads(message)
        if message['e'] == 'ORDER_TRADE_UPDATE':
            order_id = message['o']['i']
            order_status = message['o']['X']

            if order_status == 'FILLED':
                try:
                    time.sleep(1)
                    order = Order.objects.get(id=order_id)
                    targets = order.signal.target_set.all()

                    logger.info('Setting Targets and TP/SL ..')

                    for target in targets:
                        if target.num != targets.count():
                            qty = round(
                                target.percent / 100 * order.qty,
                                target.signal.precision.qty_step)

                            params = {
                                'symbol': target.signal.symbol,
                                'side': target.side,
                                'positionSide': target.signal.position_side,
                                'type': order.type,
                                'quantity': qty,
                                'reduceOnly': True,
                                'price': target.value,
                                'timeInForce': target.signal.time_in_force,
                                'timestamp': int(time.time() * 1000)
                            }

                            query_string = urlencode(params)
                            params['signature'] = get_signiture(
                                user.api_secret, query_string)
                            res = requests.post(
                                ORDER_ENDPOINT,
                                params=params,
                                headers=headers
                            )

                            content = json.loads(res.content.decode('utf-8'))
                            print(content, target.value)

                        elif target.num == targets.count():
                            params = {
                                'symbol': target.signal.symbol,
                                'side': target.side,
                                'type': 'TAKE_PROFIT_MARKET',
                                'stopPrice': target.value,
                                'closePosition': True,
                                'timeInForce': target.signal.time_in_force,
                                'priceProtect': True,
                                'timestamp': int(time.time() * 1000)
                            }

                            query_string = urlencode(params)
                            params['signature'] = get_signiture(
                                user.api_secret, query_string)
                            res = requests.post(
                                ORDER_ENDPOINT,
                                params=params,
                                headers=headers
                            )

                            content = json.loads(res.content.decode('utf-8'))
                            print(content)

                            params = {
                                'symbol': target.signal.symbol,
                                'side': target.side,
                                'type': 'STOP_MARKET',
                                'stopPrice': target.signal.stop_loss,
                                'closePosition': True,
                                'timeInForce': target.signal.time_in_force,
                                'priceProtect': True,
                                'timestamp': int(time.time() * 1000)
                            }

                            query_string = urlencode(params)
                            params['signature'] = get_signiture(
                                user.api_secret, query_string)
                            requests.post(
                                ORDER_ENDPOINT,
                                params=params,
                                headers=headers
                            )

                            logger.info(stoploss_set_message.format(
                                symbol=target.signal.symbol,
                                user=user.user_name
                            ))

                        TargetOrder.objects.create(
                            id=content['orderId'],
                            order=order, target=target)

                        logger.info(target_created_message.format(
                            symbol=target.signal.symbol,
                            user=user.user_name
                        ))

                except Order.DoesNotExist:
                    try:
                        time.sleep(1)
                        target = TargetOrder.objects.get(id=order_id).target
                        target.hit = True
                        target.save()

                        if target.num == 1:
                            params = {
                                'symbol': target.signal.symbol,
                                'side': target.side,
                                'type': 'STOP_MARKET',
                                'stopPrice': target.signal.entry,
                                'closePosition': True,
                                'timeInForce': target.signal.time_in_force,
                                'priceProtect': True,
                                'timestamp': int(time.time() * 1000)
                            }

                            query_string = urlencode(params)
                            params['signature'] = get_signiture(
                                user.api_secret, query_string)
                            requests.post(
                                ORDER_ENDPOINT,
                                params=params,
                                headers=headers
                            )

                            logger.info(target_created_message.format(
                                symbol=target.signal.symbol,
                                user=user.user_name
                            ))

                    except TargetOrder.DoesNotExist:
                        logger.warn('THERE IS NO TARGET OR ORDER WITH THIS ID')

                finally:
                    analyze_message(message, bot)

        elif message['e'] == 'listenKeyExpired':
            requests.delete(USER_DATA_STREAM, headers=headers)
            time.sleep(10)
            stream_task = celery_app.send_task(
                'core.tasks.user_data_stream',
                [user.id],
                time_limit=31536000,
                queue=user.stream_queue.name
            )

            task_id = cache.get(user.id)
            cache.set(user.id, stream_task.task_id, 31536000)
            celery_app.control.terminate(task_id)

    url = f'{BINANCE_PRIVATE_STREAM}/ws/{listen_key}'
    ws = websocket.WebSocketApp(
        url,
        headers,
        on_open,
        on_message,
        on_error,
        on_close
    )

    ws.run_forever()
