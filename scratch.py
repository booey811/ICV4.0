import requests
import json
import os
from pprint import pprint

import settings

from objects import Repair

test = Repair(zendesk=5590)

test.zendesk.convert_to_attributes()

pprint(test.zendesk.__dict__)