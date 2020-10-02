# import requests
# import json
# import os
# from pprint import pprint

# from moncli import create_column_value, ColumnType

# import settings
# from objects import Repair

# test = Repair(monday=772988281)

# test.monday.adjust_stock()

# test.debug_print(console=True)

ls1 = [1, 2, 3]
ls2 = [1, 2 ,3, 4]

print(int(list(set(ls2) - set(ls1))[0]))