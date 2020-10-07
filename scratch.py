import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair

repair = Repair(monday=783827869)







multiple = repair.zendesk.multiple_pulse_check(check_type="status")
if multiple:
    # new_notification = repair.monday.dropdown_value_webhook_comparison(data)
    if new_notification:
        repair.zendesk.notifications_check_and_send(new_notification)
    else:
        print("new notification returned false")
else:
    print("multiple pulse check false")

test.debug_print(console=os.environ["DEBUG"])

pprint(test.monday.__dict__)