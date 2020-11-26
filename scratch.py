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

test = InventoryItem(878831862)

test.add_to_product_catalogue(gabe_id)

print()