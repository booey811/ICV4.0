import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem
import keys.messages

test = Repair(monday=824923360)

test.monday.adjust_stock_alt()

print()