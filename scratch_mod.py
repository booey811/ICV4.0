from objects import Repair

from keys.monday import status_column_dictionary

test = Repair(vend="6ffc7cac-fb7b-9eb1-11ea-fcae01e226df")

test.add_to_monday()

test.debug_print()