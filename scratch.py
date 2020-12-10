from pprint import pprint


import settings
import objects
import keys.messages

gabe_id = 4251271


# Failures: None, 5

# Success: 3, 16


# =====================================================================================================================
# =====================================================================================================================

test = objects.Repair(monday=905739087)

stuart = objects.StuartClient(production=True)

stuart.arrange_courier(test, gabe_id, 'collecting')