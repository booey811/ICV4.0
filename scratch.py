import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit
import keys.messages

repair = Repair(test=True)

test = Repair(monday=798423274)

test.monday.convert_to_vend_codes()

print(test.monday.repair_names)
