import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

test = Repair(monday=765530679)

data= {'event': {'app': 'monday',
           'boardId': 349212843,
           'changedAt': 1601633204.2622943,
           'columnId': 'dropdown8',
           'columnTitle': 'Notifications',
           'columnType': 'dropdown',
           'groupId': 'new_group49546',
           'isTopGroup': False,
           'originalTriggerUuid': None,
           'previousValue': {'chosenValues': [{'id': 1,
                                               'name': 'Booking Confirmed'}]},
           'pulseId': 765530679,
           'pulseName': 'Jeremiah Bullfrog',
           'subscriptionId': 20434895,
           'triggerTime': '2020-10-02T10:06:44.554Z',
           'triggerUuid': 'bb0a5b1cebed96c3968757e55ae13b58',
           'type': 'update_column_value',
           'userId': 4251271,
           'value': {'chosenValues': [{'id': 1, 'name': 'Booking Confirmed'},
                                      {'id': 2, 'name': 'Device Received'}]}}}





print(test.monday.dropdown_value_webhook_comparison(data))

test.debug_print(console=True)

