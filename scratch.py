import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

test = Repair(monday=765530679)

test.monday.status_to_notification("Booking Confirmed")

