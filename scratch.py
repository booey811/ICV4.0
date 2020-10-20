import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns
import keys.messages

repair = Repair(zendesk=5974)
repair.vend = Repair.VendRepair(repair)

pprint(repair.zendesk.ticket.requester.user_fields)


repair.vend.customer_id_to_zendesk("blah bkah vlahd")


# ! Adding V-ID to Zendesk TO SEE: VendRepair.customer_id_to_zendesk