import moncli

from manage import Manager

for item in Manager().monday_clients['system'][0].get_items(ids=[889160665]):
    test = item
    break

value = test.get_column_value('front_screen5')

print(value.__dict__)

value.index = 99999

test.change_column_value(value)

