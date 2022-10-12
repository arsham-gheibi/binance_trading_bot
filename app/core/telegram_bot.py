import requests


class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params).json()
        try:
            return resp['result']['message_id']
        except KeyError:
            return 'cant'

    def editMessageText(self, chat_id, text, message_id):
        params = {'chat_id': chat_id, 'text': text,
                  'parse_mode': 'HTML', 'message_id': message_id}
        method = 'editMessageText'
        resp = requests.post(self.api_url + method, params)
        return resp
