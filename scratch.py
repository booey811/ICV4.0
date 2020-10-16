import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(monday=796559335)

col_val = create_column_value(id="link1", column_type=ColumnType.link, value="https://www.google.com")

repair.monday.item.change_column_value(col_val)