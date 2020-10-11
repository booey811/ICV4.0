import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair
import keys.messages

test = Repair(monday=783827869)

print(test.monday.textmessage_select_and_parse())