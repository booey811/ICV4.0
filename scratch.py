import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

test = Repair(monday=791447966)

test.monday.adjust_stock()

