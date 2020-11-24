import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem, ParentProduct
from manage import manager
import keys.messages

gabe_id = 4251271

# =====================================================================================================================
# =====================================================================================================================

test = Repair(monday=871636801)

test.monday.adjust_stock_alt()

print()
