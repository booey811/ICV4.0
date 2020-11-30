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

print("Beginning INIT")
test = NewRefurbUnit(881443933, gabe_id)
print("Finished INIT")

print("Starting Func")
test.calculate_line()
print("Ending Func")

