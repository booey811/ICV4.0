import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem
from manage import manager
import keys.messages


test = CountItem(840151447)

for item in test.inventory_items:
    print(item.change_multiple_column_values({"status6": {"label": "Add to Order"}}))