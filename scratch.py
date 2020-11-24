import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem, ParentProduct
from manage import manager
import keys.messages


test = Repair(monday=873866120)

for item in test.monday.create_inventory_items():
    pprint(item.__dict__)



print()

