import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

repair = Repair(monday=783827869)

repair.zendesk.notifications_check_and_send(2)