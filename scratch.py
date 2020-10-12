import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair
import keys.messages

# test = Repair(vend=5901)

# test.vend.sale_closed()

test = Repair(monday=791382431)

test.monday.add_to_zendesk()