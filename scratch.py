import requests
import json
import os
from pprint import pprint

from moncli import create_column_value, ColumnType

import settings
from objects import Repair, MondayColumns, RefurbUnit
import keys.messages

# repair = Repair(test=True)

# refurbs = repair.monday_client.get_items(ids=[806715006])

# for item in refurbs:
#     pulse = item
#     break

# for column in item.get_column_values():
#     print(column.title, column.id)
#     if column.id == "connect_boards1":
#         print(column.__dict__)

# # col_val = create_column_value(id="repairs", column_type=ColumnType.dropdown, ids=[69])
# col_val = {"repairs": {"ids": [69, 71]}}

# item.change_column_value(col_val)

test = RefurbUnit(806715006)

test.statuses_to_repairs()
test.adjust_main_board_repairs()