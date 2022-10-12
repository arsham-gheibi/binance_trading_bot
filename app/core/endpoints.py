from django.conf import settings
from urllib.parse import urljoin


BINANCE_ENDPOINT = settings.BINANCE_ENDPOINT


SYMBOLS = urljoin(BINANCE_ENDPOINT, '/fapi/v1/ticker/price')
CHANGE_POSITION_MODE = urljoin(BINANCE_ENDPOINT, '/fapi/v1/positionSide/dual')
PLACE_NEW_ORDER = urljoin(BINANCE_ENDPOINT, '/fapi/v1/order')
CHANGE_INITIAL_LEVERAGE = urljoin(BINANCE_ENDPOINT, '/fapi/v1/leverage')
CHANGE_MARGIN_TYPE = urljoin(BINANCE_ENDPOINT, '/fapi/v1/marginType')
EXCHANGE_INFO = urljoin(BINANCE_ENDPOINT, '/fapi/v1/exchangeInfo')
OPEN_ORDERS = urljoin(BINANCE_ENDPOINT, '/fapi/v1/openOrders')
POSITIONS = urljoin(BINANCE_ENDPOINT, '/fapi/v2/positionRisk')
CANCEL_OPEN_ORDERS = urljoin(BINANCE_ENDPOINT, '/fapi/v1/allOpenOrders')
CANCEL_ACTIVE_ORDER = urljoin(BINANCE_ENDPOINT, '/fapi/v1/order')
ACCOUNT_BALANCE = urljoin(BINANCE_ENDPOINT, '/fapi/v2/balance')
USER_DATA_STREAM = urljoin(BINANCE_ENDPOINT, '/fapi/v1/listenKey')
COUNT_DOWN_CANCEL = urljoin(
    BINANCE_ENDPOINT, '/fapi/v1/countdownCancelAll')
