import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem
import keys.messages

repair = Repair(monday=824488881)

repair.monday.adjust_stock_alt()