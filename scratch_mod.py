from pprint import pprint as p
import os

from objects import Repair

from moncli import ColumnType, create_column_value, MondayClient


v1 = Repair(vend="6ffc7cac-fb7b-97b8-11ea-d17a810b420e")

v2 = Repair(monday=667786416)





p(v1.__dict__)
p(v2.__dict__)

test = None