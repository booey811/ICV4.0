import requests
import os
import json
from pprint import pprint

import settings



class BackMarketSale():


    api_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Language': 'en-gb',
        'Authorization': 'Basic {}'.format(os.environ['BACKMARKET']),
        'User-Agent': 'iCorrect'
    }

    def __init__(self):

        pass

    def get_order(self, back_market_id):

        # Test Request

        url = 'https://www.backmarket.fr/ws/orders/{}'.format(back_market_id)

        response = requests.request('GET', url=url, headers=self.api_headers)

        print(response)

        formatted = json.loads(response.text)

        pprint(formatted)



test = BackMarketSale()

test.get_order(9574898)