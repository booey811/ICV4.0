import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit
import keys.messages

repair = Repair(zendesk=5901)

repair.zendesk.convert_to_monday()
repair.add_to_monday()

repair.debug_print(debug="console")