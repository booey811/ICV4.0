import requests
import json
import os
from pprint import pprint

import settings

from objects import Repair

test = Repair(monday=765530679)

print(test.monday.m_colour)