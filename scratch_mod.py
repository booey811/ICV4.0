from pprint import pprint as p
import os

from objects import Repair
import settings

from moncli import ColumnType, create_column_value, MondayClient



test = Repair(zendesk=5152)

test.add_to_monday()

test.debug_print(console=True)
