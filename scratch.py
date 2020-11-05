import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem
from manage import manager
import keys.messages


test = Repair(monday=837781515)

test.monday.adjust_stock_alt()

print()