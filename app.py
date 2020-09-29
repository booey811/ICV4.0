from threading import Thread
import json

from flask import Flask, request

from objects import Repair

# APP SET UP
app = Flask(__name__)

# APP FUNCTIONS
def monday_handshake(webhook):
    """Takes webhook information, authenticates if required, and decodes information

    Args:
        webhook (request): Payload received from Monday's Webhooks

    Returns:
        dictionary: contains various information from Monday, dependent on type of webhook sent
    """
    data = webhook.decode('utf-8')
    data = json.loads(data)
    if "challenge" in data.keys():
        authtoken = {"challenge": data["challenge"]}
        return [False, authtoken]
    else:
        return [True, data]


# ROUTES // MONDAY
# Status Change
@app.route("/monday/status", methods=["POST", "GET"])
def monday_status_change():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))
    new_status = data["event"]["value"]["label"]["text"]
    try:
        repair.debug("Status Change: {} ==> {}".format(data["event"]["previousValue"]["label"]["text"], new_status))
    except TypeError:
        repair.debug("Status Change: NO PREVIOUS STATUS ==> {}".format(data["event"]["value"]["label"]["text"]))


    # Filter By Status
    if repair.monday.status == "Received":
        pass

    elif repair.monday.status == "Awaiting Confirmation":
        pass

    elif repair.monday.status == "Booking Confirmed":
        pass

    elif repair.monday.status == "Book Courier":
        pass

    elif repair.monday.status == "Courier Booked":
        pass

    elif repair.monday.status == "Received":
        pass

    elif repair.monday.status == "Diagnostics":
        pass

    elif repair.monday.status == "Diagnostic Complete":
        pass

    elif repair.monday.status == "Quote Sent":
        pass

    elif repair.monday.status == "Quote Accepted":
        pass

    elif repair.monday.status == "Under Repair":
        pass

    elif repair.monday.status == "Repair Paused":
        pass

    elif repair.monday.status == "With Rico":
        pass

    elif repair.monday.status == "Invoiced":
        pass

    elif repair.monday.status == "Paid":
        pass

    elif repair.monday.status == "Book Return Courier":
        pass

    elif repair.monday.status == "Return Booked":
        pass

    elif repair.monday.status == "Returned":
        pass

    elif repair.monday.status == "Quote Rejected":
        pass

    elif repair.monday.status == "Unrepairable":
        pass

    elif repair.monday.status == "Repaired":

        # Check the required information has been filled out
        if not repair.monday.check_column_presence():
            repair.debug_print()
            return "Status Change Route Complete - Returning Early"

        # Check for corporate repairs
        elif repair.monday.end_of_day != "Complete":
            repair.debug("End of Day != Complete")

            # Check that the repair is not an End User Walk-In
            if repair.monday.client == "End User" and repair.monday.service == "Walk-In":
                repair.debug("End User Walk-in Repair - Skipping Stock Adjustment")
                return "Status Change Route Complete - Returning Early"
            else:
                repair.monday.adjust_stock()

    elif repair.monday.status == "Client Contacted":
        pass

    elif repair.monday.status == "!! See Updates !!":
        pass

    repair.debug_print()

    return "Status Change Route Completed Successfully"

@app.route("/monday/notifications", methods=["POST"])
def monday_notifications_column():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))

    return "Monday Notificaions Column Chnage Route Complete"


# End of Day Column
@app.route("/monday/eod/do_now", methods=["POST"])
def monday_eod_column_do_now():

    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))
    repair.debug("End of Day Column --> Do Now")
    repair.monday.adjust_stock()
    repair.debug_print()
    return "Monday End of Day Route Completed Successfully"



# ROUTES // VEND
# Sale Update
@app.route("/vend/sale_update")
def vend_sale_update():

    def process(sale):

        sale = sale.decode('utf-8')
        sale = parse_qs(sale)
        sale = json.loads(sale['payload'][0])
        repair = Repair(vend=sale["id"])

        # 'Update Monday' Product in Sale

        repair.debug_print()

    thread = Thread(target=process, kwargs={"sale": request.get_data()})
    thread.start()


    return ""


# ROUTES // ZENDESK
# New Comment
@app.route("/zendesk/comments", methods=["POST"])
def zendesk_comment_sent():
    data = request.get_data().decode()
    data = json.loads(data)
    repair = Repair(zendesk=data["z_id"])
    repair.debug("Zendesk Commment Webhook Received")
    if not repair.monday:
        repair.debug("No Associated Monday Pulse - Unable to add comment to Monday")

    else:
        repair.monday.add_update(update=data["latest_comment"], user="email")
    repair.debug_print()
    return "Zendesk Commments Route Completed Successfully"


@app.route("/zendesk/creation", methods=["POST"])
def zendesk_to_monday():
    data = request.get_data().decode()
    data = json.loads(data)
    repair = Repair(zendesk=data["z_id"])
    repair.debug("Adding Zendesk Ticket to Monday")
    repair.zendesk.convert_to_monday()
    repair.add_to_monday()


    repair.debug_print()

    return "Zendesk to Monday Route Completed Successfully"

# Top Line Driver Code
if __name__ == "__main__":
    app.run(load_dotenv=True)
