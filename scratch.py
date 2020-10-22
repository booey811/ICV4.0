import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit
import keys.messages

repair = Repair(monday=811389476)

repair.monday.vend_sync()

repair.debug_print(debug="console")