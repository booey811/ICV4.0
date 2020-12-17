import requests
import os
import json
from pprint import pprint

import settings


class BackMarketSale:
    api_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Language': 'en-gb',
        'User-Agent': 'iCorrect'
    }

    def __init__(self, production=False):

        if production:
            self.api_headers['Authorization'] = 'Basic {}'.format(os.environ['BACKMARKET'])
            self.url_start = 'https://www.backmarket.fr/ws'
        else:
            self.api_headers['Authorization'] = 'Basic {}'.format(os.environ['BACKMARKETSAND'])
            self.url_start = 'https://preprod.backmarket.fr/ws'

    def get_order(self, back_market_id):

        url = '{}/orders/{}'.format(self.url_start, back_market_id)
        response = requests.request('GET', url=url, headers=self.api_headers)
        print(response)
        formatted = json.loads(response.text)
        pprint(formatted)

    def edit_listing(self, catalog_string, test=False):

        url = '{}/listings'.format(self.url_start)
        print(catalog_string)
        if test:
            body = self.standard_catalog()
        else:
            body = {
                "encoding": "latin1",
                "delimiter": ";",
                "quotechar": "\"",
                "catalog": catalog_string
            }

        print(body)

        body = json.dumps(body)
        response = requests.request('POST', url=url, headers=self.api_headers, data=body)

        print(response)
        print(response.text)

    def create_catalog_string(self, listing_model):

        catalog = ''
        headers_list = []

        for item in listing_model:
            headers_list.append(item)

        headers_string = ';'.join(headers_list) + ';\\n'

        values_list = []

        for item in listing_model:
            values_list.append(str(listing_model[item]))

        values_string = ';'.join(values_list)

        final_string = headers_string + values_string + ';'

        return final_string

    def format_listing_model(self, backmarket_id, sku, quantity, price, grading, touchid_broken=False):

        required = {
            'backmarket_id': int(backmarket_id),  # REQUIRED[int] - Backmarket Product ID (Must be known)
            'sku': str(sku),  # REQUIRED[string] - SKU of offer, taken from backmarket
            'quantity': int(quantity),  # REQUIRED[string] - Quantity of units available for this sale
            'price': int(price),  # REQUIRED[float] - Price of Sale
            'state': int(grading),  # REQUIRED[int] - Grading of iPhone
            'warranty': 12,  # REQUIRED[int] - Months of Warranty (6/12 minimum??)
        }

        optional = {
            'comment': None,  # [string:500] Comment for the sale (description)
            'currency': None,  # [string:10] Type of currency (Defaults to EUR)
            'shipper_1': None,  # [string:**kwargs] Company that will ship the sale
            'shipping_price_1': None,  # [float] Cost of this shipping option
            'shipper_delay_1': None,  # [float] # Delay before the package will be collected (in hours)
        }

        for item in optional:
            if optional[item]:
                required[item] = optional[item]

        return required

    def standard_catalog(self):

        body = {
            "encoding": "latin1",
            "delimiter": ";",
            "quotechar": "\"",
            "header": True,
            "catalog": "sku;backmarket_id;quantity;warranty_delay;price;state;\n1111111111112;1151;2;6;180;2;\n1111111111113;1151;13;12;220;1;"
        }

        return body


test = BackMarketSale()

test.edit_listing(catalog_string='', test=True)
