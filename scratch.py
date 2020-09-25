import requests
import json
import os
from pprint import pprint

import settings

from objects import Repair

test = Repair(monday=760722760)

print(test.monday.end_of_day)

test.debug_print()

