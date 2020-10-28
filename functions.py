import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit


repair = Repair(test=True)

# p1 = 819839310
# p1c1 = 819841026

# sub_items_board = repair.monday_client.get_board_by_id(819809804)


def print_item_column_values(item_id):
    for thing in repair.monday_client.get_items(ids=[item_id]):
        item = thing

    pprint(item.__dict__)

    vals = item.get_column_values()

    for column in vals:
        print(column.title)
        pprint(column.__dict__)
        print()
        print()

def search_by_sub_column(column_id, value):

    col_val = create_column_value(id="text", column_type=ColumnType.text, value="SAMPLE")
    for item in repair.boards["inventory2"].get_items_by_column_values(col_val):
        print(item.name)

    print("done")

board = repair.boards["inventory"]

device_ids = [12,14,15,76,78,77]
device_names = []
for item in "iPhone X, iPhone XS Max, iPhone XR, iPhone 11, iPhone 11 Pro Max, iPhone 11 Pro".split(","):
    device_names.append(item.strip())
print(device_names)

repair_id = 99
repair_name = "Face ID"

count = 0
while count < len(device_ids):
    board.add_item(
        item_name="{} Face ID Repair".format(device_names[count]),
        column_values={
            "numbers3": device_ids[count],
            "device": 99,
            "type": device_names[count],
            "status43": {"label": "iPhone"}
        }
    )
    count += 1
    print("{} is Done".format(device_names[count]))