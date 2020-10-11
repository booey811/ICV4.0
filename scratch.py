import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair
import keys.messages

test = Repair(monday=783827869)



if test.multiple_pulse_check_repair("general"):
    for obj in test.associated_pulse_results:
        pulse = Repair(monday=obj.id)
        pulse.monday.add_update(update="TEST FROM SCRATCH", user="email")

test.debug_print(debug="console")