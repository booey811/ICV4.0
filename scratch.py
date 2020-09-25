import requests
import json
import os
from pprint import pprint

import settings

from objects import Repair

test = Repair(zendesk=5472)

print(test.__dict__)

test.debug_print(console=True)

