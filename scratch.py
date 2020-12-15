from objects import PhoneCheckResult
import keys

user = keys.monday.user_ids['gabe']

test = PhoneCheckResult(884881892, user)

test.record_check_info()