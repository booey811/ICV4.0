import requests
import json
import os

import settings

from objects import Repair

test = Repair(monday=726460853)

print(test.monday.check_column_presence())