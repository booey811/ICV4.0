import requests
import json
import os

import settings

from objects import Repair

test = Repair(monday=726460853, webhook_payload={"event": {"userId": 4251271}})

print(test.monday.convert_to_vend_codes())