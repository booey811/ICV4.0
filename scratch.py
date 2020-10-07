import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

test = Repair(zendesk=5751)

test.zendesk.multiple_pulse_check(check_type="status")

test.zendesk.notifications_check_and_send(5)

test.debug_print(console=True)

pprint(test.monday.__dict__)

