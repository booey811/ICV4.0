from objects import PhoneCheckResult
import keys

user = keys.monday.user_ids['gabe']

test = PhoneCheckResult(917174010, user)

test.record_check_info()