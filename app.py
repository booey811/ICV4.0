from threading import Thread
import json
import os

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
    # Authenticate & Create Object
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))
    # Declare type of webhook
    new_status = data["event"]["value"]["label"]["text"]
    try:
        repair.debug("Status Change: {} ==> {}".format(data["event"]["previousValue"]["label"]["text"], new_status))
    except TypeError:
        repair.debug("Status Change: NO PREVIOUS STATUS ==> {}".format(data["event"]["value"]["label"]["text"]))

    #Check Whether monday.com user is System
    if data["event"]["userId"] in [12304876, 15365289, 11581083]:
        repair.debug("Change made by System -- Ignored")

    else:
        # Add to notification column
        repair.monday.status_to_notification(data["event"]["value"]["label"]["text"])

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
                repair.debug_print(debug=os.environ["DEBUG"])
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

    repair.debug_print(debug=os.environ["DEBUG"])

    return "Status Change Route Completed Successfully"

# Notifications Column
@app.route("/monday/notifications", methods=["POST"])
def monday_notifications_column():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]

    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))
    repair.debug("Notifications Column Route")
    # Check Zendesk Exists
    if not repair.zendesk:
        repair.debug("Unable to send macro - no zendesk ticket exists")
        repair.monday.add_update(update="Unable to send Macro - No Zendesk Ticket Exists", user="error", notify="error")
    else:
        multiple = repair.zendesk.multiple_pulse_check(check_type="status")
        new_notification = repair.monday.dropdown_value_webhook_comparison(data)
        if multiple:
            if new_notification:
                repair.zendesk.notifications_check_and_send(new_notification)
            else:
                print("new notification returned false")
        else:
            repair.monday.item.change_multiple_column_values({"dropdown8": {"ids": repair.monday.m_notifications.remove(new_notification)}})
            print("multiple pulse check false")

    repair.debug_print(debug=os.environ["DEBUG"])
    return "Monday Notificaions Column Change Route Complete"


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
    repair.debug_print(debug=os.environ["DEBUG"])
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

        repair.debug_print(debug=os.environ["DEBUG"])

    thread = Thread(target=process, kwargs={"sale": request.get_data()})
    thread.start()


    return "Vend Sale Update Route Completed Successfully"


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

    repair.debug_print(debug=os.environ["DEBUG"])
    return "Zendesk Commments Route Completed Successfully"

# Ticket Creates Pulse on Monday
@app.route("/zendesk/creation", methods=["POST"])
def zendesk_to_monday():
    data = request.get_data().decode()
    data = json.loads(data)
    repair = Repair(zendesk=data["z_id"])
    repair.debug("Adding Zendesk Ticket to Monday")
    repair.zendesk.convert_to_monday()
    repair.add_to_monday()

    repair.debug_print(debug=os.environ["DEBUG"])
    return "Zendesk to Monday Route Completed Successfully"

# Top Line Driver Code
if __name__ == "__main__":
    app.run(load_dotenv=True)
