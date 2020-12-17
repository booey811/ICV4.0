from objects import ScreenRefurb

screen = ScreenRefurb(user_id=user_id, item_id=int(data["event"]["pulseId"]))
screen.refurb_complete()