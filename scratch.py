import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(monday=794401438)



if repair.multiple_pulse_check_repair():
    for obj in repair.associated_pulse_results:
        pulse = Repair(monday=obj.id)
        pulse.monday.add_update(update="LATEST COMMENT", user="email")
else:
    repair.compare_app_objects("zendesk")
    repair.monday.add_update(update="LATEST COMMENT ELSE ROUTE", user="email")
