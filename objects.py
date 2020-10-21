import json
import os
import requests
from datetime import datetime, timedelta
from pprint import pprint
from urllib import request as urlrequest
from urllib import parse

from moncli import MondayClient, create_column_value, ColumnType, NotificationTargetType
from moncli.api_v2.exceptions import MondayApiError
from zenpy import Zenpy
from zenpy.lib import exception as zenpyExceptions
from zenpy.lib.api_objects import CustomField, Ticket, User, Comment

import settings
import keys.vend
import keys.monday
import keys.messages


class Repair():

    monday_client = MondayClient(
        user_name='systems@icorrect.co.uk',
        api_key_v1=os.environ["MONV1SYS"],
        api_key_v2=os.environ["MONV2SYS"]
        )

    zendesk_client = Zenpy(
        email='admin@icorrect.co.uk',
        token=os.environ["ZENDESKADMIN"],
        subdomain="icorrect"
        )

    # Monday Boards
    boards = {
        "logging": monday_client.get_board_by_id(id=736027251),
        "inventory": monday_client.get_board_by_id(id=703218230),
        "main": monday_client.get_board_by_id(id=349212843),
        "usage": monday_client.get_board_by_id(id=722437885),
        "zendesk_tags": monday_client.get_board_by_id(id=765453815),
        "macros": monday_client.get_board_by_id(id=762417852),
        "gophr": monday_client.get_board_by_id(id=538565672)
    }

    def __init__(self, webhook_payload=False, vend=False, monday=False, zendesk=False, test=False):

        self.debug_string = []
        self.vend = None
        self.monday = None
        self.zendesk = None
        self.associated_pulse_results = None

        self.category = None

        if webhook_payload:
            self.payload = webhook_payload
        else:
            self.payload = None

        if vend:
            self.include_vend(vend)
            self.source = "vend"
            self.name = "{} {}".format(self.vend.customer_info["first_name"], self.vend.customer_info["last_name"])
            self.email = self.vend.customer_info["email"]
            self.number = None
            self.alt_numbers = []
            for number in [self.vend.all_numbers]:
                if number:
                    if self.number:
                        self.alt_numbers.append(number)
                    else:
                        self.number = number

        elif monday:
            self.include_monday(monday)
            self.source = "monday"
            self.name = self.monday.name
            self.email = self.monday.email
            self.number = self.monday.number

        elif zendesk:
            self.source = "zendesk"
            self.include_zendesk(zendesk)
            self.name = self.zendesk.name
            self.email = self.zendesk.email
            self.number = self.zendesk.number

        elif test:
            self.name = "Jeremiah Bullfrog"
            self.source = "Created"

        self.query_applications()

    def include_vend(self, vend_sale_id):

        self.debug("Adding[VEND] ID: {}".format(vend_sale_id))
        self.vend = Repair.VendRepair(self, vend_sale_id=vend_sale_id)

    def include_monday(self, monday_id):

        self.debug("Adding[MONDAY] ID: {}".format(monday_id))
        self.monday = Repair.MondayRepair(self, monday_id=monday_id)

    def include_zendesk(self, zendesk_ticket_id):

        self.debug("Adding[ZENDESK] ID: {}".format(zendesk_ticket_id))
        self.zendesk = Repair.ZendeskRepair(self, zendesk_ticket_id)

    def query_applications(self):

        """Searches the specified applications for information related to the current repair"""

        self.debug(start="query_applications")

        if self.source == 'monday':
            if self.monday.v_id:
                self.include_vend(self.monday.v_id)

            if self.monday.z_ticket_id:
                self.include_zendesk(self.monday.z_ticket_id)
                self.monday.zendesk_url = "https://icorrect.zendesk.com/agent/tickets/{}".format(self.monday.z_ticket_id)

        elif self.source == 'vend':
            col_val = create_column_value(id='text88', column_type=ColumnType.text, value=str(self.vend.id))
            for item in self.monday_client.get_board(id="349212843").get_items_by_column_values(col_val):
                self.include_monday(item.id)
                break

            if self.monday:
                if self.monday.z_ticket_id:
                    self.include_zendesk(self.monday.z_ticket_id)

        elif self.source == 'zendesk':
            if self.zendesk.monday_id:
                self.include_monday(self.zendesk.monday_id)

            if self.monday:
                if self.monday.v_id:
                    self.include_vend(self.monday.v_id)

        else:
            self.debug("Source of Repair not set")

        self.debug(end="query_applications")

    def add_to_monday(self):
        self.debug(start="add_to_monday")
        if not self.monday:
            self.debug("No Monday Object Available - Unable to Add to Monday")
        else:
            self.monday.columns = MondayColumns(self.monday)
            name = self.name
            if self.source == "zendesk":
                self.monday.columns.column_values["status5"] = {"label": "Active"}
                self.monday.columns.column_values["text6"] = str(self.zendesk.ticket_id)
                if self.zendesk.ticket.organization:
                    name = self.name + " ({})".format(self.zendesk.ticket.organization.name)
            elif self.source == "vend":
                self.monday.columns.column_values["blocker"] = {"label": "Complete"}
                self.monday.columns.column_values["text88"] = str(self.vend.id)
            pprint(self.monday.columns.column_values)
            item = self.monday.item = self.boards["main"].add_item(item_name=name, column_values=self.monday.columns.column_values)

            if self.zendesk:
                self.zendesk.ticket.custom_fields.append(CustomField(id="360004570218", value=item.id))
                self.zendesk_client.tickets.update(self.zendesk.ticket)

        self.debug(end="add_to_monday")

    def debug(self, *args, start=False, end=False):
        """Adds to a list of strings that will eventaully be printed

        Args:
            message (string): The message required to add to debug list
            start (bool, optional): Used to signify the beginning of a function. Defaults to False.
            end (bool, optional): Used to signify the end of a function. Defaults to False.
        """

        if start:
            self.debug_string.append("================== OPEN " + start + " OPEN ==================")
        elif end:
            self.debug_string.append("================= CLOSE " + end + " CLOSE =================")
        else:
            for message in args:
                self.debug_string.append(message)

    def debug_print(self, debug=False):
        if debug == "monday":
            now = datetime.now() + timedelta(hours=1)
            col_vals = {"status5": {"label": self.source.capitalize()}}
            if self.monday:
                col_vals["text"]= self.monday.id
            if self.vend:
                col_vals["text3"] = str(self.vend.id)
            if self.zendesk:
                col_vals["text1"] = str(self.zendesk.ticket_id)
            time = str(now.strftime("%X"))
            log = self.boards["logging"].add_item(item_name=time + " // " + str(self.name) + " -- FROM APPV4", column_values=col_vals)
            log.add_update("\n".join(self.debug_string))
        elif debug == "console":
            print("\n".join(self.debug_string))
        else:
            print("DEBUGGING ELSE ROUTE")

    def search_zendesk_user(self):

        email = None
        number = None
        name = None


        if self.monday:
            self.debug("Retrieving from Monday Object")
            email = self.monday.email
            number = self.monday.number
            name = self.monday.name
        elif self.vend:
            self.debug("Retrieving from Vend Object")
            email = self.vend.email
            number = self.vend.number
            name = self.vend.name
        elif self.zendesk:
            self.debug("Retrieving from Zendesk Object")
            email = self.zendesk.email
            number = self.zendesk.number
            name = self.zendesk.name
        else:
            print("Cannot Find any Objects with Email, Number or Name")

        terms = [email, number, name]

        for term in terms:
            if term:
                search = self.zendesk_client.search(term, type="user")
                if len(search) == 1:
                    self.debug("Found User Through {}".format(term))
                    for item in search:
                        return item
                elif len(search) > 1:
                    self.debug("Too Many Users Found During {} Search".format(term))
                elif len(search) < 1:
                    self.debug("Too Few Users Found During {} Search".format(term))
                else:
                    self.debug("Else Route Taken During {} Search".format(term))

        return False

    def multiple_pulse_check_repair(self):
        self.debug(start="multiple_pulse_check")
        if not self.zendesk:
            self.debug("Unable to Check for Multiple Pulses - No Zendesk Object Exists")
            answer = False
        elif self.associated_pulse_results:
            self.debug("Funtion Already Performed - Pulses Already Added")
            answer = True
        else:
            col_val = create_column_value(id="text6", column_type=ColumnType.text, value=int(self.zendesk.ticket_id))
            results = self.boards["main"].get_items_by_column_values(col_val)
            if len(results) == 0:
                answer = False
                self.debug("No results returned from Main Board for Zendesk ID (RETURNING TRUE): {}".format(self.zendesk.ticket_id))
            elif len(results) == 1:
                answer = False
                self.debug("Only one pulse found")
            else:
                self.associated_pulse_results = results
                answer = True
        self.debug(end="multiple_pulse_check")
        return answer

    def pulse_comparison(self, comparison_type):
        self.debug(start="pulse_comparison")
        if not self.multiple_pulse_check_repair():
            self.debug("No Additional Pulses Associated with Repair - Nothing Done")
            answer = True
        else:
            if comparison_type == "status":
                count = 1
                while count < len(self.associated_pulse_results):
                    if self.associated_pulse_results[count - 1].get_column_value(id="status4").index != self.associated_pulse_results[count].get_column_value(id="status4").index:
                        self.debug("Statuses do not match (RETURNING FALSE)")
                        answer = False
                        break
                    else:
                        self.debug("Two Statuses Match")
                        answer = True
                        count += 1
                        continue
            else:
                self.debug("Else Route Taken During pulse_comparison")
                answer = False
        self.debug(end="pulse_comparison")
        return answer


    def compare_app_objects(self, source, upstream):

        if source == "monday" and upstream == "vend":
            pass
        elif (source == "monday" and upstream == "zendesk"):
            if not self.monday or not self.zendesk:
                self.debug("Monday/Zendesk Object Comparison Fail - Missing an Object")
            else:
                for attribute in ["address1", "address2", "postcode", "imei_sn", "passcode", "status", "service", "client", "repair_type"]:
                    monday = getattr(self.monday, attribute, None)
                    zendesk = getattr(self.zendesk, attribute, None)
                    correct = monday
                    incorrect = zendesk
                    if ((incorrect == None) or (correct != incorrect)):
                        self.zendesk.update_custom_field(attribute, correct)
        elif source == "zendesk" and upstream == "monday":
            print("right place")
            if not self.monday or not self.zendesk:
                self.debug("Monday/Zendesk Object Comparison Fail - Missing an Object")
            else:
                updated_item = Repair.MondayRepair(self, created=self.name)
                for attribute in ["address1", "address2", "postcode", "imei_sn", "passcode", "status", "service", "client", "repair_type"]:
                    monday = getattr(self.monday, attribute, None)
                    zendesk = getattr(self.zendesk, attribute, None)
                    correct = zendesk
                    incorrect = monday
                    if ((incorrect == None) or (correct != incorrect)):
                        setattr(updated_item, attribute, correct)
                columns = MondayColumns(updated_item)
                columns.update_item(self.monday)
        elif source == "vend" and upstream == "monday":
            if not self.monday or not self.vend:
                self.debug("Monday/Zendesk Object Comparison Fail - Missing an Object")
            else:
                updated_item = self.vend.convert_to_monday_codes(True)
                pprint(updated_item.__dict__)
                columns = MondayColumns(updated_item)
                columns.update_item(self.monday)


    # //def compare_app_objects_alt(self, source_of_truth):
    # //    if not self.monday:
    # //        self.debug("Cannot Compare Monday and Zendesk Objects - Monday does not exist")
    # //    elif not self.zendesk:
    # //        self.debug("Cannot Compare Monday and Zendesk Objects - Zendesk does not exist")
    # //    else:
    # //        updated_item = Repair.MondayRepair(self, created=self.name)
    # //        for attribute in ["address1", "address2", "postcode", "imei_sn", "passcode", "status", "service", "client", "repair_type"]:
    # //            monday = getattr(self.monday, attribute, None)
    # //            zendesk = getattr(self.zendesk, attribute, None)
    # //            if source_of_truth == "zendesk":
    # //                correct = zendesk
    # //                incorrect = monday
    # //            elif source_of_truth == "monday":
    # //                correct = monday
    # //                incorrect = zendesk
    # //                pass
    # //            if ((incorrect == None) or (correct != incorrect)) and source_of_truth == "monday":
    # //                self.zendesk.update_custom_field(attribute, correct)
    # //            elif ((incorrect == None) or (correct != incorrect)) and (source_of_truth == "zendesk"):
    # //                setattr(updated_item, attribute, correct)
    # //        if source_of_truth == "zendesk":
    # //            columns = MondayColumns(updated_item)
    # //            columns.update_item(self.monday)



    class VendRepair():
        def __init__(self, repair_object, vend_sale_id=False):
            self.parent = repair_object
            self.id = None
            self.passcode = None
            self.imei_sn = None

            self.pre_checks = []
            self.post_checks = []
            self.products = []
            self.notes = []

            self.return_products = []

            if vend_sale_id:
                self.id = vend_sale_id
                self.sale_info = self.query_for_sale()
                self.customer_id = str(self.sale_info["customer_id"])
                self.customer_info = self.query_for_customer()

                self.name = "{} {}".format(self.customer_info["first_name"], self.customer_info["last_name"])
                self.number = self.customer_info["mobile"]
                self.all_numbers = [
                    self.customer_info["mobile"],
                    self.customer_info["fax"],
                    self.customer_info["phone"]
                ]
                self.email = self.customer_info["email"]

                self.client = "End User"
                self.service = "Walk-In"
                self.repair_type = "Repair"

                self.update_monday = False

                self.get_and_organise_product_codes()
            else:
                pass

        def query_for_customer(self):

            url = "https://icorrect.vendhq.com/api/2.0/customers/{}".format(self.customer_id)

            headers = {'authorization': os.environ["VENDSYS"]}

            response = requests.request("GET", url, headers=headers)

            customer = json.loads(response.text)["data"]

            return customer

        def query_for_sale(self):

            url = "https://icorrect.vendhq.com/api/2.0/sales/{}".format(self.id)

            headers = {'authorization': os.environ["VENDSYS"]}

            response = requests.request("GET", url, headers=headers)

            sale = json.loads(response.text)["data"]

            return sale

        def get_and_organise_product_codes(self):

            """Go through products on sale organise into pre-checks, actual repairs, extract passcode/data/notification preferences"""
            if self.sale_info["note"]:
                self.notes.append(self.sale_info["note"])

            for product in self.sale_info["line_items"]:

                # Check if 'Update Monday Product is present'
                if product["product_id"] == "549e099d-a641-7141-c907-cdd9d0266175":
                    self.update_monday = True
                    continue

                # Check if Diagnostic Product is present, extract notes if so
                if product["product_id"] == "02d59481-b6ab-11e5-f667-e9f1a04c6e04":
                    self.repair_type = "Diagnostic"
                    self.notes.append(product["note"])
                    continue

                # Check if Warranty Product is present, extract notes if so
                if product["product_id"] == "02dcd191-aeab-11e6-f485-aea7f2c0a90a":
                    self.client = "Warranty"
                    self.notes.append(product["note"])
                    continue

                # Check if product is the password product
                if product["product_id"] == "6ce9883a-dfd1-e137-1596-d7c3c97fb450":
                    self.passcode = product["note"]
                    continue

                # Extract IMEI
                if product["note"]:
                    if any(option in product["note"] for option in ["IMEI", "SN", "S/N"]):
                        self.imei_sn = product["note"].split(":")[1].strip()


                # Check if product is a pre-check
                if product["product_id"] in keys.vend.pre_checks:
                    self.pre_checks.append(keys.vend.pre_checks[product["product_id"]])
                    continue

                # Add remaining codes to vend code attribute
                else:
                    self.products.append(product["product_id"])

        def convert_to_monday_codes(self, comparison=False):
            inv_board = self.parent.monday_client.get_board_by_id(id=703218230)
            monday_object = Repair.MondayRepair(self.parent, created=self.name)
            for item in self.products:
                col_val = create_column_value(id="text", column_type=ColumnType.text, value=item)
                for item in inv_board.get_items_by_column_values(col_val):
                    device = item.get_column_value(id='numbers3').number
                    repair = item.get_column_value(id="device").number
                    colour = item.get_column_value(id="numbers44").number
                    if not monday_object.device and device:
                        monday_object.device = [device]
                    monday_object.repairs.append(repair)
                    if not monday_object.colour and colour:
                        monday_object.colour = colour
            info_attributes = [
                "email",
                "number",
                "client",
                "service",
                "repair_type",
                "passcode",
                "imei_sn"
            ]
            for attribute in info_attributes:
                setattr(monday_object, attribute, getattr(self, attribute))
            if not comparison:
                self.parent.monday = monday_object
            else:
                return monday_object

        def create_eod_sale(self):
            self.parent.debug(start="create_eod_sale")
            if not self.parent.monday:
                self.parent.debug("No Monday Object to Generate Repairs From")
            else:
                self.sale_to_post = self.VendSale(self)
                self.sale_to_post.create_register_sale_products(self.parent.monday.vend_codes)
                if self.parent.monday.client == "Warranty" or self.parent.monday.client == "Refurb":
                    self.sale_to_post.sale_attributes["status"] = "CLOSED"
                else:
                    self.sale_to_post.sale_attributes["status"] = "ONACCOUNT_CLOSED"
                if self.id:
                    self.sale_to_post.sale_attributes["id"] = self.id
            self.parent.debug(end="create_eod_sale")

        def post_sale(self, vend_sale, sale_update=False):
            self.parent.debug(start="post_sale")
            url = "https://icorrect.vendhq.com/api/register_sales"
            if sale_update:
                payload = vend_sale
            else:
                payload = vend_sale.sale_attributes
            payload = json.dumps(payload)
            headers = {
                'content-type': "application/json",
                'authorization': os.environ["VENDSYS"]
                }
            response = requests.request("POST", url, data=payload, headers=headers)
            sale = json.loads(response.text)
            self.sale_info = sale["register_sale"]
            self.id = sale["register_sale"]["id"]
            self.parent.debug(end="post_sale")
            return sale["register_sale"]["id"]

        def sale_closed(self):
            self.parent.debug(start="sale_closed")
            if self.parent.monday:
                self.parent.monday.item.change_multiple_column_values({
                    "status4": {"label": "Returned"}
                })
            if self.parent.zendesk:
                self.parent.zendesk.ticket.status = "closed"
                self.parent.zendesk_client.tickets.update(self.parent.zendesk.ticket)
                self.customer_id_to_zendesk(self.id)
            for product in self.products:
                if (product in keys.vend.post_checks) or (product in keys.vend.pre_checks):
                    continue
                else:
                    self.add_to_usage(product)
            self.parent.debug(end="sale_closed")

        def customer_id_to_zendesk(self, customer_id):
            if not self.parent.zendesk:
                return False
            elif not self.parent.zendesk.ticket.requester.user_fields["vend_customer_id"]:
                self.parent.zendesk.ticket.requester.user_fields["vend_customer_id"] = customer_id
                self.parent.zendesk_client.users.update(self.parent.zendesk.ticket.requester)
                return True
            else:
                return False


        def parked_sale_adjustment(self):

            return_sale = self.sale_info.copy()
            return_sale.pop("line_items")
            return_sale["register_sale_products"] = []
            for item in self.sale_info["line_items"]:
                if item["product_id"] not in keys.vend.pre_checks:
                    return_sale["register_sale_products"].append(item)
            self.post_sale(return_sale, sale_update=True)

            self.parent.monday.add_update("PRE-CHECKS:\n{}\n\nNOTES:\n{}\n\nALT NUMBERS: {}".format("\n".join(self.pre_checks), "\n".join(self.notes), self.all_numbers))


        def add_to_usage(self, product_id):
            url = "https://icorrect.vendhq.com/api/products/{}".format(product_id)
            headers = {'authorization': os.environ["VENDSYS"]}
            response = requests.request("GET", url, headers=headers)
            info = json.loads(response.text)["products"][0]
            name = info["name"]
            name = name.replace('"', "")
            name = name.replace('\\"', "")
            col_vals = {
                "text2": "Vend",
                "numbers_1": info["price"],
                "numbers4": info["tax"],
                "numbers": info["supply_price"],
                "text": self.name,
            }
            if self.id:
                col_vals["text6"] = self.id
            try:
                self.parent.boards["usage"].add_item(item_name=name, column_values=col_vals)
            except MondayApiError:
                self.parent.boards["usage"].add_item(item_name="Parse Error While Adding", column_values=col_vals)


        class VendSale():

            sale_attributes = {
                "register_id": "02d59481-b67d-11e5-f667-b318647c76c1",
                "user_id": "0a6f6e36-8bab-11ea-f3d6-9603728ea3e6",
                "status": "SAVED",
                "register_sale_products": []
            }

            def __init__(self, vend_object):
                """Creates the request object for the Vend API and assists with editing it

                Args:
                    vend_object (VendRepair): The parent VendRepair object
                """

                self.vend_parent = vend_object

            def create_register_sale_products(self, product_ids):
                """Creates line items for the register sale

                Args:
                    product_ids (list): List of product ids to be added to the sale
                """
                self.vend_parent.parent.debug(start="create_register_sale_products")
                for product in product_ids:
                    dictionary = {
                        "product_id": product,
                        "quantity": 1,
                        "price": False,
                        "tax": False,
                        "tax_id": "647087e0-b318-11e5-9667-02d59481b67d"
                    }
                    self.get_pricing_info(dictionary)
                    self.sale_attributes["register_sale_products"].append(dictionary)
                self.vend_parent.parent.debug(end="create_register_sale_products")

            def get_pricing_info(self, dictionary):
                self.vend_parent.parent.debug(start="get_pricing_info")
                url = "https://icorrect.vendhq.com/api/products/{}".format(dictionary["product_id"])
                headers = {'authorization': os.environ["VENDSYS"]}
                response = requests.request("GET", url, headers=headers)
                info = json.loads(response.text)["products"][0]
                dictionary["price"] = info["price"]
                dictionary["tax"] = info["price_book_entries"][0]["tax"]
                if self.vend_parent.parent.monday.client == "Warranty" or self.vend_parent.parent.monday.client == "Refurb":
                    self.vend_parent.parent.debug("Warranty/Refurb Product - Sale and Tax Set to 0")
                    dictionary["price"] = dictionary["tax"] = 0
                    self.vend_parent.parent.monday.repair_names[dictionary["product_id"]].append(0)
                    self.vend_parent.parent.monday.repair_names[dictionary["product_id"]].append(0)
                    self.vend_parent.parent.monday.repair_names[dictionary["product_id"]].append(info["supply_price"])
                else:
                    self.vend_parent.parent.monday.repair_names[dictionary["product_id"]].append(info["price"])
                    self.vend_parent.parent.monday.repair_names[dictionary["product_id"]].append(info["tax"])
                    self.vend_parent.parent.monday.repair_names[dictionary["product_id"]].append(info["supply_price"])
                    self.vend_parent.parent.debug("Adding: {}".format(info["name"]))
                self.vend_parent.parent.debug(end="get_pricing_info")


    class MondayRepair():
        def __init__(self, repair_object, monday_id=False, created=False):
            self.parent = repair_object

            self.v_id = None
            self.z_ticket_id = None

            self.invoiced = None # Not currently used in program
            self.zendesk_url = None
            self.zenlink = None
            self.status = None
            self.service = None
            self.client = None
            self.repair_type = None
            self.case = None
            self.refurb = None
            self.booking_time = None # Not currently used in program
            self.deadline = None # Not currently used in program
            self.time = None # Not currently used in program
            self.technician = None # Not currently used in program
            self.device = []
            self.repairs = []
            self.colour = None
            self.screen_condition = None
            self.imei_sn = None
            self.data = None
            self.passcode = None
            self.postcode = None
            self.address2 = None
            self.address1 = None
            self.date_received = None
            self.number = None
            self.email = None
            self.eta = None # Not currently used in program
            self.date_repaired = None # Not currently used in program
            self.date_collected = None # Not currently used in program
            self.end_of_day = None
            self.deactivated = None
            self.notifications = []

            self.vend_codes = []
            self.repair_names = {}
            self.category = None

            self.z_notification_tags = []

            if monday_id:
                for item in self.parent.monday_client.get_items(limit=1, ids=[int(monday_id)]):
                    self.item = item
                    self.id = item.id
                    break
                self.name = str(self.item.name.split()[0]) + " " + str(self.item.name.split()[1])
                if self.parent.payload:
                    self.user_id = self.parent.payload["event"]["userId"]
                self.retreive_column_data()
                self.translate_column_data()
            if created:
                self.name = created
                self.id = None

            # self.columns = MondayColumns(self)

        def translate_column_data(self):
            self.parent.debug(start="translate_column_data")
            status_attributes = [
                ["Status", "m_status", "status"],
                ["Service", "m_service", "service"],
                ["Client", "m_client", "client"],
                ["Type", "m_type", "repair_type"],
                ["Refurb Type", "m_refurb", "refurb"],
                ["End Of Day", "m_eod", "end_of_day"],
                ["ZenLink", "m_zenlink", "zenlink"],
                ["Has Case", "m_has_case", "case"],
                ["Colour", "m_colour", "colour"]
            ]
            for column, m_attribute, attribute in status_attributes:
                # Check in status column dictionary for the corresponding column
                for option in keys.monday.status_column_dictionary[column]["values"]:
                    # Take title from column dictionary and add it to the Repair object
                    if option["index"] == getattr(self, m_attribute):
                        setattr(self, attribute, option["title"])
                        self.parent.debug("{}: {}".format(column, option["title"]))
            dropdown_attributes = [
                ["Device", "m_device", "device"],
                ["Repairs", "m_repairs", "repairs"],
                ["Screen Condition", "m_screen_condition", "screen_condition"],
                ["Notifications", "m_notifications", "notifications"]
            ]
            for column, m_attribute, attribute in dropdown_attributes:

                if column == "Notifications":
                    for ids in self.m_notifications:
                        for option in keys.monday.dropdown_column_dictionary["Notifications"]["values"]:
                            if option["ids"] == ids:
                                getattr(self, attribute).append(option["title"])
                                self.z_notification_tags.append(option["z_tag"])
                else:
                    setattr(self, attribute, getattr(self, m_attribute))

            self.parent.debug(end="translate_column_data")

        def retreive_column_data(self):
            self.parent.debug(start="retreive_column_data")

            for line in keys.monday.col_ids_to_attributes:
                if keys.monday.col_ids_to_attributes[line]["attribute"]:
                    if keys.monday.col_ids_to_attributes[line]["value_type"][0] == "ids":
                        setattr(self, keys.monday.col_ids_to_attributes[line]["attribute"], [])
                    else:
                        setattr(self, keys.monday.col_ids_to_attributes[line]["attribute"], None)

            column_values = self.item.get_column_values()
            for item in keys.monday.col_ids_to_attributes:
                if keys.monday.col_ids_to_attributes[item]['attribute'] is not None:
                    col_id = item
                    for value in column_values:
                        if value.id == "device0":
                            if value.ids:
                                self.set_device_category(value.text)
                        if value is None:
                            continue
                        else:
                            if value.id == col_id:
                                try:
                                    if keys.monday.col_ids_to_attributes[item]["value_type"][0] == "ids":
                                        setattr(self, keys.monday.col_ids_to_attributes[item]['attribute'], getattr(self, keys.monday.col_ids_to_attributes[item]['attribute']) + (getattr(value, keys.monday.col_ids_to_attributes[item]["value_type"][0])))
                                    else:
                                        setattr(self, keys.monday.col_ids_to_attributes[item]['attribute'],
                                                getattr(value, keys.monday.col_ids_to_attributes[item]["value_type"][0]))
                                except KeyError:
                                    self.parent.debug(
                                        "*811*ERROR: KEY: Cannot set {} Attribute in Class".format(keys.monday.col_ids_to_attributes[item]['attribute']))
                                except TypeError:
                                    self.parent.debug(
                                        "*811*ERROR: TYPE: Cannot set {} Attribute in Class".format(keys.monday.col_ids_to_attributes[item]['attribute']))
            self.parent.debug(end="retreive_column_data")

        def set_device_category(self, dropdown_text):
            dictionary = {
                "iPhone": "iPhone",
                "iPad": "iPad",
                "Watch": "Apple Watch"
            }
            for key in dictionary:
                if key in dropdown_text:
                    self.category = self.parent.category = dictionary[key]
                    break
            if not self.category:
                if (dropdown_text[0] == "A") and ("Watch" not in dropdown_text):
                    self.category = self.parent.category = "MacBook"

        def check_column_presence(self):
            """Goes through monday columns to make sure essential data has been filled out for this repair
            Returns False if any information is missing or True if all is well
            """
            self.parent.debug(start="check_column_presence")
            placeholder_repairs = [96, 97, 98]
            # Check if a placeholder repair has been left on pulse
            if any(repair in self.repairs for repair in placeholder_repairs):
                self.add_update(
                    "You have selected a placeholder repair - please select the repair you have completed and try again",
                    user="error",
                    notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name),
                    status="!! See Updates !!"
                )
                return False
            # Check if some type of screen repair has been completed
            if any(repair in self.m_repairs for repair in [69, 74, 84, 89, 90, 83]):
                # Check that screen condition has been selected/not left blank
                if not self.m_screen_condition and self.client != "Refurb":
                    self.add_update(
                        "You have not selected a screen condition for this repair - please select an option from the dropdown menu and try again",
                        user="error",
                        notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name),
                        status="!! See Updates !!"
                    )
                    return False
                # Check that colour has been selected/not left blank
                elif self.m_colour is None or self.m_colour == 5:
                    self.add_update(
                        "You have not selected a colour for the screen of this device - please select a colour option and try again",
                        user="error",
                        notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name),
                        status="!! See Updates !!"
                    )
                    return False
                # Check that a refurb type has been selected/not left blank
                elif not self.m_refurb or self.m_refurb == 5:
                    self.add_update(
                        "You have not selected what refurb variety of screen was used with this repair - please select a refurbishmnet option and try again",
                        user="error",
                        notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name),
                        status="!! See Updates !!"
                    )
                    return False
            # Check that IMEI has been recorded
            if not self.imei_sn and self.client != "Refurb":
                self.add_update(
                    "This device does not have an IMEI or SN given - please input this and try again",
                    user="error",
                    notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name),
                    status="!! See Updates !!"
                )
                return False
            return True
            self.parent.debug(end="check_column_presence")

        def add_update(self, update, user=False, notify=False, status=False):
            """Adds Updates to oulses and aids with adjusting status or notifying users

            Args:
                update (str): The body of the update to be posted to Monday Pulse
                user (str, optional): Used to select which User the API should post as. Defaults to False.
                notify (bool, optional): Used to send a notification from the selected API Client to the user who made the change on this webhook. Defaults to False.
                status (str, optional): Used to adjust the status of a pulse (if required). Defaults to False.
            """

            self.parent.debug(start="add_update")
            if user == 'error':
                client =  MondayClient(user_name='admin@icorrect.co.uk', api_key_v1=os.environ["MONV1ERR"], api_key_v2=os.environ["MONV2ERR"])
                for item in client.get_items(ids=[int(self.id)], limit=1):
                    monday_object = item
                    break
            elif user == 'email':
                client =  MondayClient(user_name='icorrectltd@gmail.com', api_key_v1=os.environ["MONV1EML"], api_key_v2=os.environ["MONV2EML"])
                for item in client.get_items(ids=[int(self.id)], limit=1):
                    monday_object = item
                    break
            else:
                monday_object = self.item
                client = self.parent.monday_client
            monday_object.add_update(update)
            if status:
                monday_object.change_column_value(column_id="status4", column_value={"label": status})
            if notify:
                self.send_notification(sender=client, message=notify, user_id=self.user_id)
            self.parent.debug(end="add_update")

        def send_notification(self, sender, message, user_id):
            self.parent.debug(start="send_notifcation")
            sender.create_notification(text=message, user_id=user_id, target_id=349212843, target_type=NotificationTargetType.Project)
            self.parent.debug(message)
            self.parent.debug(end="send_notifcation")

        def adjust_stock(self):
            self.parent.debug(start="adjust stock")
            if len(self.m_repairs) == 0:
                self.parent.debug_print("No Repairs on Monday")
            self.convert_to_vend_codes()
            if len(self.vend_codes) != len(self.repairs):
                self.parent.debug("Cannot Adjust Stock -- vend_codes {} :: {} m_repairs".format(len(self.vend_codes), len(self.repairs)))
                self.add_update("Cannot Adjust Stock - Vend Codes Lost During Conversion", user="error", status="!! See Updates !!")
            else:
                self.parent.vend = Repair.VendRepair(self.parent)
                self.parent.vend.create_eod_sale()
                sale_id = str(self.parent.vend.post_sale(self.parent.vend.sale_to_post))
                for repair in self.repair_names:
                    col_vals = {
                        "text": self.name,
                        "text2": self.parent.source.capitalize(),
                        "numbers": self.repair_names[repair][3],
                        "numbers4": self.repair_names[repair][2],
                        "numbers_1": self.repair_names[repair][1],
                        "text6": sale_id
                    }
                    try:
                        usage_name = "{} - {}".format(self.repair_names[repair][0], self.client)
                        self.parent.boards["usage"].add_item(item_name=usage_name, column_values=col_vals)
                    except MondayApiError:
                        self.parent.boards["usage"].add_item(item_name="Experienced Parse Error While Adding to Usage", column_values=col_vals)
                        self.parent.debug("Experienced Parse Error While Adding to Usage")
                    finally:
                        self.item.change_multiple_column_values({"blocker": {"label": "Complete"}})
                        update = []
                        for repair in self.repair_names:
                            update.append(self.repair_names[repair][0])
                        try:
                            self.add_update(update="Repairs Processed:\n{}".format("\n".join(update)))
                        except MondayApiError:
                            self.add_update(update="Repairs Have Been Processed, but a Parsing error prevented them from being displayed here")
            self.parent.debug(end="adjust stock")

        def convert_to_vend_codes(self):
            self.parent.debug(start="convert_to_vend_codes")
            for repair in self.repairs:
                search = tuple([(self.device[0],), (repair,), (self.m_colour,)])
                col_val = create_column_value(id="text99", column_type=ColumnType.text, value=search)
                results = self.parent.boards["inventory"].get_items_by_column_values(column_value=col_val)
                if not len(results) or len(results) > 1:
                    self.parent.debug("No results found for tuple (including colour): {}".format(search))
                    search = tuple([(self.device[0],), (repair,), ()])
                    col_val = create_column_value(id="text99", column_type=ColumnType.text, value=search)
                    results = self.parent.boards["inventory"].get_items_by_column_values(column_value=col_val)
                    if not len(results):
                        self.parent.debug("No results found for tuple (excluding colour): {}".format(search))
                    elif len(results) > 1:
                        self.parent.debug("Too many results found for tuple: {}".format(search))
                        self.add_update("Cannot Find: {}".format(search))
                        continue
                for product in results:
                    product_id = product.get_column_value(id="text").text
                    self.vend_codes.append(product_id)
                    name = product.name.replace('"', "")
                    name = name.replace('\\"', "")
                    self.repair_names[product_id] = [name]
            self.parent.debug(end="convert_to_vend_codes")

        def dropdown_value_webhook_comparison(self, webhook_data):
            self.parent.debug(start="dropdown_value_webhook_comparison")
            previous_ids = []
            new_ids = []
            added_id = False
            if not webhook_data["event"]["value"]:
                self.parent.debug("Notification Column Empty - Nothing Done")
            else:
                if webhook_data["event"]["previousValue"]:
                    for value in webhook_data["event"]["previousValue"]["chosenValues"]:
                        previous_ids.append(value["id"])
                for value in webhook_data["event"]["value"]["chosenValues"]:
                    new_ids.append(value["id"])
                if len(new_ids) <= len(previous_ids) or len(new_ids) == 0:
                    self.parent.debug("Notification ID Deleted - Nothing Done")
                else:
                    added_id = list(set(new_ids) - set(previous_ids))[0]
            self.parent.debug(end="dropdown_value_webhook_comparison")
            return added_id

        def status_to_notification(self, status_label):
            self.parent.debug(start="status_to_notification")
            if not self.parent.zendesk:
                self.parent.debug("No Zendesk Object Found - No Notifications to be sent")
            else:
                notification_ids = {
                    "Booking Confirmed": 1,
                    "Courier Booked": 6,
                    "Received": 2,
                    "Returned": 5,
                    "Repaired": 3,
                    "Invoiced": 4,
                    "Return Booked": 7
                }
                if (status_label in notification_ids):
                    if notification_ids[status_label] in self.m_notifications:
                        self.parent.debug("Notification ID already present on Pulse - Nothing Done")
                    elif self.parent.pulse_comparison("status"):
                        self.m_notifications.append(notification_ids[status_label])
                        self.item.change_multiple_column_values({"dropdown8": {"ids": self.m_notifications}})
                    else:
                        print("else route")
                else:
                    print("No Automated Macro")
            self.parent.debug(end="status_to_notification")

        def add_to_zendesk(self):
            self.parent.debug(start="add_to_zendesk")
            tag_options = [
                "Status",
                "Service",
                "Client",
                "Type"
            ]
            fields= {
                "imei_sn": 360004242638,
                "id": 360004570218,
                "passcode": 360005102118,
                "address1": 360006582778,
                "address2": 360006582798,
                "postcode": 360006582758
            }
            user = self.parent.search_zendesk_user()
            if not user:
                self.parent.debug("Cannot Find User -- Must Create One")
                if not self.email:
                    self.add_update(update="Unable to Create a Zendesk User -- Please provide an email address", user="error")
                else:
                    info = User(name=self.name, email=self.email, phone=self.number)
                    user = self.parent.zendesk_client.users.create(info)
            custom_fields =[]
            for item in fields:
                value = getattr(self, item, None)
                addition = CustomField(id=fields[item], value=value)
                custom_fields.append(addition)
            tags = ["mondayactive"]
            for option in tag_options:
                category = keys.monday.status_column_dictionary[option]
                attribute = getattr(self, category["attribute"])
                for value in category["values"]:
                    if value["label"] == attribute:
                        tags.append(value["z_tag"])
                    else:
                        continue
            ticket_audit = self.parent.zendesk_client.tickets.create(
                Ticket(
                    subject='Your Repair with iCorrect',
                    description="iCorrect Ltd",
                    public=False,
                    requester_id=user.id,
                    custom_fields=custom_fields,
                    tags=tags
                )
            )
            self.parent.include_zendesk(ticket_audit.ticket.id)
            self.parent.zendesk.address_extractor()
            self.item.change_multiple_column_values({
                "text6": str(ticket_audit.ticket.id),
                "link1": {"url": str("https://icorrect.zendesk.com/agent/tickets/{}".format(ticket_audit.ticket.id)), "text": str(ticket_audit.ticket.id)},
                "status5": {"label": "Active"},
                "text00": user.phone,
                "text5": user.email,
                "text93": self.parent.zendesk.postcode,
                "dup__of_passcode": self.parent.zendesk.address2,
                "passcode": self.parent.zendesk.address1,
                "text15": self.parent.zendesk.company_name
                })
            self.parent.debug(end="add_to_zendesk")



        def gophr_booking(self, from_client=True):
            self.parent.debug(start="gophr_booking")
            url = "https://api.gophr.com/v1/commercial-api/create-job"
            headers = {
                'content-type': "application/x-www-form-urlencoded"}

            pickup_info = {
                "pickup_person_name": ["name", "Gabriel"],
                "pickup_address1": ["address1", "12 Margaret Street"],
                "pickup_address2": ["address2", "iCorrect Ltd"],
                "pickup_postcode": ["postcode", "W1W 8JQ"],
                "pickup_mobile_number": ["number", "02070998517"],
                "pickup_email": ["email", "support@icorrect.co.uk"]
            }
            delivery_info = {
                "delivery_person_name": ["name", "Gabriel"],
                "delivery_address1": ["address1", "12 Margaret Street"],
                "delivery_address2": ["address2", "iCorrect Ltd"],
                "delivery_postcode": ["postcode", "W1W 8JQ"],
                "delivery_mobile_number": ["number", "02070998517"],
                "delivery_email": ["email", "support@icorrect.co.uk"]
            }
            info = {
                'api_key': os.environ["GOPHR"],
                "pickup_city": "London",
                "pickup_country_code": "GB",
                "delivery_city": "London",
                "delivery_country_code": "GB",
                "size_x": float(25),
                "size_y": float(16),
                "size_z": float(5),
                "weight": float(3),
                "delivery_deadline": "",
                "external_id": self.id,
                "team_id": "820",
                "callback_url": "https://icv4.herokuapp.com/gophr"
            }

            if from_client:
                for item in pickup_info:
                    info[item] = getattr(self, pickup_info[item][0], None)
                for item in delivery_info:
                    info[item] = delivery_info[item][1]
            elif not from_client:
                for item in pickup_info:
                    info[item] = pickup_info[item][1]
                for item in delivery_info:
                    info[item] = getattr(self, delivery_info[item][0], None)
            send_info = json.dumps(info)
            response = requests.request("POST", url, data=send_info, headers=headers)
            text_response = json.loads(response.text)
            if text_response["success"]:
                self.parent.debug("Booking Successful -- Job ID: {}".format(text_response["data"]["job_id"]))
                self.add_update(
                    update="Booking Successful\nJob ID: {}\nPrice: £{}\nPickup ETA: {}\nClick to Confirm Booking: {}".format(
                        text_response["data"]["job_id"], text_response["data"]["price_gross"],
                        text_response["data"]["pickup_eta"][11:19], text_response["data"]["private_job_url"])
                )
                self.parent.zendesk.ticket.custom_fields.append(CustomField(id=360006704157, value=text_response["data"]["public_tracker_url"]))
                self.parent.zendesk_client.tickets.update(self.parent.zendesk.ticket)
                if from_client:
                    self.capture_gophr_data(info["pickup_postcode"], info["delivery_postcode"], text_response["data"])
                else:
                    self.capture_gophr_data(info["pickup_postcode"], info["delivery_postcode"], text_response["data"], collect=False)
                result = True
            else:
                # error_code = text_response["error"]["code"].replace('\"', "|")
                notes = text_response["error"]["message"].replace('\"', "|")
                self.add_update(update="""Booking Failed\n\nNotes: {}""".format(notes), user="error", status="!! See Updates !!")
                result = False
            self.parent.debug(end="gophr_booking")
            return result

        def capture_gophr_data(self, collect_postcode, deliver_postcode, gophr_response, collect=True):
            self.parent.debug(start="capture_gophr_data")
            if collect:
                name = "{} Collection".format(self.name)
            else:
                name = "{} Return".format(self.name)
            pprint(gophr_response)
            column_values = {"text": collect_postcode,
                            "text4": deliver_postcode,
                            "distance": str(gophr_response["distance"]),
                            "price__ex_vat_": str(gophr_response["price_net"]),
                            "text0": str(gophr_response["job_id"]),
                            "text9": str(gophr_response["min_realistic_time"]),
                            "text5": self.id
                            }
            values = ["pickup_eta", "delivery_eta"]
            for option in values:
                date = gophr_response[option].split("T")[0]
                time = gophr_response[option].split("T")[1]
                time = time[:-6]
                if option == "pickup_eta":
                    column_values["date1"] = {"date": date, "time": time}
                else:
                    column_values["date5"] = {"date": date, "time": time}
            new_item = self.parent.boards["gophr"].add_item(item_name=name, column_values=column_values)
            self.parent.debug(end="capture_gophr_data")

        def adjust_gophr_data(self, monday_id, name=False, booking=False, collection=False, delivery=False):
            col_val = create_column_value(id="text5", column_type=ColumnType.text, value = str(monday_id))
            results = self.parent.boards["gophr"].get_items_by_column_values(col_val)
            if len(results) != 1:
                self.parent.debug("Cannot Find Gophr Data Object")
            else:
                for item in results:
                    pulse = item
                    break
                if name:
                    pulse.change_column_value(column_id="text56", column_value=str(name))
                adjust = [[booking, "hour89"], [collection, "hour4"], [delivery, "hour_1"]]
                for column in adjust:
                    if column[0]:
                        hour = datetime.now().hour
                        minute = datetime.now().minute
                        col_val = create_column_value(id=column[1], column_type=ColumnType.hour, hour=hour, minute=minute)
                        pulse.change_multiple_column_values([col_val])




        def textlocal_notification(self):
            message = self.textmessage_select_and_parse()
            if message:
                details = {
                    'apikey': os.environ["TEXTLOCAL"],
                    'numbers': str(self.number),
                    'message': message,
                    'sender': "iCorrect"
                }
                if self.repair_type == "Diagnostic" and self.status == "Received":
                    details["simple_reply"] = "true"
                data =  parse.urlencode(details)
                data = data.encode('utf-8')
                request = urlrequest.Request("https://api.txtlocal.com/send/?")
                f = urlrequest.urlopen(request, data)
                fr = f.read()
                self.parent.debug("Text Message Sent")
                return True
            else:
                return False

        def textmessage_select_and_parse(self):
            key = [
                self.client,
                self.service,
                self.status
            ]
            if self.repair_type == "Diagnostic" and self.status != "Repaired":
                key.insert(2, self.repair_type)
            string = " ".join(key)
            try:
                message = keys.messages.messages[string].format(self.name.split()[0])
            except KeyError:
                self.parent.debug("Text Message Template Does Not Exist")
                message = False
            return message

    class ZendeskRepair():

        def __init__(self, repair_object, zendesk_ticket_number, created=False):
            self.name = None
            self.email = None
            self.number = None

            self.status = None
            self.client = None
            self.service = None
            self.repair_type = None
            self.notifications = []
            self.associated_pulse_results = None

            self.monday_id = None

            self.address1 = None
            self.address2 = None
            self.postcode = None
            self.company_name = None


            self.parent = repair_object


            if not created:
                self.ticket_id = str(zendesk_ticket_number)
                try:
                    ticket = self.parent.zendesk_client.tickets(id=self.ticket_id)
                except zenpyExceptions.RecordNotFoundException:
                    self.parent.debug("Ticket {} Does Not Exist".format(zendesk_ticket_number))
                    ticket = False

                if ticket:
                    self.ticket = ticket
                    self.user = self.ticket.requester
                    self.user_id = self.user.id
                    self.zendesk_url = "https://icorrect.zendesk.com/agent/tickets/{}".format(self.ticket.id)

                    self.name = self.user.name
                    self.email = self.user.email
                    self.number = self.user.phone

                    if self.ticket.organization:
                        self.company_name = self.ticket.organization.name

                    self.convert_to_attributes()

                else:
                    self.parent.debug("Unable to find Zendesk ticket: {}".format(self.ticket_id))
            else:
                pass


        def address_extractor(self):

            self.parent.debug(start="address_extractor")

            fields = {
                "address1": [360006582778, "street_address", "street_address"],
                "address2": [360006582798, "company_flat_number", "company_flat_number"],
                "postcode": [360006582758, "post_code", "postcode"]
            }

            for attribute in fields:
                value = None

                for field in self.ticket.custom_fields:
                    if field["id"] == fields[attribute][0] and field["value"]:
                        value = field["value"]
                        self.parent.debug("got {} from ticket".format(attribute))

                if not value:
                    if self.user.user_fields[fields[attribute][1]]:
                        value = self.user.user_fields[fields[attribute][1]]
                        self.parent.debug("got {} from user".format(attribute))

                if not value:
                    if self.ticket.organization:
                        if self.ticket.organization.organization_fields[fields[attribute][2]]:
                            value = self.ticket.organization.organization_fields[fields[attribute][2]]
                            self.parent.debug("got {} from org".format(attribute))

                if value:
                    setattr(self, attribute, value)
                else:
                    self.parent.debug("No address found")

            self.parent.debug(end="address_extractor")

        def convert_to_attributes(self):

            self.parent.debug(start="convert_to_attributes")

            self.tag_conversion()

            custom_fields = {
                "imei_sn": 360004242638,
                "monday_id": 360004570218,
                "passcode": 360005102118,
                "monday_id": 360004570218
            }

            for field in self.ticket.custom_fields:
                for attribute in custom_fields:
                    if field["value"]:
                        if field["id"] == custom_fields[attribute]:
                            setattr(self, attribute, field["value"])

            self.address_extractor()

            self.parent.debug(end="convert_to_attributes")

        def tag_conversion(self):
            self.parent.debug(start="tag conversion")
            # Cycle Through Tags on Ticket
            for tag in self.ticket.tags:
                # Create Column Value with Tag for Text Value
                for category in keys.monday.status_column_dictionary:
                    for option in keys.monday.status_column_dictionary[category]["values"]:
                        if tag == option["z_tag"]:
                            setattr(self, keys.monday.status_column_dictionary[category]["attribute"], option["label"])
                            continue
                for category in keys.monday.dropdown_column_dictionary:
                    for option in keys.monday.dropdown_column_dictionary[category]["values"]:
                        if tag == option["z_tag"]:
                            to_append = getattr(self, keys.monday.dropdown_column_dictionary[category]["attribute"])
                            to_append.append([option["title"], int(option["ids"])])
                            continue
            self.parent.debug(end="tag conversion")

        def convert_to_monday(self):
            self.parent.debug(start="convert_to_monday")
            if self.parent.monday:
                self.parent.debug("Monday Object Already Exists - Cannot Create")
            else:
                self.parent.monday = Repair.MondayRepair(repair_object=self.parent, created=self.name)
                attributes = [
                    "status",
                    "client",
                    "service",
                    "imei_sn",
                    "address1",
                    "address2",
                    "postcode",
                    "passcode",
                    "number",
                    "email",
                    "name",
                    "repair_type",
                    "zendesk_url",
                    "company_name"
                ]
                for attribute in attributes:
                    value = getattr(self, attribute, None)
                    if value:
                        setattr(self.parent.monday, attribute, value)
                self.parent.monday.z_ticket_id = str(self.ticket_id)
                if self.ticket.organization:
                    self.parent.monday.name += " ({})".format(self.ticket.organization.name)
                for notification in self.notifications:
                    self.parent.monday.notifications.append(int(notification[1]))
            self.parent.debug(end="convert_to_monday")

        def execute_macro(self, macro_id):
            self.parent.debug(start="execute_macro")
            macro_result = self.parent.zendesk_client.tickets.show_macro_effect(self.ticket, macro_id)
            self.parent.zendesk_client.tickets.update(macro_result.ticket)
            self.parent.debug(end="execute_macro")

        def notifications_check_and_send(self, notification_id):
            self.parent.debug(start="notifcations_check_and_send")
            macro_id = None
            tag = None
            for option in keys.monday.dropdown_column_dictionary["Notifications"]["values"]:
                if option["ids"] == notification_id:
                    tag = option["z_tag"]
            if not self.ticket:
                self.parent.debug("No Ticket Generated on Zendesk Object -- Cannot Process Zendesk Features")
            elif tag and tag in self.ticket.tags:
                self.parent.debug("No Macro Sent - macro has already been applied to this ticket")
                self.parent.monday.add_update(update="No Macro Sent - This ticket has already received this macro", user="email")
            elif not tag:
                self.parent.debug("No Macro Sent - Cannot find notification ID in dropdown_column_dictionary")
                self.parent.monday.add_update("Cannot Send Macro - Please Let Gabe Know (Notification ID not found in dropdown_column_dictionary)", user="error")
            else:
                col_val = create_column_value(id="numbers8", column_type=ColumnType.numbers, value=int(notification_id))
                results = self.parent.boards["macros"].get_items_by_column_values(col_val)
                for item in results:
                    if item.get_column_value(id="status06").index == self.parent.monday.m_service:
                        if item.get_column_value(id="status5").index == self.parent.monday.m_client:
                            if item.get_column_value(id="status0").index == self.parent.monday.m_type:
                                macro_id = item.get_column_value(id="text").text
                                name = "{} {} {} {}".format(item.name, self.parent.monday.service, self.parent.monday.client, self.parent.monday.repair_type)
            if macro_id:
                self.execute_macro(macro_id)
                self.ticket.tags.extend([tag])
                self.parent.zendesk_client.tickets.update(self.ticket)
                self.parent.debug("Macro Sent: {}".format(name))
                self.update_monday_notification_column(notification_id)
            else:
                self.parent.monday.add_update("Cannot Send Macro - Please Let Gabe Know (No Macro On Macro Board)", user="error")
                self.parent.debug("Could Not Get Macro ID from Macro Board\nNotication ID: {}\nService: {}\nClient: {}\nType: {}".format(notification_id, self.parent.monday.service, self.parent.monday.client, self.parent.monday.repair_type))
            self.parent.debug(end="notifcations_check_and_send")

        def update_monday_notification_column(self, notification_id):
            self.parent.debug(start="update_monday_notification_column")
            if self.parent.multiple_pulse_check_repair():
                notifications = list(set(self.parent.monday.m_notifications + [notification_id]))
                for pulse in self.parent.associated_pulse_results:
                    pulse.change_multiple_column_values({"dropdown8": {"ids": notifications}})
            else:
                self.parent.debug("Only One Pulse Found - Nothing Done")
            self.parent.debug(end="update_monday_notification_column")

        def add_comment(self, message_body):
            self.parent.debug(start="add_comment")
            self.ticket.comment = Comment(body=message_body, public=False)
            self.parent.zendesk_client.tickets.update(self.ticket)
            self.parent.debug(start="add_comment")


        def compare_with_monday(self):
            if not self.parent.monday:
                self.parent.debug("Cannot Compare Monday and Zendesk Objects - Monday does not exist")
            else:
                for attribute in ["address1", "address2", "postcode", "imei_sn", "passcode", "status", "service", "client", "repair_type"]:
                    monday = getattr(self.parent.monday, attribute, None)
                    zendesk = getattr(self, attribute, None)

                    print("M:{} == Z:{}".format(monday, zendesk))

        def update_custom_field(self, field, value):
            text_fields = {
                "address1": 360006582778,
                "address2": 360006582798,
                "postcode": 360006582758,
                "imei_sn": 360004242638,
                "passcode": 360005102118,
            }
            tag_fields = {
                "status": keys.monday.status_column_dictionary["Status"]["values"],
                "service": keys.monday.status_column_dictionary["Service"]["values"],
                "client": keys.monday.status_column_dictionary["Client"]["values"],
                "repair_type": keys.monday.status_column_dictionary["Type"]["values"]
            }
            if field in text_fields:
                self.ticket.custom_fields.append(CustomField(id=text_fields[field], value=value))
                self.parent.zendesk_client.tickets.update(self.ticket)
            elif field in tag_fields:
                for option in tag_fields[field]:
                    if option["title"] == value:
                        self.ticket.tags.extend([option["z_tag"]])
                        self.parent.zendesk_client.tickets.update(self.ticket)
            else:
                print("field not found in method")




