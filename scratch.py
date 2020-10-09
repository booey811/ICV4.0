import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

repair = Repair(monday=783827869)

pprint(repair.monday.__dict__)

repair.monday.gophr_booking()

repair.debug_print(debug="console")