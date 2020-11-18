from threading import Thread
import json
import os
from urllib.parse import parse_qs
from time import sleep

from flask import Flask, request

from objects import Repair, RefurbUnit, OrderItem, CountItem
from manage import manager

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

    print(data)


# ROUTES // ++++++++++++ TEST ROUTE ++++++++++++ \\
@app.route("/811/test", methods=["POST"])
def test_route():
    info = request.get_data()
    print(info)
    return "TEST COMPLETE"

# ROUTES // ++++++++++++ TEST ROUTE == MONDAY ++++++++++++ \\
@app.route("/811/test/monday", methods=["POST"])
def test_route_monday():
    print("Zenlink Column Adjustment")
    webhook = request.get_data()
    # Authenticate & Create Object
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    print(data)
    return "MONDAY TEST COMPLETE"

# ROUTES // MONDAY
# Zenlink Column
@app.route("/monday/zenlink", methods=["POST", "GET"])
def monday_zenlink_column():
    print("Zenlink Column Adjustment")
    webhook = request.get_data()
    # Authenticate & Create Object
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))
    new_status = data["event"]["value"]["label"]["text"]

    if new_status == "Active":
        pass

    elif new_status == "Create Connection":
        repair.monday.add_to_zendesk()

    elif new_status == "Unable to Connect":
        pass

    elif new_status == "Error":
        pass

    elif new_status == "Severed":
        pass

    return "Zenlink Change Route Completed Successfully"

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
        print("Status Change: {} ==> {}".format(data["event"]["previousValue"]["label"]["text"], new_status))
    except TypeError:
        print("Status Change: NO PREVIOUS STATUS ==> {}".format(data["event"]["value"]["label"]["text"]))

    # Check Whether monday.com user is System
    if (data["event"]["userId"] in [15365289, 11581083]):
        repair.debug("Change made by System -- Ignored")
        if repair.zendesk and not repair.multiple_pulse_check_repair():
            repair.compare_app_objects("monday", "zendesk")

    else:
        # Add to notification column
        repair.monday.status_to_notification(data["event"]["value"]["label"]["text"])
        if not repair.multiple_pulse_check_repair():
            repair.compare_app_objects("monday", "zendesk")

        # Filter By Status
        if repair.monday.status == "Received":
            pass

        elif repair.monday.status == "Awaiting Confirmation":
            pass

        elif repair.monday.status == "Booking Confirmed":
            pass

        elif repair.monday.status == "Book Courier":
            repair.debug("STATUS - BOOK COURIER")
            repair.monday.gophr_booking(from_client=True)

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
            repair.debug("STATUS - BOOK RETURN COURIER")
            repair.monday.gophr_booking(from_client=False)

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
            if not repair.monday.check_column_presence(data["event"]["userId"]):
                repair.debug_print(debug=os.environ["DEBUG"])
                return "Status Change Route Complete - Returning Early"

            if repair.monday.client == "End User" and repair.monday.service == "Walk-In":
                    repair.monday.vend_sync()

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
    print("Notification Column Webhook")
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]

    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))
    new_notification = repair.monday.dropdown_value_webhook_comparison(data)
    if new_notification:
        if not repair.zendesk:
            repair.monday.add_to_zendesk
        repair.zendesk.notifications_check_and_send(new_notification)
        repair.monday.textlocal_notification()
    else:
        print("new notification returned false")

    repair.debug_print(debug=os.environ["DEBUG"])
    return "Monday Notificaions Column Change Route Complete"


# New End of Day Column
@app.route("/monday/eod/new", methods=["POST"])
def monday_eod_column_new():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]

    repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))

    repair.monday.adjust_stock_alt()

    return "New End Of Day Route Complete"

# Vend End of Day Column
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

# Updates Posted
@app.route("/monday/updates", methods=["POST"])
def monday_update_added():
    print("Monday Update Posted")
    # Monday Handshake
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    # Check update is not system-created
    if data["event"]["userId"] in [12304876, 15365289, 11581083]:
        print("Update Created By System - Ignored")
    else:
        repair = Repair(webhook_payload=data, monday=int(data["event"]["pulseId"]))
        if repair.zendesk:
            if repair.zendesk.ticket:
                repair.zendesk.add_comment(data["event"]["textBody"])
            else:
                repair.debug("Ticket Does Not Exist")
        else:
            repair.debug("Cannot Add Comment - No Zendesk Object Available")
    return "Monday Update Posted Route Complete"

# Refurb Added to Main Board
@app.route("/monday/refurb/add", methods=["POST"])
def refurb_to_main():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    sleep(4)
    refurb = RefurbUnit(int(data["event"]["pulseId"]))
    refurb.statuses_to_repairs()
    refurb.adjust_main_board_repairs()
    return "Add Refurb to Main Board Route Complete"


# Refurb Completed
@app.route("/monday/refurb/sales", methods=["POST"])
def refurb_price_calcs():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    refurb = RefurbUnit(int(data["event"]["pulseId"]))
    refurb.add_costs_to_refurbs(refurb.get_cost_data())
    return "Refurb Complete & Calculations Route Complete"

# Refurb Sold
@app.route("/monday/refurb/sold", methods=["POST"])
def refurb_unit_sold():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    refurb = RefurbUnit(int(data["event"]["pulseId"]))
    refurb.refurb_unit_sold()
    return "Refurb Complete & Calculations Route Complete"

# Stock Order Placed
@app.route("/monday/stock/order", methods=["POST"])
def stock_ordered():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    order_item = OrderItem(int(data["event"]["pulseId"]))
    order_item.order_placed()
    return "Stock Order Placed Route Complete"


