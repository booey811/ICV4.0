import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

test = Repair(zendesk=5646)

test.zendesk.convert_to_attributes()

test.zendesk.convert_to_monday()

pprint(test.monday.__dict__)

test.debug_print(console=True)

