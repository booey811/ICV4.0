import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair
import keys.messages

repair = Repair(monday=783827869)

print(repair.monday.textlocal_notification())