# Stock Orders Received
@app.route("/monday/stock/received", methods=["POST"])
def stock_received():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    order_item = OrderItem(int(data["event"]["pulseId"]))
    if order_item.quant_received == None or order_item.quant_received == 0 or order_item.unit_cost == None or order_item.unit_cost == 0:
        manager.add_update(
            monday_id=int(data["event"]["pulseId"]),
            user="error",
            notify=["There was an issue while processing your stock order - please check and try again", data["event"]["userId"]],
            status=["status3", "Check Quantities"]
        )
    else:
        order_item.add_to_stock()
    return "Stock Received Route Complete"

# Stock Count Complete
@app.route("/monday/stock/count", methods=["POST"])
def stock_count():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    if data[0] is False:
        return data[1]
    else:
        data = data[1]
    stock_count = CountItem(int(data["event"]["pulseId"]))
    stock_count.adjust_inventory_with_count()
    return "Stock Count Route Complete"


# ROUTES // VEND
# Sale Update
@app.route("/vend/sale_update", methods=["POST"])
def vend_sale_update():
    print("Vend Sale Update")
    def process(sale):
        sale = sale.decode('utf-8')
        sale = parse_qs(sale)
        sale = json.loads(sale['payload'][0])
        repair = Repair(vend=sale["id"])

        # Ignore EOD Sales
        if any(option in sale["status"] for option in ["ONACCOUNT", "ONACCOUNT_CLOSED"]):
            repair.debug("Sale Processed for End of Day - Nothing Done")
            repair.debug("END OF ROUTE")

        # Closed Sales
        elif sale["status"] == "CLOSED" and repair.monday.client != "Refurb":
            repair.debug("Sale Closed")
            repair.vend.sale_closed()
            repair.debug("END OF ROUTE")

        # 'Update Monday' Product in Sale
        elif sale["status"] == "SAVED":
            if repair.vend.update_monday:
                if not repair.monday:
                    repair.vend.convert_to_monday_codes()
                    repair.add_to_monday()
                    repair.vend.parked_sale_adjustment(add_notes=False)
                else:
                    repair.compare_app_objects("vend", "monday")
                    repair.vend.parked_sale_adjustment()
        repair.debug_print(debug=os.environ["DEBUG"])

    thread = Thread(target=process, kwargs={"sale": request.get_data()})
    thread.start()
    return "Vend Sale Update Route Completed Successfully"

# ROUTES // ZENDESK
# New Comment
@app.route("/zendesk/comments", methods=["POST"])
def zendesk_comment_sent():
    print("Zendesk Comment Webhook")
    data = request.get_data().decode()
    data = json.loads(data)
    repair = Repair(zendesk=data["z_id"])

    if not repair.monday:
        repair.debug("No Associated Monday Pulse - Unable to add comment to Monday")
    else:
        if repair.multiple_pulse_check_repair():
            for obj in repair.associated_pulse_results:
                manager.add_update(
                    monday_id=obj.id,
                    user="email",
                    update=data["latest_comment"]
                )
        else:
            repair.compare_app_objects("zendesk", "monday")
            manager.add_update(
                monday_id=repair.monday.id,
                user="email",
                update=data["latest_comment"]
            )

    repair.debug_print(debug=os.environ["DEBUG"])
    return "Zendesk Commments Route Completed Successfully"

# Ticket Creates Pulse on Monday
@app.route("/zendesk/creation", methods=["POST"])
def zendesk_to_monday():
    print("Zendesk Creation Webhook")
    data = request.get_data().decode()
    data = json.loads(data)
    repair = Repair(zendesk=data["z_id"])
    repair.debug("Adding Zendesk Ticket to Monday")
    repair.zendesk.convert_to_monday()
    repair.add_to_monday()

    repair.debug_print(debug=os.environ["DEBUG"])
    return "Zendesk to Monday Route Completed Successfully"


# ROUTES // GOPHR
# Callback Function
@app.route("/gophr", methods=["POST"])
def gophr_webhook():
    print("Gophr Webhook")
    info = request.get_data().decode("utf-8")
    info = parse_qs(info)

    status = info["status"][0]

    # TODO Adjust Main Board Status on Confirmation
    # TODO Add To Gophr Data Board (Courier Name, Booking Time, Actual Collection, Actual Delivery)

    repair = Repair(monday=info["external_id"][0])

    if status == "ACCEPTED_BY_COURIER":
        repair.monday.adjust_gophr_data(info["external_id"][0], name=info["courier_name"][0], booking=True)
        if repair.monday.status == "Book Courier":
            repair.monday.item.change_column_value(column_id="status4", column_value={"label": "Courier Booked"})
        elif repair.monday.status == "Book Return Courier":
            repair.monday.item.change_column_value(column_id="status4", column_value={"label": "Return Booked"})

    elif status == "AT_PICKUP":
        repair.monday.adjust_gophr_data(repair.monday.id, collection=True)

    elif status == "AT_DELIVERY":
        repair.monday.adjust_gophr_data(repair.monday.id, delivery=True)

    elif status == "DELIVERED":
        if repair.monday.status == "Courier Booked":
            repair.monday.item.change_column_value(column_id="status4", column_value={"label": "Received"})
        elif repair.monday.status == "Return Booked":
            repair.monday.item.change_column_value(column_id="status4", column_value={"label": "Returned"})

    return "Gophr Webhook Route Completed Successfully"

# Top Line Driver Code
if __name__ == "__main__":
    app.run(load_dotenv=True)
