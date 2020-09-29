import requests
import json
import os
from pprint import pprint

import settings

from objects import Repair

test = Repair(zendesk=5590)

pprint(test.zendesk.__dict__)

test.zendesk.convert_to_monday()

pprint(test.monday.__dict__)

test.add_to_monday()