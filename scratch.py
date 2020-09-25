import requests
import json
import os
from pprint import pprint

import settings

from objects import Repair

test = Repair(monday=760722760)

print(test.monday.notifications)

test.debug_print(console=True)
