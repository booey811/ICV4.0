import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem, ParentProduct, ScreenRefurb
from manage import manager
import keys.messages

gabe_id = 4251271


# ================================================================================================
# ================================================================================================
# ================================================================================================


test = ParentProduct(868238254)

pprint(test.__dict__)


test.refurb_order_creation(gabe_id)

print()