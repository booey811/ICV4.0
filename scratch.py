from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem, ParentProduct
from manage import manager
import keys.messages

test = InventoryItem(867599202)

pprint(test.__dict__)

test.add_to_product_catalogue(4251271)