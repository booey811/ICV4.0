import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit
import keys.messages


repair = Repair(test=True)
ids = [771064360, 772822485, 772860267, 773018411, 773043414, 779431758, 782516992]


print(ids)

for id_ in ids:
    refurb = RefurbUnit(id_)
    ls1 = refurb.get_cost_data()
    print(ls1)
    if ls1:
        refurb.add_costs_to_refurbs(ls1)

