import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit
import keys.messages

repair = Repair(monday=803866624)

repair.monday.adjust_stock()
