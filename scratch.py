import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem, ParentProduct, RefurbGroup, NewRefurbUnit
from manage import manager
import keys.messages

gabe_id = 4251271

# =====================================================================================================================
# =====================================================================================================================
print("Begin INIT")
test = Repair(monday=889287132)
print("End INIT")

print("Begin Process")
test.monday.stock_checker(gabe_id)
print("End Process")

print()

