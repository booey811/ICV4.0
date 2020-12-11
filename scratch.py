from manage import manager


col_vals = {'link1': {"url": "https://icorrect.monday.com/boards/876594047/pulses/{}".format(887477065), "text": 'LINK TEST'}}
manager.monday_clients['system'][0].get_board_by_id(349212843).add_item(item_name='LINK TEST', column_values=col_vals)