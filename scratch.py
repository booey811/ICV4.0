import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

# test = Repair(vend=5901)

# test.vend.sale_closed()

test = Repair(zendesk=5901)

test.compare_app_objects("zendesk")