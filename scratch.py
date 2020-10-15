import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(vend="6ffc7cac-fb7b-bffe-11eb-0e250b145031")

repair.vend.convert_to_monday_codes()
repair.add_to_monday()
repair.vend.parked_sale_adjustment()