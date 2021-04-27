import requests

class RasaClient(object):
    def __init__(self, url):
        self._base_url = url
        self._session = requests.Session()

    def _post_rasa(self, path, data):
        url = "{}/{}".format(self._base_url, path)
        response = self._session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def post_action(self, message, sender="default"):
        data = {"message": message, "sender": sender}
        return self._post_rasa("webhooks/rest/webhook", data)
