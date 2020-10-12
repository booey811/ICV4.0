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

test.monday.email="blahblah@blah.com"
test.monday.number="06564728104"
test.monday.name="ERICA BADU"

test.monday.add_to_zendesk()

test.debug_print(debug='console')