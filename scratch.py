import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(monday=801017744)

repair.monday.add_to_zendesk()