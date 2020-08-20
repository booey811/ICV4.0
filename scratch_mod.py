from pprint import pprint as p

from objects import Repair


test = Repair(vend='6ffc7cac-fb7b-9dfc-11ea-d59d7f1fc76d')

p(test.__dict__)
print()
print()
print()
print()
p(test.vend.__dict__)



# from moncli import MondayClient
# import os

# import settings

# moncli = MondayClient(user_name='systems@icorrect.co.uk',
#                                 api_key_v1=os.environ["MONV1SYS"],
#                                 api_key_v2=os.environ["MONV2SYS"])


# main_board = moncli.get_board(id='349212843')

# col_vals = {"text4": "TESTCOL1", "text8": "TESTCOL2", "status4": {"label": "Awaiting Confirmation"}}

# main_board.add_item(item_name="TESTV4.1", column_values=col_vals)

# warranty_board = client.get_board(id='419735954')

# gophr_data = client.get_board(id="538565672")

# processed_stock = client.get_board(id='665823275')

# g_repairs_today = main_board.get_group(id="new_group70029")

# categories = {17: 'iPad', 18: 'iPad', 19: 'iPad', 20: 'iPad', 22: 'iPad', 24: 'iPad', 26: 'iPad', 27: 'iPad', 28: "iPad", 46: 'iPad', 47: 'iPad', 79: 'iPad', 1: 'iPhone', 2: 'iPhone', 3: 'iPhone', 4: 'iPhone', 6: 'iPhone', 7: 'iPhone', 9: 'iPhone', 10: 'iPhone', 11: 'iPhone', 12: 'iPhone', 13: 'iPhone', 15: 'iPhone', 77: 'iPhone', 78: 'iPhone', 37: 'Watch', 38: 'Watch', 39: 'Watch', 40: 'Watch', 41: 'Watch', 59: 'Watch', 75: 'Watch', 30: 'MacBook', 32: 'MacBook', 33: 'MacBook', 35: 'MacBook', 36: 'MacBook', 43: 'MacBook', 44: 'MacBook', 49: 'MacBook', 50: 'MacBook', 51: 'MacBook', 56: 'MacBook', 57: 'MacBook', 61: 'MacBook', 63: 'MacBook', 64: 'MacBook', 66: 'MacBook', 67: 'MacBook', 68: 'MacBook', 69: 'MacBook', 72: 'MacBook', 73: 'MacBook', 74: 'MacBook', 76: 'iPhone', 82: 'MacBook', 83: 'MacBook', 85: 'MacBook', 86: 'MacBook', 89: 'MacBook', 90: 'MacBook', 91: 'MacBook', 92: 'MacBook', 94: 'MacBook', 95: 'MacBook', 96: 'MacBook', 98: 'MacBook', 99: 'MacBook', 100: 'MacBook', 101: 'MacBook', 102: 'MacBook', 103: 'MacBook', 104: 'MacBook', 105: 'MacBook', 107: 'MacBook', 108: 'MacBook', 110: 'MacBook', 111: 'MacBook', 112: 'MacBook', 114: 'MacBook', 116: 'MacBook', 119: 'MacBook'}

# test_board = client.get_board(id=622750001)