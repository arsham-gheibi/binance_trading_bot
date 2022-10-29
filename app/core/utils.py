from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from app.celery import celery_app
from core.models import Signal, Target, Precision
from core.messages import signal_detail_message
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
                    percent = 30
                elif num == 2:
                    percent = 20
                elif num == 3:
                    percent = 30
                elif num == 4:
                    percent = 30
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


def is_signal_closed_or_cancelled(text):
    close_message = 'closed at trailing stoploss after reaching take profit'
    cancel_message = 'target achieved before entering the entry zone'
    return \
        text.lower().__contains__(close_message) or \
        text.lower().__contains__(cancel_message)


def analyze_reply_message(message):
    text = message['text']
    try:
        reply_text = message['reply_to_message']['text']
        symbol = find_symbol(reply_text)
        signal = Signal.objects.filter(symbol=symbol).first()

        if signal is not None:
            if is_signal_closed_or_cancelled(text):
                users = User.objects.filter(is_active=True)
                for user in users:
                    celery_app.send_task(
                        'core.tasks.close_and_cancel_order',
                        [user.id, signal.symbol],
                        queue=user.main_queue.name
                    )

                    logger.info(
                        f'#{signal.symbol} Signal is Closed/Cancelled')
            else:
                # Sending Signal as a reply message to another Signal
                create_new_signal(text)
        else:
            # Sending Signal as a reply message to some message
            create_new_signal(text)
    except KeyError:
        # Sending Signal as a normal telegram message
        create_new_signal(text)
