import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem
import keys.messages

test = Repair(monday=796559335)

print(test.monday.new_end_of_day)