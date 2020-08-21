from pprint import pprint as p
import os

from objects import Repair
import settings

from moncli import ColumnType, create_column_value, MondayClient

item = Repair(monday=651224290)
board = MondayClient(user_name="systems@icorrect.co.uk", api_key_v1=os.environ["MONV1SYS"], api_key_v2=os.environ["MONV2SYS"]).get_board(id=703218230)

# for thing in board.get_items():
#     for value in thing.get_column_values():
#         print(value.__dict__)

print(ColumnType.dropdown.__dict__)

for pulse in item.monday:
    col_val = create_column_value(id="device0", column_type=ColumnType.dropdown, value=[2])
    results = board.get_items_by_column_values(col_val)
    print(len(results))
    for item in results:
        print(item.name)

