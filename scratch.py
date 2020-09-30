import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

test = Repair(zendesk=5692)

test.zendesk.convert_to_attributes()

test.zendesk.convert_to_monday()

print(test.zendesk.ticket.organization.name)


pprint(test.monday.__dict__)


