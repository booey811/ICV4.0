import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit, OrderItem, InventoryItem, CountItem
from manage import manager
import keys.messages


manager.add_update(824488881, "system", notify=["TEST NOTIFY", 4251271])