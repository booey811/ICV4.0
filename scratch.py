import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(vend='6ffc7cac-fb7b-8c53-11eb-12b8b4be5cb2')

repair.compare_app_objects("vend", "monday")