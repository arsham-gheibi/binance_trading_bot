from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from app.celery import celery_app
from core.models import Signal, Target, Precision
import logging
import hmac
import hashlib


User = get_user_model()
logger = logging.getLogger(__name__)


def get_signiture(api_secret, query_string):
    return hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def find_symbol(text):
    text = text.split('\n')
    for t in text:
        t = t.lower()
        if t.__contains__('#'):
            try:
                t = t.split()[1].replace('#', '').upper()
                return t
            except IndexError:
                continue
    return ''


def get_signal_details(text):
    is_signal = True
    symbol = ''
    entry = 0
    targets = []
    stop_loss = 0
    order_type = 'LIMIT'
    side = ''
    target_side = ''
    precision = ''

    text = text.split('\n')
    for t in text:
        t = t.lower()
        if t.__contains__('#'):
            t = t.split()[1].replace('#', '').upper()
            symbol = t

    try:
        precision = Precision.objects.get(symbol=symbol)

        for t in text:
            t = t.lower()
            if t.__contains__('long entry zone'):
                t = t.split()[-1].split('-')
                side = 'BUY'
                target_side = 'SELL'
                if float(t[0]) < float(t[1]):
                    entry = round(float(t[1]), precision.tick_size)
                else:
                    entry = round(float(t[0]), precision.tick_size)

            elif t.__contains__('short entry zone'):
                t = t.split()[-1].split('-')
                side = 'SELL'
                target_side = 'BUY'
                if float(t[0]) < float(t[1]):
                    entry = round(float(t[0]), precision.tick_size)
                else:
                    entry = round(float(t[1]), precision.tick_size)

            if t.__contains__('target'):
                try:
                    targets.append(
                        round(float(t.split()[-1]), precision.tick_size))

                except ValueError:
                    continue

            if t.__contains__('stop-loss'):
                stop_loss = round(float(t.split()[-1]), precision.tick_size)

    except Precision.DoesNotExist:
        is_signal = False

    if len(targets) == 0:
        is_signal = False

    return is_signal, symbol, entry, targets, stop_loss,\
        order_type, side, target_side, precision


def create_new_signal(text):
    is_signal, symbol, entry, targets, stop_loss,\
        order_type, side, target_side, precision\
        = get_signal_details(text)

    if is_signal:
        print('entry is :', entry)
        try:
            signal = Signal.objects.create(
                precision=precision,
                message_text=text,
                symbol=symbol,
                order_type=order_type,
                side=side,
                time_frame='',
                entry=entry,
                stop_loss=stop_loss
            )

            logger.info(signal_detail_message.format(
                symbol=symbol,
                entry=entry,
                stop_loss=stop_loss,
                targets=targets
            ))

            num = 0
            for target_value in targets:
                num += 1
                if num == 1:
                    percent = 40
                elif num == 2:
                    percent = 30
                elif num == 3:
                    percent = 20
                elif num == 4:
                    percent = 10
                else:
                    percent = 0

                Target.objects.create(
                    value=target_value,
                    percent=percent,
                    num=num,
                    side=target_side,
                    signal=signal
                )

            users = User.objects.filter(is_active=True)
            for user in users:
                celery_app.send_task(
                    'core.tasks.open_new_position',
                    [user.id,
                     signal.id,
                     precision.qty_step],
                    queue=user.main_queue.name)

        except IntegrityError:
            pass


def is_signal_cancelled(text):
    cancel_message = 'target achieved before entering the entry zone'
    return text.lower().__contains__(cancel_message)


def is_signal_closed(text):
    close_message = 'closed at trailing stoploss after reaching take profit'
    return text.lower().__contains__(close_message)


# Emojis
blue_circle = '&#128309;'
green_circle = '&#128994;'
red_circle = '&#128308;'
money_bag = '&#128176;'
money_with_wings = '&#128184;'
woman_shrugging = '&#129335;&#127997;&#8205;&#9792;&#65039;'
check_mark_button = '&#9989;'
no_entry = '&#9940;'
joystick = '&#128377;&#65039;'

# Logger Messages
signal_detail_message = '#{symbol} {entry} {stop_loss} {targets}'
order_created_message = '#{symbol} Order Created for {user}'
order_creation_failed_message = '#{symbol} Order Creation Failed for {user}'
order_cancelled_message = '#{symbol} has been Cancelled for {user}'
order_closed_message = '#{symbol} has been Closed for {user}'
target_created_message = '#{symbol} Target Created for {user}'
stoploss_set_message = '#{symbol} StopLoss Set for {user}'
cant_open_position_due_qty =\
    "#{symbol} Can't Place this Order due Low Quantity {user}"

# Notifier Messages
reduce_only_target_message = """{emoji}
User: {user_name}
#{symbol} {side} Target {target_number} Achieved &#128640;
Price: ${price}
Quantity: {qty}
Profit/Loss: ${profit}{second_emoji}"""

reduce_only_message = """{emoji}
User: {user_name}
Closed #{symbol} {side}
Price: ${price}
Quantity: {qty}
Profit/Loss: ${profit}{second_emoji}
{closed_due}"""

not_reduce_only_message = """User: {user_name}
{side} {qty} #{symbol}
Entry: ${price}"""


closed_due_tp = f'All Targets Achived {check_mark_button}'
closed_due_manually = f'Manually Closed {joystick}'