class MondayColumns():

    """Object that contains relevant column information for when repairs are added to Monday.

        This will translate normal attributes to values that are usable through moncli
    """

    # Dictionary to iterate through when translating column data back to Monday
    attributes_to_ids = {

        "statuses": {

            "values": {
                "status": "status4", # Status Column
                "service": "service", # Servcie Column
                "client": "status", # Client Column
                "repair_type": "status24", # Type Column
                "case": "status_14", # Case Column
                "colour": "status8", # Colour Column
                "refurb": "status_15", # Refurb Type Column
                "data": "status55", # Data Column
                "end_of_day": "blocker", # End Of Day Column
                "zenlink": "status5" # Zenlink Column
            },

            "structure": lambda id, value: [id, {"label": value}]
        },

        "index_statuses": {

            "values": {
                "colour": "status8", # Colour Column
            },

            "structure": lambda id, value: [id, {"index": value}]
        },

        # "checkboxes": {
        #     "values": {
        #         "invoiced": "check", # Invoiced? Column
        #     },

        #     "structure":
        # },

        "text": {
            "values": {
                "email": "text5", # Email Column
                "number": "text00", # Tel. No. Column
                "z_ticket_id": "text6", # Zendesk ID Column
                "v_id": "text6", # Vend Sale ID Column
                "address1": "passcode", # Street Address Column
                "address2": "dup__of_passcode", # Company/Flat Column
                "postcode": "text93", # Postcode Column
                "passcode": "text8", # Passcode Column
                "imei_sn": "text4", # IMEI Column
                "company_name": "text15" # Company Column
            },

            "structure": lambda id, value: [id, value]
        },

        "link": {
            "values": {
                "zendesk_url": "link1" # Zenlink URL Column
            },

            "structure": lambda id, url, text: [id, {"url": url, "text": text}]

        },

        "dropdown": {
            "values": {
                "device": "device0", # Device Column
                "repairs": "repair", # Repairs Column
                "screen_condition": "screen_condition",
                "notifications": "dropdown8" # Notifications Column
            },

            "structure": lambda id, value: [id, {"ids": value}]
        },

        # "date": {
        #     "values": {
        #         "booking_time": "date6", # Booking Date Column
        #         "deadline": "date36", # Deadline Column
        #     },

        #     "structure": lambda id, value:
        # },

        # "numbers": {
        #     "values": {
        #         "time": "numbers0", # Time Column
        #     },

        #     "structure": lambda id, value: [id, value]
        # }

    }

    def __init__(self, monday_object):

        self.column_values  = {}

        for category in self.attributes_to_ids:

            values = self.attributes_to_ids[category]["values"]
            structure = self.attributes_to_ids[category]["structure"]

            for column in values:
                if category == "link":
                    diction = structure(values[column], getattr(monday_object, column), getattr(monday_object, "z_ticket_id"))
                    self.column_values[diction[0]] = str(diction[1])
                else:
                    diction = structure(values[column], getattr(monday_object, column))
                    self.column_values[diction[0]] = diction[1]



    def update_item(self, monday_object):
        values_to_change = {}
        for column in self.column_values:
            if column == "link1":
                continue
            if self.column_values[column] is None:
                continue
            elif type(self.column_values[column]) == dict:
                try:
                    if self.column_values[column]["label"]:
                        values_to_change[column] = self.column_values[column]
                        continue
                except KeyError:
                    try:
                        if self.column_values[column]["index"]:
                            values_to_change[column] = self.column_values[column]
                            continue
                    except KeyError:
                        if self.column_values[column]["ids"]:
                            values_to_change[column] = self.column_values[column]
                            continue
            else:
                values_to_change[column] = self.column_values[column]
        monday_object.item.change_multiple_column_values(values_to_change)
