import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem
import keys.messages

test= OrderItem(824508892)

print(test.add_to_stock())
