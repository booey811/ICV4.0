import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(vend='6b530743-1938-ba07-11eb-12abe7f66b7e')

repair.compare_app_objects("vend", "monday")

repair.vend.adjust