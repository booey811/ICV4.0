import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(monday=794402584)

repair.monday.adjust_stock()

repair.debug_print(debug="console")

