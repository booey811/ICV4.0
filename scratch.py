import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem
import keys.messages

order_item = OrderItem(824798101)

Repair.MondayRepair(repair_object=Repair(test=True), created=True).add_update(non_main=[order_item.id, 4251271, 822509956], user="error", notify="There was an issue while processing your stock order - please check and try again", status=["status3", "Check Quantities"])
