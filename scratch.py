import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(test=True)
repair.monday = repair.MondayRepair(repair, created="Test")

repair.monday.adjust_gophr_data("666", name="ANOTHER TEST", delivery=True)