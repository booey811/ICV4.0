from pprint import pprint

from objects import PhoneCheckResult
import keys

user = keys.monday.user_ids['gabe']

test = PhoneCheckResult(917532647, user)

test.edit_listing()
