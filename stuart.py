import requests
import os
import json
from pprint import pprint


class BackMarketSale:
    api_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Language': 'en-gb',
        'User-Agent': 'iCorrect'
    }

    def __init__(self, production=False):

        if production:
            url_start = 'https://preprod.backmarket.fr/ws'
            self.api_headers['Authorization'] = 'Basic {}'.format(os.environ['BACKMARKET'])
        else:
            self.api_headers['Authorization'] = 'Basic {}'.format(os.environ['BACKMARKETSAND'])
            url_start = 'https://www.backmarket.fr/ws'

    def get_order(self, back_market_id):

        # Test Request
        url = '{}/orders/{}'.format(self.url_start, back_market_id)
        response = requests.request('GET', url=url, headers=self.api_headers)
        print(response)
        formatted = json.loads(response.text)
        pprint(formatted)

    def get_all_listings(self):
        pass


test = BackMarketSale()

test.get_order(9574898)
