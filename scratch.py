from pprint import pprint


import settings
import objects
import keys.messages

gabe_id = 4251271


# Failures: None, 5

# Success: 3, 16


# =====================================================================================================================
# =====================================================================================================================

test = objects.MainRefurbComplete(904688799, gabe_id)

pprint(test.__dict__)
