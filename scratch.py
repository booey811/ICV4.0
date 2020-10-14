import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(monday=794402584)

repair.monday.convert_to_vend_codes()
repair.vend = Repair.VendRepair(repair)
repair.vend.create_eod_sale()

pprint(repair.vend.sale_to_post.__dict__)

repair.debug_print(debug="console")