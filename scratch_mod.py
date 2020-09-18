from pprint import pprint as p
import os

from objects import Repair
import settings

from moncli import ColumnType, create_column_value, MondayClient



test = Repair(monday=745437272)

print("\n".join(test.debug_string))

