import requests
import json
import os
from pprint import pprint

import settings

from objects import Repair

test = Repair(monday=760722760)


test.monday.adjust_stock()

test.debug_print()

