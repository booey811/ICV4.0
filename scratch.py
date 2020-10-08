import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

repair = Repair(zendesk=5849)

repair.zendesk.email = "iavdawdjhv@isefgjsfb.com"
repair.zendesk.number = "iavdawdjhv@isefgjsfb.com"
repair.zendesk.name = "iavdawdjhv@isefgjsfb.com"

print(repair.search_user().name)




