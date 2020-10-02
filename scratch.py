import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

test = Repair(monday=765530679)

data= {'event': {'userId': 4251271, 'originalTriggerUuid': None, 'boardId': 349212843, 'groupId': 'new_group49546', 'pulseId': 765530679, 'pulseName': 'Jeremiah Bullfrog', 'columnId': 'dropdown8', 'columnType': 'dropdown', 'columnTitle': 'Notifications', 'value': None, 'previousValue': {'chosenValues': [{'id': 3, 'name': 'Repaired'}]}, 'changedAt': 1601646222.1596475, 'isTopGroup': False, 'type': 'update_column_value', 'app': 'monday', 'triggerTime': '2020-10-02T13:43:50.245Z', 'subscriptionId': 20434895, 'triggerUuid': '45aba7891112874c4bae3bcdd1d72bb8'}}

pprint(data)


for value in webhook_data["event"]["value"]["chosenValues"]