from moncli import create_column_value, ColumnType

from objects import Repair, InventoryItem, monday_client
from keys.monday import status_column_dictionary

parents = monday_client.get_board_by_id(840389891)
inventory = monday_client.get_board_by_id(703218230)

col_val = create_column_value(id="processed5", column_type=ColumnType.text, value="Not Done")

parent_results = parents.get_items_by_column_values(col_val)
total_num = len(parent_results)
count = 0

for parent_item in parent_results:

    search_term = parent_item.get_column_value(id="sku").text

    search_val = create_column_value(id="text0", column_type=ColumnType.text, value=search_term)

    slaves = inventory.get_items_by_column_values(search_val)

    return_vals = {
        "processed5": "Complete"
    }

    if len(slaves) == 1:
        print("{}: Only Has One Slave".format(parent_item.name))
        return_vals["link_required"] = {"label": "Finished"}
    elif len(slaves) == 0:
        print("{}: No Results Found")
        return_vals["link_required"] = {"label": "Other Issue"}
    else:
        names = []
        for inv_item in slaves:
            names.append(inv_item.name.replace('"', " Inch"))
        return_vals["link_required"] = {"label": "Adjustment Required"}
        parent_item.add_update("\n".join(names))
        parent_item.change_multiple_column_values(return_vals)
        print("{}: Updated".format(parent_item.name))
    count += 1
    print("{}% Complete".format((count/total_num)*100))