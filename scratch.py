import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit
import keys.messages

repair = Repair(vend="6ffc7cac-fb7b-8099-11eb-13a870ba7d71")

repair.vend.parked_sale_adjustment()