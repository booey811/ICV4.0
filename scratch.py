import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

repair = Repair(zendesk=5751)

print(repair.zendesk.__dict__)

repair.monday.add_update("TESTER", user="email", status="Awaiting Confirmation")

repair.debug_print(debug='console')