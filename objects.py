import json
import os
import requests
from datetime import datetime, timedelta, date
import time
from pprint import pprint
from urllib import request as urlrequest
from urllib import parse

from moncli import MondayClient, create_column_value, ColumnType, NotificationTargetType, PeopleKind
from moncli.api_v2.exceptions import MondayApiError
from zenpy import Zenpy
from zenpy.lib import exception as zenpyExceptions
from zenpy.lib.api_objects import CustomField, Ticket, User, Comment
import pycurl
from io import BytesIO

import settings
import keys.vend
import keys.monday
import keys.messages
from manage import manager

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


class Repair():
    # Monday Boards
    boards = {
        # "logging": monday_client.get_board_by_id(id=736027251),
        "inventory": monday_client.get_board_by_id(id=868065293),
        "main": monday_client.get_board_by_id(id=349212843),
        "usage": monday_client.get_board_by_id(id=722437885),
        "zendesk_tags": monday_client.get_board_by_id(id=765453815),
        "macros": monday_client.get_board_by_id(id=762417852),
        "gophr": monday_client.get_board_by_id(id=538565672),
        "refurbs": monday_client.get_board_by_id(id=757808757),
        "new_sales": monday_client.get_board_by_id(id=826011912)
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
        self.monday = Repair.MondayRepair(repair_object=self, monday_id=monday_id)

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
                self.monday.zendesk_url = "https://icorrect.zendesk.com/agent/tickets/{}".format(
                    self.monday.z_ticket_id)

        elif self.source == 'vend':
            col_val = create_column_value(id='text88', column_type=ColumnType.text, value=str(self.vend.id))
            for item in monday_client.get_board(id="349212843").get_items_by_column_values(col_val):
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
            item = self.monday.item = self.boards["main"].add_item(item_name=name,
                                                                   column_values=self.monday.columns.column_values)
            if self.zendesk:
                self.zendesk.ticket.custom_fields.append(CustomField(id="360004570218", value=item.id))
                zendesk_client.tickets.update(self.zendesk.ticket)
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
                col_vals["text"] = self.monday.id
            if self.vend:
                col_vals["text3"] = str(self.vend.id)
            if self.zendesk:
                col_vals["text1"] = str(self.zendesk.ticket_id)
            time = str(now.strftime("%X"))
            # log = self.boards["logging"].add_item(item_name=time + " // " + str(self.name) + " -- FROM APPV4", column_values=col_vals)
            # log.add_update("\n".join(self.debug_string))
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
                search = zendesk_client.search(term, type="user")
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
                self.debug("No results returned from Main Board for Zendesk ID (RETURNING TRUE): {}".format(
                    self.zendesk.ticket_id))
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
                    if self.associated_pulse_results[count - 1].get_column_value(id="status4").index != \
                            self.associated_pulse_results[count].get_column_value(id="status4").index:
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
                for attribute in ["address1", "address2", "postcode", "imei_sn", "passcode", "status", "service",
                                  "client", "repair_type"]:
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
                updated_item = Repair.MondayRepair(repair_object=self, created=self.name)
                for attribute in ["address1", "address2", "postcode", "imei_sn", "passcode", "status", "service",
                                  "client", "repair_type"]:
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
                updated_item = self.vend.convert_to_monday_codes(comparison=True)
                pprint(updated_item.__dict__)
                columns = MondayColumns(updated_item)
                columns.update_item(self.monday)

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
                        try:
                            self.imei_sn = product["note"].split(":")[1].strip()
                        except IndexError:
                            self.pre_checks.append(product["note"])
                # Check if product is a pre-check
                if product["product_id"] in keys.vend.pre_checks:
                    self.pre_checks.append(keys.vend.pre_checks[product["product_id"]])
                    continue
                # Add remaining codes to vend code attribute
                else:
                    self.products.append(product["product_id"])

        def convert_to_monday_codes(self, comparison=False):
            inv_board = monday_client.get_board_by_id(id=703218230)
            monday_object = Repair.MondayRepair(repair_object=self.parent, created=self.name)
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
                for code in self.parent.monday.vend_codes:
                    self.sale_to_post.sale_attributes["register_sale_products"].append(
                        self.sale_to_post.create_register_sale_products(code))
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
                manager.add_update(
                    monday_id=self.parent.monday.id,
                    user="system",
                    update="Vend Sale:\nhttps://icorrect.vendhq.com/register_sale/edit/id/{}".format(self.id),
                    status=["status4", "Returned"]
                )
            if self.parent.zendesk:
                self.parent.zendesk.ticket.status = "closed"
                zendesk_client.tickets.update(self.parent.zendesk.ticket)
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
                zendesk_client.users.update(self.parent.zendesk.ticket.requester)
                return True
            else:
                return False

        def parked_sale_adjustment(self, add_notes=True):
            return_sale = self.sale_info.copy()
            return_sale.pop("line_items")
            return_sale["register_sale_products"] = []
            for item in self.sale_info["line_items"]:
                if item["product_id"] not in keys.vend.pre_checks:
                    return_sale["register_sale_products"].append(item)
            self.post_sale(return_sale, sale_update=True)
            count = 1
            key = {
                1: "PRE-CHECKS",
                2: "NOTES"
            }
            for info in [[self.pre_checks, "PRE-CHECKS"], [self.notes, "NOTES"]]:
                if info[0]:
                    manager.add_update(
                        monday_id=self.parent.monday.id,
                        user="system",
                        update="{}:\n\n{}".format(info[1], "\n".join(info[0]))
                    )

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

            def create_register_sale_products_alt(self, product_ids):
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

            def create_register_sale_products(self, product_id):
                """Creates line items for the register sale

                Args:
                    product_ids (list): List of product ids to be added to the sale
                """
                self.vend_parent.parent.debug(start="create_register_sale_products")
                dictionary = {
                    "product_id": product_id,
                    "quantity": 1,
                    "price": False,
                    "tax": False,
                    "tax_id": "647087e0-b318-11e5-9667-02d59481b67d",
                    "attributes": []
                }
                self.get_pricing_info(dictionary)
                self.vend_parent.parent.debug(end="create_register_sale_products")
                return dictionary

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
        def __init__(self, repair_object=False, monday_id=False, created=False):
            self.parent = repair_object

            self.v_id = None
            self.z_ticket_id = None

            self.invoiced = None  # Not currently used in program
            self.zendesk_url = None
            self.zenlink = None
            self.status = None
            self.service = None
            self.client = None
            self.repair_type = None
            self.company_name = None
            self.case = None
            self.refurb = None
            self.booking_time = None  # Not currently used in program
            self.deadline = None  # Not currently used in program
            self.time = None  # Not currently used in program
            self.technician = None  # Not currently used in program
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
            self.eta = None  # Not currently used in program
            self.date_repaired = None  # Not currently used in program
            self.date_collected = None  # Not currently used in program
            self.end_of_day = None
            self.deactivated = None
            self.notifications = []
            self.new_end_of_day = False

            self.vend_codes = []
            self.repair_names = {}
            self.category = None

            self.z_notification_tags = []

            if monday_id:
                for item in monday_client.get_items(limit=1, ids=[int(monday_id)]):
                    self.item = item
                    self.id = item.id
                    break
                self.name = str(self.item.name.split()[0]) + " " + str(self.item.name.split()[1])
                if self.parent.payload:
                    self.user_id = self.parent.payload["event"]["userId"]
                else:
                    self.user_id = False
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
                ["Vend End Of Day", "m_eod", "end_of_day"],
                ["ZenLink", "m_zenlink", "zenlink"],
                ["Has Case", "m_has_case", "case"],
                ["Colour", "m_colour", "colour"],
                ["New End Of Day", "new_eod", "new_end_of_day"]
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
                                        setattr(self, keys.monday.col_ids_to_attributes[item]['attribute'],
                                                getattr(self, keys.monday.col_ids_to_attributes[item]['attribute']) + (
                                                    getattr(value,
                                                            keys.monday.col_ids_to_attributes[item]["value_type"][0])))
                                    else:
                                        setattr(self, keys.monday.col_ids_to_attributes[item]['attribute'],
                                                getattr(value,
                                                        keys.monday.col_ids_to_attributes[item]["value_type"][0]))
                                except KeyError:
                                    self.parent.debug(
                                        "*811*ERROR: KEY: Cannot set {} Attribute in Class".format(
                                            keys.monday.col_ids_to_attributes[item]['attribute']))
                                except TypeError:
                                    self.parent.debug(
                                        "*811*ERROR: TYPE: Cannot set {} Attribute in Class".format(
                                            keys.monday.col_ids_to_attributes[item]['attribute']))
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

        def check_column_presence(self, user_id):
            """Goes through monday columns to make sure essential data has been filled out for this repair
            Returns False if any information is missing or True if all is well
            """
            self.parent.debug(start="check_column_presence")
            placeholder_repairs = [96, 97, 98]
            # Check if a placeholder repair has been left on pulse
            if any(repair in self.repairs for repair in placeholder_repairs):
                manager.add_update(
                    monday_id=self.id,
                    update="You have selected a placeholder repair - please select the repair you have completed and try again",
                    user="error",
                    notify=[
                        "You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(
                            self.name), user_id],
                    status=["status4", "!! See Updates !!"]
                )
                return False
            # Check if some type of screen repair has been completed
            if any(repair in self.m_repairs for repair in [69, 74, 84, 89, 90, 83]):
                # Check that screen condition has been selected/not left blank
                if not self.m_screen_condition and self.client != "Refurb":
                    manager.add_update(
                        monday_id=self.id,
                        update="You have not selected a screen condition for this repair - please select an option from the dropdown menu and try again",
                        user="error",
                        notify=[
                            "You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(
                                self.name), user_id],
                        status=["status4", "!! See Updates !!"]
                    )
                    return False
                # Check that colour has been selected/not left blank
                elif self.m_colour is None or self.m_colour == 5:
                    manager.add_update(
                        monday_id=self.id,
                        update="You have not selected a colour for the screen of this device - please select a colour option and try again",
                        user="error",
                        notify=[
                            "You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(
                                self.name), user_id],
                        status=["status4", "!! See Updates !!"]
                    )
                    return False
                # Check that a refurb type has been selected/not left blank
                elif not self.m_refurb or self.m_refurb == 5:
                    manager.add_update(
                        monday_id=self.id,
                        update="You have not selected what refurb variety of screen was used with this repair - please select a refurbishmnet option and try again",
                        user="error",
                        notify=[
                            "You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(
                                self.name), user_id],
                        status=["status4", "!! See Updates !!"]
                    )
                    return False
            # Check that IMEI has been recorded
            if not self.imei_sn and self.client != "Refurb":
                manager.add_update(
                    monday_id=self.id,
                    update="This device does not have an IMEI or SN given - please input this and try again",
                    user="error",
                    notify=[
                        "You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(
                            self.name), user_id],
                    status=["status4", "!! See Updates !!"]
                )
                return False
            return True
            self.parent.debug(end="check_column_presence")

        def add_update(self, update=False, user=False, notify=False, status=False, non_main=False):
            """Adds Updates to oulses and aids with adjusting status or notifying users

            Args:
                update (str): The body of the update to be posted to Monday Pulse
                user (str, optional): Used to select which User the API should post as. Defaults to False.
                notify (bool, optional): Used to send a notification from the selected API Client to the user who made the change on this webhook. Defaults to False.
                status (list, optional): Used to adjust the status of a pulse (if required). [column_id, label] Defaults to False.
                non_main (list, optional): Used when a notification neeeds to be sent for an itme on on the main board [item_id, userid_to_notify, board_id]
            """

            if non_main:
                monday_id = int(non_main[0])
                user_id = int(non_main[1])
                target_id = int(non_main[2])
            else:
                monday_id = int(self.id)
                user_id = int(self.user_id)
                target_id = 349212843
            if user == 'error':
                client = MondayClient(user_name='admin@icorrect.co.uk', api_key_v1=os.environ["MONV1ERR"],
                                      api_key_v2=os.environ["MONV2ERR"])
                for item in client.get_items(ids=[monday_id], limit=1):
                    monday_object = item
                    break
            elif user == 'email':
                client = MondayClient(user_name='icorrectltd@gmail.com', api_key_v1=os.environ["MONV1EML"],
                                      api_key_v2=os.environ["MONV2EML"])
                for item in client.get_items(ids=[monday_id], limit=1):
                    monday_object = item
                    break
            else:
                monday_object = self.item
                client = monday_client
            if update:
                monday_object.add_update(update)
            if status:
                monday_object.change_column_value(column_id=status[0], column_value={"label": status[1]})
            if notify:
                self.send_notification(sender=client, message=notify, user_id=user_id, target_id=target_id)

        def send_notification(self, sender, message, user_id, target_id):
            self.parent.debug(start="send_notifcation")
            sender.create_notification(text=message, user_id=user_id, target_id=target_id,
                                       target_type=NotificationTargetType.Project)
            self.parent.debug(message)
            self.parent.debug(end="send_notifcation")

        def adjust_stock(self):
            self.parent.debug(start="adjust stock")
            if len(self.m_repairs) == 0:
                self.parent.debug_print("No Repairs on Monday")
            self.convert_to_vend_codes()
            if len(self.vend_codes) != len(self.repairs):
                self.parent.debug("Cannot Adjust Stock -- vend_codes {} :: {} m_repairs".format(len(self.vend_codes),
                                                                                                len(self.repairs)))
                manager.add_update(
                    monday_id=self.id,
                    update="Cannot Adjust Stock - Vend Codes Lost During Conversion",
                    user="error",
                    status=["status4", "!! See Updates !!"])
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
                        self.parent.boards["usage"].add_item(item_name="Experienced Parse Error While Adding to Usage",
                                                             column_values=col_vals)
                        self.parent.debug("Experienced Parse Error While Adding to Usage")
                    finally:
                        self.item.change_multiple_column_values({"blocker": {"label": "Complete"}})
                        update = []
                        for repair in self.repair_names:
                            update.append(self.repair_names[repair][0])
                        try:
                            manager.add_update(
                                monday_id=self.id,
                                user="system",
                                update="Repairs Processed:\n{}\n\nVend Sale:\n{}".format("\n".join(update),
                                                                                         "https://icorrect.vendhq.com/register_sale/edit/id/{}".format(
                                                                                             sale_id))
                            )
                        except MondayApiError:
                            manager.add_update(
                                monday_id=self.id,
                                user="system",
                                update="Repairs Have Been Processed, but a Parsing error prevented them from being displayed here\n\nVend Sale:\nhttps://icorrect.vendhq.com/register_sale/edit/id/{}".format(
                                    sale_id)
                            )
            self.parent.debug(end="adjust stock")

        def convert_to_vend_codes(self, for_refurb=False):
            self.parent.debug(start="convert_to_vend_codes")
            inventory_items = []
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
                        self.add_update(update="Cannot Find: {}".format(search))
                        continue
                for product in results:
                    if for_refurb:
                        inventory_items.append(product)
                    else:
                        product_id = product.get_column_value(id="text").text
                        self.vend_codes.append(product_id)
                        name = product.name.replace('"', "")
                        name = name.replace('\\"', "")
                        self.repair_names[product_id] = [name]
            self.parent.debug(end="convert_to_vend_codes")
            if for_refurb:
                return inventory_items

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
            if self.client == "Refurb":
                self.parent.debug("Refurb Repair - No Notification Required")
                return False
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
                if not self.parent.zendesk:
                    self.add_to_zendesk()
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
            fields = {
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
                    manager.add_update(
                        monday_id=self.id,
                        update="Unable to Create a Zendesk User -- Please provide an email address",
                        user="error"
                    )
                else:
                    info = User(name=self.name, email=self.email, phone=self.number)
                    user = zendesk_client.users.create(info)
            custom_fields = []
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
            ticket_audit = zendesk_client.tickets.create(
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
            values = {
                "text6": str(ticket_audit.ticket.id),
                "link1": {"url": "https://icorrect.zendesk.com/agent/tickets/{}".format(ticket_audit.ticket.id),
                          "text": str(ticket_audit.ticket.id)},
                "status5": {"label": "Active"},
                "text5": user.email,
                "text15": self.parent.zendesk.company_name
            }
            attributes = [["number", "text00"], ["address1", "passcode"], ["address2", "dup__of_passcode"],
                          ["postcode", "text93"]]
            for attribute in attributes:
                mon_val = getattr(self, attribute[0])
                zen_val = getattr(self.parent.zendesk, attribute[0], None)
                if not mon_val and zen_val:
                    values[attribute[1]] = zen_val
            self.item.change_multiple_column_values(values)
            self.parent.debug(end="add_to_zendesk")

        def stuart_details_creation(self):

            print(self.id)

            address = [
                self.address2,
                self.address1,
                "London",
                self.postcode
            ]
            address = [line for line in address if line]
            address_string = " ".join(address)

            time = str(datetime.now().hour) + ":" + str(datetime.now().minute)
            reference = "{} -- {}".format(self.id, str(time))

            conversion = [
                ["number", "phone"],
                ["email", "email"],
                ["company_name", "company"]
            ]

            details = {line[1]: getattr(self, line[0]) for line in conversion}

            details["reference"] = reference
            details["address"] = address_string
            details["firstname"] = self.name.split()[0]
            details["lastname"] = self.name.split()[1]

            if self.status == "Book Return Courier":
                details["direction"] = "delivering"
            else:
                details["direction"] = "picking"

            pprint(details)

            return details

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
                manager.add_update(
                    monday_id=self.id,
                    user="system",
                    update="Booking Successful\nJob ID: {}\nPrice: £{}\nPickup ETA: {}\nClick to Confirm Booking: {}".format(
                        text_response["data"]["job_id"], text_response["data"]["price_gross"],
                        text_response["data"]["pickup_eta"][11:19], text_response["data"]["private_job_url"])
                )
                self.parent.zendesk.ticket.custom_fields.append(
                    CustomField(id=360006704157, value=text_response["data"]["public_tracker_url"]))
                zendesk_client.tickets.update(self.parent.zendesk.ticket)
                if from_client:
                    self.capture_gophr_data(info["pickup_postcode"], info["delivery_postcode"], text_response["data"])
                else:
                    self.capture_gophr_data(info["pickup_postcode"], info["delivery_postcode"], text_response["data"],
                                            collect=False)
                result = True
            else:
                # error_code = text_response["error"]["code"].replace('\"', "|")
                notes = text_response["error"]["message"].replace('\"', "|")
                manager.add_update(
                    update="""Booking Failed\n\nNotes: {}""".format(notes),
                    user="error",
                    status=["status4", "!! See Updates !!"]
                )
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
            col_val = create_column_value(id="text5", column_type=ColumnType.text, value=str(monday_id))
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
                        col_val = create_column_value(id=column[1], column_type=ColumnType.hour, hour=hour,
                                                      minute=minute)
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
                data = parse.urlencode(details)
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

        def vend_sync(self):

            # TODO: Create Sale if One has not already been created
            # TODO: Add  customer IDs to Zendesk
            # TODO: Query Zendesk for Customer IDs

            if not self.parent.vend:
                # TODO: Get User
                # TODO: Create Line Items
                # TODO: Post Sale (As Below)
                self.parent.debug("Unable to Adjust Vend Sale as it does not exist")
                return
            else:
                sale = self.parent.vend.VendSale(self.parent.vend)
                sale.sale_attributes = self.parent.vend.sale_info
                sale.sale_attributes.pop("line_items")
                sale.sale_attributes["register_sale_products"] = []

            self.convert_to_vend_codes()
            if len(self.vend_codes) != len(self.m_repairs):
                manager.add_update(
                    monday_id=self.id,
                    user="error",
                    notify=[
                        "Please add {}'s Repairs to Vend Manually, I can't find one or more of the repairs that have been completed on this device".format(
                            self.name), self.user_id]
                )
                self.parent.debug(
                    "Vend Codes Lost During Conversion: D:{} Rs:{} C:{}".format(self.m_device, self.m_repairs,
                                                                                self.m_colour))
            else:
                for code in self.vend_codes:
                    sale.sale_attributes["register_sale_products"].append(sale.create_register_sale_products(code))
                sale.sale_attributes["register_sale_products"][0]["attributes"].append(
                    {"name": "line_note", "value": "IMEI/SN: {}".format(self.imei_sn)})
                self.parent.vend.post_sale(sale.sale_attributes, sale_update=True)

        def adjust_stock_alt(self):
            if len(self.m_repairs) == 0:
                self.parent.debug_print("No Repairs on Monday")
                manager.add_update(
                    monday_id=self.id,
                    user="error",
                    update="No Repairs Given - Cannot Check Out Stock",
                    status=["status_17", "Error - Other"]
                )
            else:
                inventory_items = self.create_inventory_items()
                if len(inventory_items) != len(self.m_repairs):
                    manager.add_update(
                        monday_id=self.id,
                        update="Vend Codes Lost During Conversion - Cannot Adjust Stock\nDevice: {}\nRepairs: {}\nColour: {}".format(
                            self.m_device, self.m_repairs, self.m_colour),  # Notify Gabe
                        notify=[
                            "Vend Codes Lost During Conversion - Cannot Adjust Stock\nDevice: {}\nRepairs: {}\nColour: {}".format(
                                self.m_device, self.m_repairs, self.m_colour).format(self.name), 4251271],
                        user="error",
                        status=["status_17", "Error - Not Found"]
                    )
                else:
                    deductables = self.construct_inventory_deductables(inventory_items)
                    for item in deductables:
                        deductables[item][0].get_parent()
                        val = deductables[item][0].parent_product.stock_level - deductables[item][1]
                        deductables[item][0].parent_product.item.change_column_value(column_id="inventory_oc_walk_in",
                                                                                     column_value=str(val))
                        print("Adjusting Stock: {}".format(deductables[item][0].parent_product.name))
                    stats = self.create_sale_stats(inventory_items)
                    sale_items = []
                    for item in stats[0]:
                        sale_items.append("\n".join(item))
                    update = "SALE STATS:\n\n{}\n\n{}\n{}\n{}\n{}".format("\n\n".join(sale_items),
                                                                          "Multi Discount: £{}".format(stats[1]),
                                                                          "Total Sale Price: £{}".format(stats[2]),
                                                                          "Total Cost: £{}".format(stats[3]),
                                                                          "Margin: {}%".format(stats[4]))
                    manager.add_update(
                        monday_id=self.id,
                        user="system",
                        update=update,
                        status=["status_17", "Complete"]
                    )
                    col_vals = {
                        "numbers": stats[2],
                        "numbers3": stats[3],
                        "numbers5": stats[4],
                        "status5": {"label": str(self.client)}
                    }

                    if self.client == "Warranty":
                        col_vals["numbers"] = 0

                    log = self.parent.boards["new_sales"].add_item(item_name=self.name, column_values=col_vals)
                    log.add_update(update)

        def stock_checker(self, user_id):

            repair_stats = []
            tracked = False
            warning = False

            inventory_items = self.create_inventory_items()

            for item in inventory_items:
                repair_stats.append(item.stock_check())

            if len(inventory_items) != len(self.repairs):
                not_complete = True
            else:
                not_complete = False

            for item in repair_stats:
                if item["tracked"]:
                    tracked = True

                if item["stock"] < 5:
                    warning = True

            if tracked:
                update = 'Estimated Stock Levels:\n\n{}'.format(
                    "\n".join([str(item["name"]) + ': ' + str(item['stock'])]))
            else:
                update = 'Roughly Estimated Stock Levels\nSome of These Products Are Not Tracked:\n\n{}'.format(
                    "\n".join(([str(item["name"]) + ': ' + str(item['stock'])])))

            if not_complete:
                update.append("\n\nThis is not a full check, and some repairs may have been missed while checking")

            if warning or not tracked:
                manager.add_update(
                    self.id,
                    'error',
                    notify=['LOW OR NO STOCK: Please Click Me For More Info', user_id],
                    update=update,
                    checkbox=['check3', False]
                )

            else:
                manager.add_update(
                    self.id,
                    'system',
                    notify=['There is enough stock for the {} repair'.format(self.name), user_id],
                    checkbox=['check3', False]
                )

        def create_sale_stats(self, inventory_items):
            total_sale = 0
            total_cost = 0
            stats = []
            for item in inventory_items:
                if not item.supply_price:
                    item.supply_price = 0
                name = "Repair: {}".format(item.name)
                price = "Sale Price: £{}".format(item.sale_price)
                supply = "Supply Price: £{}".format(item.supply_price)
                stats.append([name, price, supply])
                total_sale += int(item.sale_price)
                total_cost += int(item.supply_price)
            discount = 0
            if len(stats) > 1:
                discount = (len(stats) - 1) * 10
                total_sale = total_sale - discount
            if total_sale == 0:
                total_sale = 1
            margin = ((total_sale - total_cost) / total_sale) * 100
            return [stats, discount, total_sale, total_cost, margin]

        def create_inventory_items(self):
            self.parent.debug(start="convert_to_vend_codes")
            inventory_items = []
            for repair in self.repairs:
                if repair == 35:
                    inventory_items.append(InventoryItem(item_id=901008625))
                    continue
                if repair == 43:
                    inventory_items.append(InventoryItem(item_id=901006495))
                    continue
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
                        manager.add_update(
                            monday_id=self.id,
                            user="error",
                            update="Cannot Find: {}".format(search)
                        )
                        continue
                for product in results:
                    if repair in [69, 83, 84]:
                        inventory_items.append(InventoryItem(item_object=product, refurb=self.refurb))
                    else:
                        inventory_items.append(InventoryItem(item_object=product))
            return inventory_items

        def construct_inventory_deductables(self, inventory_list):
            deductables = {}
            for item in inventory_list:
                if item.sku in deductables:
                    deductables[item.sku][1] += 1
                else:
                    deductables[item.sku] = [item, 1]
            return deductables

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
                    ticket = zendesk_client.tickets(id=self.ticket_id)
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
            macro_result = zendesk_client.tickets.show_macro_effect(self.ticket, macro_id)
            zendesk_client.tickets.update(macro_result.ticket)
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
                manager.add_update(
                    monday_id=self.parent.monday.id,
                    user="email",
                    update="No Macro Sent - This ticket has already received this macro"
                )
            elif not tag:
                self.parent.debug("No Macro Sent - Cannot find notification ID in dropdown_column_dictionary")
                manager.add_update(
                    monday_id=self.parent.monday.id,
                    user="error",
                    update="Cannot Send Macro - Please Let Gabe Know (Notification ID not found in dropdown_column_dictionary)"
                )
            else:
                col_val = create_column_value(id="numbers8", column_type=ColumnType.numbers, value=int(notification_id))
                results = self.parent.boards["macros"].get_items_by_column_values(col_val)
                for item in results:
                    if item.get_column_value(id="status06").index == self.parent.monday.m_service:
                        if item.get_column_value(id="status5").index == self.parent.monday.m_client:
                            if item.get_column_value(id="status0").index == self.parent.monday.m_type:
                                macro_id = item.get_column_value(id="text").text
                                name = "{} {} {} {}".format(item.name, self.parent.monday.service,
                                                            self.parent.monday.client, self.parent.monday.repair_type)
            if macro_id:
                self.execute_macro(macro_id)
                self.ticket.tags.extend([tag])
                zendesk_client.tickets.update(self.ticket)
                self.parent.debug("Macro Sent: {}".format(name))
                self.update_monday_notification_column(notification_id)
            else:
                manager.add_update(
                    monday_id=self.parent.monday.id,
                    update="Cannot Send Macro - Please Let Gabe Know (No Macro On Macro Board)",
                    user="error"
                )
                self.parent.debug(
                    "Could Not Get Macro ID from Macro Board\nNotication ID: {}\nService: {}\nClient: {}\nType: {}".format(
                        notification_id, self.parent.monday.service, self.parent.monday.client,
                        self.parent.monday.repair_type))
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
            zendesk_client.tickets.update(self.ticket)
            self.parent.debug(start="add_comment")

        def compare_with_monday(self):
            if not self.parent.monday:
                self.parent.debug("Cannot Compare Monday and Zendesk Objects - Monday does not exist")
            else:
                for attribute in ["address1", "address2", "postcode", "imei_sn", "passcode", "status", "service",
                                  "client", "repair_type"]:
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
                "tracking_link": 360006704157
            }

            tag_fields = {
                "status": keys.monday.status_column_dictionary["Status"]["values"],
                "service": keys.monday.status_column_dictionary["Service"]["values"],
                "client": keys.monday.status_column_dictionary["Client"]["values"],
                "repair_type": keys.monday.status_column_dictionary["Type"]["values"]
            }
            if field in text_fields:
                self.ticket.custom_fields.append(CustomField(id=text_fields[field], value=value))
                zendesk_client.tickets.update(self.ticket)
            elif field in tag_fields:
                for option in tag_fields[field]:
                    if option["title"] == value:
                        self.ticket.tags.extend([option["z_tag"]])
                        zendesk_client.tickets.update(self.ticket)
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
                "status": "status4",  # Status Column
                "service": "service",  # Servcie Column
                "client": "status",  # Client Column
                "repair_type": "status24",  # Type Column
                "case": "status_14",  # Case Column
                "colour": "status8",  # Colour Column
                "refurb": "status_15",  # Refurb Type Column
                "data": "status55",  # Data Column
                "end_of_day": "blocker",  # End Of Day Column
                "zenlink": "status5"  # Zenlink Column
            },

            "structure": lambda id, value: [id, {"label": value}]
        },

        "index_statuses": {

            "values": {
                "colour": "status8",  # Colour Column
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
                "email": "text5",  # Email Column
                "number": "text00",  # Tel. No. Column
                "z_ticket_id": "text6",  # Zendesk ID Column
                "v_id": "text6",  # Vend Sale ID Column
                "address1": "passcode",  # Street Address Column
                "address2": "dup__of_passcode",  # Company/Flat Column
                "postcode": "text93",  # Postcode Column
                "passcode": "text8",  # Passcode Column
                "imei_sn": "text4",  # IMEI Column
                "company_name": "text15"  # Company Column
            },

            "structure": lambda id, value: [id, value]
        },

        "link": {
            "values": {
                "zendesk_url": "link1"  # Zenlink URL Column
            },

            "structure": lambda id, url, text: [id, {"url": url, "text": text}]

        },

        "dropdown": {
            "values": {
                "device": "device0",  # Device Column
                "repairs": "repair",  # Repairs Column
                "screen_condition": "screen_condition",
                "notifications": "dropdown8"  # Notifications Column
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

        self.column_values = {}

        for category in self.attributes_to_ids:

            values = self.attributes_to_ids[category]["values"]
            structure = self.attributes_to_ids[category]["structure"]

            for column in values:
                if category == "link":
                    diction = structure(values[column], getattr(monday_object, column),
                                        getattr(monday_object, "z_ticket_id"))
                    self.column_values[diction[0]] = diction[1]
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


class RefurbUnit():
    # Monday Boards
    boards = {
        "inventory": monday_client.get_board_by_id(id=868065293),
        "main": monday_client.get_board_by_id(id=349212843),
        "usage": monday_client.get_board_by_id(id=722437885),
        "zendesk_tags": monday_client.get_board_by_id(id=765453815),
        "macros": monday_client.get_board_by_id(id=762417852),
        "gophr": monday_client.get_board_by_id(id=538565672),
        "refurbs": monday_client.get_board_by_id(id=757808757)
    }

    def __init__(self, monday_id):

        self.id = monday_id

        for pulse in monday_client.get_items(ids=[monday_id], limit=1):
            self.item = pulse
            break

        connected = self.item.get_column_value(id="connect_boards1")
        if connected.value:
            self.main_board_id = connected.value["linkedPulseIds"][0]["linkedPulseId"]
            for item in monday_client.get_items(ids=[self.main_board_id], limit=1):
                self.main_board_item = item
                break
        else:
            self.main_board_id = None
            self.main_board_item = None

        self.imei_sn = self.item.name.split()[-1]

    def statuses_to_repairs(self):
        repairs = []
        columns_to_use = {
            "vol_buttons3": 75,
            "mute_button": 36,
            "power_button": 73,
            "earpiece": 88,
            "loudspeaker": 18,
            "wifi3": 93,
            "bluetooth22": 54,
            "bluetooth2": 101,
            "bluetooth1": 85,
            "nfc4": 70,
            "nfc5": 76,
            "front_camera0": 66,
            "front_camera9": 102,
            "front_camera7": 78,
            "haptic": 96,
            "front_screen": 65
        }
        for column in self.item.get_column_values():
            if column.id in columns_to_use and (column.index in [0, 2, 9, 11]):
                if column.id == "haptic" and column.index == 0:
                    repairs.append(82)
                elif column.id == "haptic" and column.index == 2:
                    repairs.append(65)
                else:
                    repairs.append(columns_to_use[column.id])

        self.repairs_required = repairs

    def adjust_main_board_repairs(self):

        self.main_board_item.change_multiple_column_values(
            {"repair": {"ids": self.repairs_required}, "text4": str(self.imei_sn)})

    def get_cost_data(self):

        price_dict = {
            2: "supply_price",
            1: "numbers7",
            8: "numbers1",
            19: "numbers_17",
            109: "numbers2"
        }

        if not self.main_board_id:
            print("No Main Board Connected Item - Nothing Done")
        else:
            main = Repair(monday=self.main_board_id)

            inventory_items = main.monday.convert_to_vend_codes(for_refurb=True)
            print(inventory_items)

            completed = []

            for item in inventory_items:
                if item.get_column_value(id="device").number in [69, 83, 84]:
                    col_id = price_dict[main.monday.m_refurb]
                    name = "{}: {}".format(item.name, main.monday.refurb)
                else:
                    col_id = "supply_price"
                    name = item.name

                completed.append([
                    name,
                    item.get_column_value(id=col_id).number
                ])

            return completed

    def add_costs_to_refurbs(self, listed_repairs):
        update = []
        total = 0
        for item in listed_repairs:
            update.append("{}: £{}".format(item[0], item[1]))
            total += item[1]
        self.item.change_multiple_column_values({
            "numbers6": int(total)
        })
        self.item.add_update(
            "PARTS COST BREAKDOWN:\n\n{}\n\nTotal: {}".format("\n".join(update), total)
        )

    def refurb_unit_sold(self):
        if not self.main_board_item:
            manager.add_update(
                self.id,
                "error",
                notify=[
                    "There is no item on the Main Board for this Refurb. Please correct this so that stock and sales numbers can be proceesed"],
                status=["status", "Cannot Sell"]
            )
        else:
            self.main_board_item.change_multiple_column_values({
                "status4": {"label": "Returned"}
            })


class NewRefurbUnit():
    boards = {
        "refurbs": monday_client.get_board_by_id(876594047),
        "inventory": monday_client.get_board_by_id(868065293),
        "refurb_ref": monday_client.get_board_by_id(883161436)
    }

    columns = [
        ["imei_sn", "text3", "text"],
        ["model", "status4", "text"],
        ["colour", "status2", "text"],
        ["storage", "status6", "text"],
        ["network", "status1", "text"],
        ["face_id", "status7", "text"],
        ["batch_cost", "numbers5", "number"],
        ["rear_glass", "status69", "text"],
        ["unit_cost", "numbers64", "number"],
        ["comments", "long_text", "text"],
        ["screen_index", "status0", "index"]
    ]

    inventory_convert = {
        "iPhone 8": 10,
        "iPhone 8 Plus": 11,
        "iPhone X": 12,
        "iPhone XR": 15,
        "iPhone XS": 13,
        "iPhone XS Max": 14,
        "iPhone 11": 76,
        "iPhone 11 Pro": 77,
        "iPhone 11 Pro Max": 78
    }

    def __init__(self, item_id, user_id):

        self.id = item_id
        self.user_id = user_id

        self.price = False

        for pulse in self.boards["refurbs"].get_items(ids=[item_id], limit=1):
            self.item = pulse
            self.name = self.item.name.replace('"', "")
            break
        self.column_values_raw = self.item.get_column_values()
        self.set_attributes()
        self.get_inventory_by_model()

    def set_attributes(self):
        for column in self.column_values_raw:
            for attribute in self.columns:
                if column.id == attribute[1]:
                    setattr(self, attribute[0], getattr(column, attribute[2], None))

    def get_inventory_by_model(self):
        model_val = create_column_value(id="type", column_type=ColumnType.text, value=self.model)
        self.inventory_by_model = self.boards["inventory"].get_items_by_column_values(model_val)

    def calculate_line(self):
        if not self.get_sale_price():
            print("No Sale Price Provided")
            return False

        if not self.unit_cost:
            manager.add_update(self.id, "error", notify=[
                "Refurbished Calculator: {} Has Not Been Assigned a Unit Cost, PLease Correct This and Try Again".format(
                    self.name), self.user_id])
            return False

        screen = float(self.select_screen_cost())
        faceId = float(self.select_faceid_cost())
        glass = float(self.select_rear_glass_cost())
        parts_cost = screen + faceId + glass
        total_cost = parts_cost + self.unit_cost
        time = float(self.calculate_time_cost())

        self.item.change_multiple_column_values({
            "numbers": time,
            "numbers1": parts_cost,
            "numbers0": self.price,
            "numbers52": total_cost
        })

    def get_sale_price(self):

        search_string = self.item.get_column_value(id="status4").text + " " + self.item.get_column_value(
            id="status6").text
        search_val = create_column_value(id="text", column_type=ColumnType.text, value=search_string)
        results = self.boards["refurb_ref"].get_items_by_column_values(search_val)

        if len(results) == 0:
            manager.add_update(self.id, "error", notify=[
                "Refurbished Unit -- Cannot Find An Entry on The Estimates Board for {}".format(search_string),
                self.user_id])
            self.price = False
        elif len(results) == 1:
            for pulse in results:
                self.reference_id = pulse.id
                self.price = pulse.get_column_value(id="numbers0").number
                break
        elif len(results) > 1:
            manager.add_update(self.id, "error", notify=[
                "Refurbished Unit -- Multiple Entries Found on Estimates Board for {}".format(search_string),
                self.user_id])
            self.price = False

        if not self.price:
            manager.add_update(self.id, "error",
                               notify=["Refurbished Unit -- No Price Provided for {}".format(search_string),
                                       self.user_id])
            self.price = False

        return self.price

    def select_screen_cost(self):
        refurb_key = {
            1: "numbers7",
            8: "numbers1",
            109: "numbers_17",
            2: "supply_price"
        }

        string = tuple([(self.inventory_convert[self.model],), (69,), ()])
        search_val = create_column_value(id="text99", column_type=ColumnType.text, value=str(string))
        results = self.boards["inventory"].get_items_by_column_values(search_val)
        if len(results) == 0:
            manager.add_update(self.id, "error",
                               notify=["Cannot Locate Screen Cost on Inventory Board: {}".format(string), self.user_id])
            return False
        elif len(results) > 1:
            manager.add_update(self.id, "error",
                               notify=["Too Many Screen Costs Found on Inventory Board: {}".format(string),
                                       self.user_id])
            return False
        else:
            for pulse in results:
                item = pulse
                price = pulse.get_column_value(id=str(refurb_key[self.screen_index])).number
                break
            if not price:
                price = item.get_column_value(id="supply_price").number
            if not price:
                manager.add_update(self.id, "error",
                                   notify=["Unable to Ascertain Price of Screen Required", self.user_id])
                return False
            return price

    def select_faceid_cost(self):
        if self.face_id == "FaceID Ok":
            return 0
        string = tuple([(self.inventory_convert[self.model],), (99,), ()])
        search_val = create_column_value(id="text99", column_type=ColumnType.text, value=str(string))
        results = self.boards["inventory"].get_items_by_column_values(search_val)
        if len(results) == 0:
            manager.add_update(self.id, "error",
                               notify=["Cannot Locate Face ID Cost on Inventory Board: {}".format(string)])
            return False
        elif len(results) > 1:
            manager.add_update(self.id, "error",
                               notify=["Too Many Face ID Costs Found on Inventory Board: {}".format(string)])
            return False
        else:
            for pulse in results:
                price = pulse.get_column_value(id="supply_price").number
                break
            return price

    def select_rear_glass_cost(self):
        if self.rear_glass == "Seems OK":
            return 0

        string = tuple([(self.inventory_convert[self.model],), (82,), (17,)])
        search_val = create_column_value(id="text99", column_type=ColumnType.text, value=str(string))
        results = self.boards["inventory"].get_items_by_column_values(search_val)
        if len(results) == 0:
            manager.add_update(self.id, "error", notify=[
                "Cannot Locate Rear Glass (Space Grey) Cost on Inventory Board: {}".format(string)])
            return False
        elif len(results) > 1:
            manager.add_update(self.id, "error", notify=[
                "Too Many Rear Glass (Space Grey) Costs Found on Inventory Board: {}".format(string)])
            return False
        else:
            for pulse in results:
                price = pulse.get_column_value(id="supply_price").number
                break
            return price

    def calculate_time_cost(self):
        time = 1
        if self.face_id != "FaceID Ok":
            time += 1
        if self.rear_glass != "Seems OK":
            time += 1
        if self.comments:
            time += 0.5
        return time


class RefurbGroup():
    boards = {
        "refurbs": monday_client.get_board_by_id(876594047)
    }

    columns = [
        [""]
    ]

    def __init__(self, item_id, user_id):
        for pulse in self.boards["refurbs"].get_items(ids=[item_id], limit=1):
            self.refurb_unit = NewRefurbUnit(item_id, user_id)
            self.group_id = pulse._Item__group_id
            break
        self.user_id = user_id
        self.group_items = self.boards["refurbs"].get_group(self.group_id).get_items()

    def calculate_unit_price(self):
        batch_price = self.refurb_unit.batch_cost
        unit_price = round(batch_price / len(self.group_items), 3)
        return str(unit_price)

    def calculate_batch(self):
        count = 1
        unit_cost = self.calculate_unit_price()
        for item in self.group_items:
            print("===== {} =====".format(item.name))
            if item.get_column_value(id="numbers").number:
                manager.add_update(item.id, "system", notify=[
                    "Refurbished Unit: {} Has already been calculated (Delete the value in 'Time Required' to re-calculate".format(
                        self.name), self.user_id])
            else:
                NewRefurbUnit(item.id, self.user_id).calculate_line(unit_cost)
            print(count)
            count += 1
        manager.add_update(self.refurb_unit.id, "system",
                           notify=["Refurbished Phones Batch Calculation Complete", self.user_id])


class OrderItem():
    boards = {
        "inventory": monday_client.get_board_by_id(id=868065293),
        "orders": monday_client.get_board_by_id(id=878945205),
        "parents": monday_client.get_board_by_id(id=867934405)
    }

    simple_columns = [
        ["ordered", "numbers", "number"],
        ["received", "numbers5", "number"],
        ["unit_cost", "numbers0", "number"],
        ["sku", "text", "text"]
    ]

    def __init__(self, item_id, user_id):

        self.parent_id = None
        self.inventory_items = []
        self.user_id = user_id

        self.id = item_id
        for item in monday_client.get_items(ids=[item_id], limit=1):
            self.item = item
            break
        self.name = self.item.name
        self.set_attributes()

    def set_attributes(self):
        for column in self.item.get_column_values():
            if column.id == "connect_boards":
                self.parent_id = column.value["linkedPulseIds"][0]["linkedPulseId"]
                continue
            for option in self.simple_columns:
                if column.id == option[1]:
                    value = getattr(column, option[2])
                    if not value and option[2] == "number":
                        value = 0
                    setattr(self, option[0], value)

    def get_parent(self):
        if not self.parent_id:
            print("No Parent ID Found")
            return False
        else:
            self.parent = ParentProduct(item_id=self.parent_id)
            return True

    def add_order_to_stock(self):
        if not self.get_parent():
            print("No Parent Item Found")
            return [False, "noparent"]
        elif self.received is None or self.received == 0:
            manager.add_update(self.id, "error", notify=[
                "Please check the order line for {} has a number in the 'Quantity Received' Column".format(self.name),
                self.user_id])
            return [False, "noquantity"]
        else:
            self.collect_inventory_items()
            stats = self.calculate_supply_price()
            self.parent.item.change_multiple_column_values({
                "inventory_oc_walk_in": str(stats[1]),
                "status5": {"label": "No Movement"}
            })
            for pulse in self.inventory_items:
                pulse.change_multiple_column_values({
                    "supply_price": str(stats[0])
                })
            self.item.change_multiple_column_values({
                "numbers2": str(self.parent.stock_level),
                "numbers7": str(stats[1])
            })
            return [True]

    def collect_inventory_items(self):
        col_val = create_column_value(id="text0", column_type=ColumnType.text, value=self.parent.sku)
        for item in self.boards["inventory"].get_items_by_column_values(col_val):
            self.inventory_items.append(item)

    def calculate_supply_price(self):
        on_hand_unit = self.inventory_items[0].get_column_value(id="supply_price").number
        on_hand_quant = self.parent.item.get_column_value(id="inventory_oc_walk_in").number
        if not on_hand_quant:
            on_hand_quant = 0
        on_hand_total = on_hand_unit * on_hand_quant
        new_unit = self.unit_cost
        new_quant = self.received
        new_total = new_unit * new_quant
        total_quant = new_quant + on_hand_quant
        new_supply = round((new_total + on_hand_total) / (total_quant), 3)
        return [new_supply, total_quant]


class InventoryItem():
    boards = {
        "inventory": monday_client.get_board_by_id(id=868065293),
        "orders": monday_client.get_board_by_id(id=822509956),
        "parents": monday_client.get_board_by_id(id=867934405)
    }

    simple_columns = [
        ["sku", "text0", "text"],
        ["device", "numbers3", "number"],
        ["repair", "device", "number"],
        ["colour", "numbers44", "number"],
        ["live", "live", "text"],
        ["vend_id", "text", "text"],
        ["sale_price", "retail_price", "number"],
        ["parent_id", "text1", "text"],
        ["model", "type", "text"],
        ["category", "status43", "text"],
        ["type", "status_11", "text"],
        ["stock_level", "numbers", "number"]
    ]

    status_columns = [
    ]

    price_key = {
        "Glass Only": "numbers7",
        "Glass & Touch": "numbers1",
        "Glass, Touch & LCD": "numbers_17",
        "Glass, Touch & Backlight": "numbers_17",
        "China Screen": "supply_price"
    }

    def __init__(self, item_id=False, item_object=False, refurb=False, repair_id=False):

        # Normal Set Up
        if repair_id:
            self.repair_id = repair_id
        if item_id:
            for item in monday_client.get_items(ids=[item_id], limit=1):
                self.item = item
        elif item_object:
            self.item = item_object
        self.id = self.item.id
        self.name = self.item.name.replace('"', "inch")
        if refurb:
            self.simple_columns.append(["supply_price", self.price_key[refurb], "number"])
            self.name = self.name + " | REFURB: {}".format(refurb)
        else:
            self.simple_columns.append(["supply_price", "supply_price", "number"])
        for column in self.item.get_column_values():
            for option in self.simple_columns:
                if column.id == option[1]:
                    setattr(self, option[0], getattr(column, option[2]))
        if not self.supply_price:
            self.supply_price = self.item.get_column_value(id="supply_price").number
        self.linked_items = None
        self.parent_product = False

    def check_linked_products(self, sku):
        col_val = create_column_value(id="text0", column_type=ColumnType.text, value=sku)
        links = self.boards["inventory"].get_items_by_column_values(col_val)
        if len(links) == 1:
            return [self.item]
        elif len(links) > 1:
            return links

    def stock_check(self):
        if not self.parent_id:
            return False
        else:
            self.get_parent()

            result = self.parent_product.check_stock()

            return result

    def get_parent(self):
        if not self.parent_id:
            return False
        else:
            results = self.boards["parents"].get_items(ids=[self.parent_id], limit=1)
            if len(results) > 1:
                return False
            elif len(results) < 1:
                return False
            else:
                for pulse in results:
                    self.parent_product = ParentProduct(item_id=self.parent_id)
                    return True

    def add_to_product_catalogue(self, user_id):
        # Check for Required Info
        for attribute in ["sku", "model", "category", "type"]:
            if not getattr(self, attribute):
                manager.add_update(self.id, "error", notify=[
                    "Unable to Add Product as no {} has been provided".format(attribute.capitalize()), user_id])
                return False

        if self.parent_id:
            print("Already Has A Parent ID")
            return False

        search_val = create_column_value(id="better_sku", column_type=ColumnType.text, value=str(self.sku))
        results = self.boards["parents"].get_items_by_column_values(column_value=search_val, limit=1)

        if len(results) == 0:
            parent_obj = ParentProduct(create_from_inventory=self)
            parent_obj.add_to_parents_board(self)
            parent = parent_obj.item
        elif len(results) == 1:
            for pulse in results:
                parent = pulse
                break
        else:
            print("Found Multiple Pulses on Parent Board")
            return False
        names = []
        linked_items = self.check_linked_products(self.sku)
        for item in linked_items:
            item.change_column_value(column_id="text1", column_value=parent.id)
            names.append(item.name)
        if len(names) > 1:
            parent.add_update(body="\n".join(names))
            parent.change_column_value(column_id="text3", column_value="Required")


class ParentProduct():
    boards = {
        "parents": monday_client.get_board_by_id(id=867934405),
        "screen_refurbs": monday_client.get_board_by_id(id=874011166),
        "counts": monday_client.get_board_by_id(id=874560619)
    }
    columns = [
        ["vend_id", "id", "text"],
        ["sku", "better_sku", "text"],
        ["model", "type", "text"],
        ["stock_level", "inventory_oc_walk_in", "number"],
        ["add_quantity", "numbers", "number"],
        ["tracking", "text", 'text']
    ]
    price_key = {
        "Glass Only": "numbers7",
        "Glass & Touch": "numbers1",
        "Glass, Touch & Backlight": "numbers_17",
        "Glass, Touch & LCD": "numbers2",
        "China Screen": "supply_price"
    }

    def __init__(self, user_id=False, item_id=False, create_from_inventory=False, refurb=False):

        if user_id:
            self.user_id = user_id

        self.stock_level = None

        if item_id:
            for pulse in self.boards["parents"].get_items(ids=[item_id], limit=1):
                self.item = pulse
                break
            self.id = self.item.id
            self.name = self.item.name.replace('"', " inch")
            self.stock_level = False
            for column in self.item.get_column_values():
                for option in self.columns:
                    if column.id == option[1]:
                        setattr(self, option[0], getattr(column, option[2]))
            if not self.stock_level:
                self.stock_level = 0

        elif create_from_inventory:
            self.name = create_from_inventory.name
            for attribute in self.columns:
                try:
                    inventory_att = getattr(create_from_inventory, attribute[0])
                    setattr(self, attribute[0], inventory_att)
                except AttributeError:
                    print("Cannot Set {} As It Does Not Exist".format(attribute[0]))
        else:
            pass

        try:
            self.stock_level = int(self.stock_level)
        except TypeError:
            self.stock_level = int(0)

    def check_stock(self):

        stats = {
            "name": self.name,
            "stock": int(self.stock_level),
            "tracked": self.tracking
        }

        return stats

    def add_to_parents_board(self, inventory_item):
        col_vals = {attribute[1]: getattr(self, attribute[0]) for attribute in self.columns[:3]}
        linked_items = inventory_item.check_linked_products(self.sku)
        if len(linked_items) > 1:
            col_vals["text3"] = "Required"
        col_vals["status"] = {"label": inventory_item.category}
        col_vals["status6"] = {"label": inventory_item.type}
        self.item = self.boards["parents"].add_item(item_name=self.name, column_values=col_vals)
        self.id = self.item.id

    # def refurb_order_creation(self):
    #     if not self.add_quantity:
    #         manager.add_update(
    #             self.id,
    #             "error",
    #             notify=["You have not specified how many {}'s have been completed. Please correct this and try again",
    #                     self.user_id]
    #         )
    #     else:
    #         order = ScreenRefurb(create_from_parent=self, user_id=self.user_id)
    #         order.add_to_screen_refurbs()
    #         self.item.change_multiple_column_values({
    #             "status5": {"label": "Refurb - Testing"},
    #             "numbers": str(0)
    #         })

    def stock_counted(self):
        if self.add_quantity is None:
            manager.add_update(
                self.id,
                "error",
                notify=["Unable to include Stock Count for {}. You have not entered a quantity for the count".format(
                    self.name), self.user_id],
            )
            return False

        else:
            count = CountItem(create_from_inventory=self)
            count.add_to_count_board()
            new_stock = int(int(self.stock_level) + int(self.add_quantity))
            self.item.change_multiple_column_values({
                "numbers": 0,
                "status5": {"label": "Counted Today"},
                "inventory_oc_walk_in": new_stock,
                "text": 'Yes'
            })


class CountItem():
    boards = {
        "parents": monday_client.get_board_by_id(id=867934405),
        "screen_refurbs": monday_client.get_board_by_id(id=874011166),
        "counts": monday_client.get_board_by_id(id=874560619)
    }
    columns = [
        ["expected", "numbers", "number"],
        ["counted", "numbers0", "number"],
        ["sku", "text", "text"]
    ]

    def __init__(self, user_id=False, item_id=False, create_from_inventory=False):

        if user_id:
            self.user_id = user_id

        if item_id:
            self.id = item_id
            for item in monday_client.get_items(ids=[item_id], limit=1):
                self.item = item
                self.name = self.item.name
                break
            for column in self.item.get_column_values():
                for option in self.columns:
                    if column.id == option[1]:
                        setattr(self, option[0], getattr(column, option[2]))

        elif create_from_inventory:
            self.name = create_from_inventory.name
            self.expected = create_from_inventory.stock_level
            self.counted = create_from_inventory.add_quantity
            self.sku = create_from_inventory.sku

    def add_to_count_board(self):
        col_vals = {attribute[1]: getattr(self, attribute[0]) for attribute in self.columns}
        self.item = self.boards["counts"].add_item(item_name=self.name, column_values=col_vals)
        self.id = self.item.id


class ScreenRefurb():
    simple_columns = [
        ["refurb_quantity", "numbers", "number"],
        ["sku", "text", "text"],
        ["tested_quantity", "numbers0", "number"]
    ]

    boards = {
        "parents": monday_client.get_board_by_id(id='867934405'),
        "screen_refurbs": monday_client.get_board_by_id(id='874011166')
    }

    def __init__(self, user_id=False, item_id=False, create_from_parent=False):

        if user_id:
            self.user_id = user_id

        if item_id:
            self.id = item_id
            for pulse in self.boards["screen_refurbs"].get_items(ids=[item_id], limit=1):
                self.item = pulse
                self.name = self.item.name.replace('"', " Inch")
                break
            for column in self.item.get_column_values():
                for attribute in self.simple_columns:
                    if column.id == attribute[1]:
                        value = getattr(column, attribute[2])
                        if attribute[2] == 'number' and not value:
                            value = 0
                        setattr(self, attribute[0], value)
        elif create_from_parent:
            self.name = create_from_parent.name
            self.refurb_quantity = create_from_parent.add_quantity
            self.sku = create_from_parent.sku

    # def add_to_test_queue(self):
    #
    #     test_group = self.boards["screen_refurbs"].get_group(id="new_group5426")
    #
    #     col_vals = {
    #         "text": self.sku,
    #         "numbers": self.refurb_quantity
    #     }
    #
    #     test_group.add_item(item_name=self.name, column_values=col_vals)
    #
    #     self.item.change_multiple_column_values({"numbers": None})

    def add_to_screen_refurbs(self):
        col_vals = {
            "numbers": self.refurb_quantity,
            "text": self.sku
        }
        self.item = self.boards["screen_refurbs"].add_item(item_name=self.name, column_values=col_vals)
        self.id = self.item.id

    def refurb_complete(self):
        # If Quantity is Empty
        if not self.refurb_quantity:
            manager.add_update(self.id,
                               "error",
                               notify=[
                                   "You have missed out Quantities from {}. Please correct this and try again".format(
                                       self.name), self.user_id])

        # No SKU - should never happen
        elif not self.sku:
            manager.add_update(
                self.id,
                "error",
                notify=["Unable to Add {} x {} as no SKU has been provided. Please check this and try again".format(
                    self.tested_quantity, self.name), self.user_id]
            )

        # Actual stock adjustment process
        else:
            search_val = create_column_value(id="better_sku", column_type=ColumnType.text, value=self.sku)
            results = self.boards["parents"].get_items_by_column_values(search_val)
            if len(results) == 1:
                for pulse in results:
                    parent = ParentProduct(item_id=pulse.id)
                    break
            elif len(results) == 0:
                print("No Parent Item Found - Cannot Adjust Stock :: {}".format(self.sku))
                return False
            else:
                print("More Than One Parent Found - Cannot Adjust Stock :: {}".format(self.sku))
                return False
            new_quantity = int(int(parent.stock_level) + int(self.refurb_quantity))
            parent.item.change_multiple_column_values({
                "inventory_oc_walk_in": new_quantity,
            })

            col_vals = {
                "numbers6": int(parent.stock_level),
                "numbers3": new_quantity,
                'numbers': self.refurb_quantity,
                'text': self.sku
            }

            refurb_record = self.boards['screen_refurbs'].add_item(item_name=self.name, column_values=col_vals)

            self.item.change_multiple_column_values({'numbers': 0})


class StuartClient():
    boards = {
        "stuart_dump": manager.monday_clients["system"][0].get_board_by_id(891724597)
    }

    def __init__(self, production=False):
        self.production = production
        self.authenticate()

    def authenticate(self):

        if self.production:
            url = "https://api.stuart.com/oauth/token"
            payload = "client_id={}&client_secret={}&scope=api&grant_type=client_credentials".format(
                os.environ["STUARTID"], os.environ["STUARTSECRET"])
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = requests.request("POST", url, data=payload, headers=headers)

        else:
            payload = {
                "scope": "api",
                "grant_type": "client_credentials",
                "client_id": os.environ["STUARTIDSAND"],
                "client_secret": os.environ["STUARTSECRETSAND"]
            }
            url = "https://api.sandbox.stuart.com/oauth/token"
            payload = json.dumps(payload)
            headers = {'content-type': "application/json"}

        response = requests.request('POST', url, data=payload, headers=headers)
        print(response)
        print(response.text)
        info = json.loads(response.text)
        self.token = info["access_token"]
        print()
        print()
        print()
        print(self.token)

    def arrange_courier(self, repair_object, user_id, direction):

        if not repair_object.number:
            manager.add_update(
                repair_object.monday.id,
                'error',
                notify=[
                    'Unable to Book Courier: Please provide a phone number',
                    user_id
                ]
            )
            return False

        booking_details = repair_object.monday.stuart_details_creation()
        address_verification = self.validate_address(booking_details)
        if address_verification[0] == 200:
            courier_info = self.format_details(booking_details, repair_object.monday.id, direction)
            parameter_verification = self.validate_job_parameters(courier_info)
            if parameter_verification[0] == 200:
                info = self.create_job(courier_info)
                if info[0] in [401, 422, 503]:
                    manager.add_update(
                        repair_object.monday.id,
                        "error",
                        update="Unable to Book Courier - Gabe will look into it",
                        notify=["Unable to book courier - failure in create_job: {}".format(info[1]),
                                keys.monday.user_ids['gabe']],
                        status=['status4', '!! See Updates !!']
                    )
                    return False

                elif info[0] == 201:
                    update = [str(item) + ": " + str(info[1][item]) for item in info[1]]
                    if direction == 'collecting':
                        status = ["status4", "Courier Booked"]
                    else:
                        status = ["status4", "Return Booked"]
                    manager.add_update(
                        repair_object.monday.id,
                        "system",
                        update="Booking Details:\n{}".format("\n".join(update)),
                        status=status
                    )

                    if repair_object.zendesk:
                        repair_object.zendesk.update_custom_field('tracking_link',
                                                                  info[1]['deliveries'][0]['tracking_url'])

                    self.dump_to_stuart_data(info[1], repair_object, direction)
                    return True

                else:
                    manager.add_update(
                        repair_object.monday.id,
                        "error",
                        notify=["There is an issue with the arrangement of this courier", keys.monday.user_ids['gabe']],
                        update="There was an issue while trying to book this courier - Gabe is looking into it",
                        status=['status4', '!! See Updates !!']
                    )
                    return False

            elif parameter_verification[0] in [422, 401]:
                update = [item + ": " + booking_details[item] for item in booking_details]
                manager.add_update(
                    repair_object.monday.id,
                    "error",
                    notify=["There is an issue with the address you have entered. Please check item updates", user_id],
                    update="Booking Details:\n{}\n\n{}".format("\n".join(update), address_verification[1]),
                    status=['status4', '!! See Updates !!']
                )
                return False

        elif address_verification[0] in [422, 401]:
            update = [item + ": " + booking_details[item] for item in booking_details]
            manager.add_update(
                repair_object.monday.id,
                "error",
                notify=["There is an issue with the address you have entered. Please check item updates", user_id],
                update="Booking Details:\n{}\n\n{}".format("\n".join(update), address_verification[1]),
                status=['status4', '!! See Updates !!']
            )
            return False

        else:
            print("Else Route: arrange_courier")

    def validate_address(self, client_details):
        if self.production:
            url = "https://api.stuart.com/v2/addresses/validate"
        else:
            url = "https://sandbox-api.stuart.com/v2/addresses/validate"

        payload = {
            "address": client_details["address"],
            "type": client_details["direction"],
            "phone": client_details["phone"]
        }

        headers = {'authorization': "Bearer {}".format(self.token)}
        response = requests.request("GET", url, data=payload, headers=headers)
        job_info = json.loads(response.text)

        return self.validation_return(response, job_info)

    def validation_return(self, response, job_info):

        if response.status_code == 422:
            return [422, job_info["message"]]
        elif response.status_code == 401:
            return [401, job_info["message"]]
        elif response.status_code == 200:
            return [200, job_info]

    def validate_job_parameters(self, client_details):
        if self.production:
            url = "https://api.stuart.com/v2/jobs/validate"
        else:
            url = "https://sandbox-api.stuart.com/v2/jobs/validate"

        payload = json.dumps(client_details)

        headers = {
            'content-type': "application/json",
            'authorization': "Bearer {}".format(self.token)
        }
        response = requests.request("POST", url, data=payload, headers=headers)
        job_info = json.loads(response.text)
        return self.validation_return(response, job_info)

    def format_details(self, client_details, monday_id, direction):
        """Takes delivery details (client address, phone, email, direction) and creates the structure required for the create_job function

        Args:
            client_details (dict): Dictionary for client details
            monday_object (MondayRepair): Monday Object (For Status and ID Info)

        Returns:
            dict: Data structure for create_job func
        """
        icorrect = {
            'address': 'iCorrect 12 Margaret Street London W1W 8JQ',
            'email': 'support@icorrect.co.uk',
            'phone': '02070998517',
            'firstname': 'Gabriel',
            'lastname': 'Barr',
            "reference": client_details["reference"],
            "company": "iCorrect Ltd"
        }

        assignment_code = "{} {}".format(monday_id, date.today())

        if direction == 'delivering':
            collect = icorrect
            deliver = client_details
            assignment_code += "*RETURN"

        elif direction == "collecting":
            collect = client_details
            deliver = icorrect
            assignment_code += "*COLLECTION"
        result = {
            "job": {
                "assignment_code": assignment_code,
                "pickups": [{
                    "address": collect["address"],
                    # "comment": "{}",
                    "contact": {
                        "firstname": collect["firstname"],
                        "lastname": collect["lastname"],
                        "phone": collect["phone"],
                        "email": collect["email"],
                        "company": collect["company"]
                    }
                }],
                "dropoffs": [{
                    "package_type": "small",
                    # "package_description": "The blue one.",
                    "client_reference": deliver["reference"],
                    "address": deliver["address"],
                    # "comment": "2nd floor on the left",
                    "contact": {
                        "firstname": deliver["firstname"],
                        "lastname": deliver["lastname"],
                        "phone": deliver["phone"],
                        "email": deliver["email"],
                        "company": deliver["company"]
                    }
                }]
            }
        }
        return result

    def create_job(self, payload, production=False):
        """Takes a dictionoary of job details and sends a request

        Args:
            payload (dictionary): Dictionary of details returned by the format_details function
        """

        if self.production:
            url = "https://api.stuart.com/v2/jobs"
        else:
            url = "https://sandbox-api.stuart.com/v2/jobs"

        payload = json.dumps(payload)

        print(self.token)

        headers = {
            'content-type': "application/json",
            'authorization': str("Bearer ") + str(self.token)
        }

        print(headers)

        response = requests.request("POST", url, data=payload, headers=headers)

        job_info = json.loads(response.text)

        return [response.status_code, job_info]

    def dump_to_stuart_data(self, job_info, repair_object, direction):
        name = str(repair_object.monday.name) + " " + direction.capitalize()
        if not self.production:
            name += " {}".format("SANDBOX")

        booking_hour = int(datetime.now().hour)
        booking_minute = int(datetime.now().minute)

        cost_ex = round(float((job_info['pricing']['price_tax_excluded'])), 2)
        vat = round(float((job_info['pricing']['tax_amount'])), 2)

        distance = round(float((job_info['distance'])), 2)

        assignment_code = job_info['assignment_code']

        estimated_time = round(float((job_info['duration'])), 2)

        col_vals = {
            "text": str(job_info["id"]),
            'hour': {"hour": booking_hour, 'minute': booking_minute},
            'numbers': cost_ex,
            'numbers8': vat,
            'numbers_1': distance,
            'numbers7': estimated_time,
            'text9': assignment_code
        }

        if direction == 'collecting':
            col_vals['text80'] = repair_object.monday.postcode
            col_vals['collection_postcode'] = 'W1W 8JQ'
        elif direction == 'delivering':
            col_vals['text80'] = 'W1W 8JQ'
            col_vals['collection_postcode'] = repair_object.monday.postcode

        item = self.boards["stuart_dump"].add_item(item_name=name, column_values=col_vals)
        item.add_update("\n".join([str(item) + ": " + str(job_info[item]) for item in job_info]))

    def add_to_stuart_data(self, job_id, data, column=False):

        search_val = create_column_value(id="text", column_type=ColumnType.text, value=str(job_id))
        results = self.boards["stuart_dump"].get_items_by_column_values(search_val)
        if len(results) == 0:
            print("No Pulse Found on Stuart Data")
            return False
        elif len(results) == 1:
            print('FOUND ON STUART BOARD')
            for pulse in results:
                item = pulse
            hour = int(datetime.now().hour)
            minute = int(datetime.now().minute)
            if column:
                item.change_multiple_column_values({
                    column: {'hour': hour, 'minute': minute}
                })
            item.add_update(data)
        elif len(results) > 1:
            print("Too Many Pulses Found on Stuart Data")
            return False


class RefurbRepair():
    boards = {
        'main': monday_client.get_board_by_id(349212843),
        'refurbs': monday_client.get_board_by_id(876594047)
    }

    basic_stats = [
        ['model', 'status4', 'text'],
        ['grade', 'status_16', 'text'],
        ['colour', 'status2', 'text'],
        ['phone_check', 'status_14', 'text'],
        ['imei', 'text3', 'text'],
        ['code', 'text84', 'text'],
        ['phase', 'status_122', 'text'],
        ['status', 'status5', 'text']
    ]

    phase_face_id_raw = [
        ['faceid', 'front_screen5', 'index', 99]
    ]

    phase_screen_rear_raw = [
        ['screen', 'status_1', 'index', 96],
        ['rear_glass', 'front_screen', 'index', 82]
    ]

    phase_internal_raw = [
        ['battery', 'haptic2', 'index', 71],
        ['microphone', 'rear_housing', 'index', 66],
        ['charging_port', 'microphone', 'index', 54],
        ['wireless', 'charging_port40', 'index', 101],
        ['mute_vol_buttons', 'charging_port8', 'index', 75],
        ['power_button', 'charging_port', 'index', 36],
        ['earpiece', 'charging_port4', 'index', 73],
        ['speaker', 'power_button', 'index', 88],
        ['wifi', 'power_button9', 'index', 18],
        ['bluetooth', 'wifi', 'index', 93],
        ['rcam', 'bluetooth', 'index', 70],
        ['fcam', 'rear_camera', 'index', 76],
        ['lens', 'front_camera', 'index', 7],
        ['siri', 'rear_lens', 'index', 102],
        ['haptic', 'siri', 'index', 78],
        ['nfc', 'haptic3', 'index', 85]
    ]

    def __init__(self, monday_id, user_id):
        self.id = str(monday_id)
        self.user_id = user_id

        for pulse in self.boards["refurbs"].get_items(ids=[monday_id], limit=1):
            self.item = pulse
            self.name = self.item.name.replace('"', "")
            break

        self.phase_face_id = []
        self.phase_screen_rear = []
        self.phase_internal = []

        self.all_columns = self.phase_face_id_raw + self.phase_screen_rear_raw + self.phase_internal_raw

        self.column_values_raw = self.item.get_column_values()

        self.set_attributes()

        self.create_phases()

    def set_attributes(self):
        all_atts = self.phase_face_id_raw + self.phase_internal_raw + self.phase_screen_rear_raw + self.basic_stats
        for column in self.column_values_raw:
            for attribute in all_atts:
                if column.id == attribute[1]:
                    value = getattr(column, attribute[2], None)
                    # Will Need to Put in a check to ensure all columns are filled in here once phonecheck API is integrated
                    setattr(self, attribute[0], value)

    def create_phases(self):
        success = [3, 16, None, 5]
        for column in self.phase_face_id_raw:
            if getattr(self, column[0]) not in success:
                self.phase_face_id.append(column[0])
        for column in self.phase_screen_rear_raw:
            if getattr(self, column[0]) not in success:
                self.phase_screen_rear.append(column[0])
        for column in self.phase_internal_raw:
            if getattr(self, column[0]) not in success:
                self.phase_internal.append(column[0])

    def check_phases(self):
        repairs = []
        columns = self.phase_face_id_raw + self.phase_screen_rear_raw + self.phase_internal_raw
        pprint(columns)
        phases = {
            1: 'Face ID',
            2: 'Rear Glass/Screen IC',
            3: 'Internals',
            4: 'Repairs Complete'
        }
        count = 1
        for phase in [self.phase_face_id, self.phase_screen_rear, self.phase_internal]:
            for item in phase:
                repairs.append([line[3] for line in columns if item == line[0]][0])
            if repairs:
                print('phase complete - to be ported to main')
                self.new_phase = phases[count]
                col_vals = {'status_122': {'label': self.new_phase}}
                if self.new_phase == 'Repairs Complete':
                    col_vals['status5'] = {'label': 'Ready For Testing'}
                self.item.change_multiple_column_values(col_vals)
                return repairs
            count += 1
        print('all repairs completed')
        return False

    def add_to_main(self, repairs):

        # Need to determine group and assign to tech

        groups = {
            'Face ID': keys.monday.main_groups['meesha'],
            'Rear Glass/Screen IC': keys.monday.main_groups['mcadam'],
            'Internals': keys.monday.main_groups['today'],
        }

        name = 'REFURB: ({}) {} {} {}'.format(self.code, self.model, self.colour, self.new_phase.upper())

        todays_date = str(date.today())

        col_vals = {
            'repair': {'ids': repairs},
            'status': {'label': 'Refurb'},
            'status24': {'label': 'Repair'},
            'text84': self.id,
            'date36': {'date': todays_date},
            'status4': {'label': 'Awaiting Confirmation'},
            'status5': {'label': 'Severed'},
            'text4': self.imei
        }

        pprint(col_vals)

        for group in self.boards['main'].get_groups():
            if group.id == groups[self.new_phase]:
                group.add_item(item_name=name, column_values=col_vals)
                return True

        self.boards["main"].add_item(item_name=name, column_values=col_vals)
        return False


class MainRefurbComplete():
    boards = {
        'main': monday_client.get_board_by_id(349212843),
        'refurbs': monday_client.get_board_by_id(876594047)
    }

    columns = [
        ['refurb_id', 'text84', 'text'],
        ['repairs', 'repair', 'ids']
    ]

    column_conversions = {
        71: 'haptic2',
        66: 'rear_housing',
        54: 'microphone',
        101: 'charging_port40',
        75: 'charging_port8',
        36: 'charging_port',
        73: 'charging_port4',
        88: 'power_button',
        18: 'power_button9',
        93: 'wifi',
        70: 'bluetooth',
        76: 'rear_camera',
        7: 'front_camera',
        102: 'rear_lens',
        78: 'siri',
        85: 'haptic3',
        82: 'front_screen',
        99: 'front_screen5',
        96: 'status_1',
        69: 'status_1',
        74: 'status_1',
        84: 'status_1',
        89: 'status_1',
        90: 'status_1',
        83: 'status_1',
        90: 'status_1',
    }

    def __init__(self, monday_id, user_id):
        self.id = monday_id
        self.user_id = user_id

        for pulse in self.boards['main'].get_items(ids=[monday_id], limit=1):
            self.item = pulse
            self.name = pulse.name
            break

        self.column_values_raw = self.item.get_column_values()

        self.set_attributes()

        for pulse in self.boards['refurbs'].get_items(ids=[self.refurb_id], limit=1):
            self.refurb_item = pulse
            break

    def set_attributes(self):
        for column in self.column_values_raw:
            for attribute in self.columns:
                if column.id == attribute[1]:
                    value = getattr(column, attribute[2], None)
                    # Will Need to Put in a check to ensure all columns are filled in here once phonecheck API is integrated
                    setattr(self, attribute[0], value)

    def adjust_columns(self):
        col_vals = {}
        for repair in self.repairs:
            col_vals[self.column_conversions[repair]] = {'index': 16}
        self.refurb_item.change_multiple_column_values(col_vals)

    def move_to_next_phase(self):

        refurb = RefurbRepair(self.refurb_id, self.user_id)
        repairs = refurb.check_phases()

        if repairs:
            refurb.add_to_main(repairs)
        else:
            refurb.item.change_multiple_column_values({
                'status_122': {'label': 'Repairs Complete'},
                'status5': {'label': 'Ready For Testing'}
            })


class PhoneCheckResult:
    boards = {
        'main': monday_client.get_board_by_id(349212843),
        'refurbs': monday_client.get_board_by_id(876594047)
    }

    # Missing From Phone Check
    # [Charging Port, Wireless]

    standard_checks = {
        'Bluetooth': 'wifi',  # Bluetooth Column
        'Ear Speaker': 'charging_port4',  # Earpiece & Mesh Column
        'Flashlight': None,  # HAS NO Column
        'Flip Switch': 'charging_port8',  # Mute/Vol Buttons Column
        'Front Camera': 'rear_camera',  # Front Camera Column
        'Front Microphone': 'rear_lens',  # Siri Column
        'Front Video Camera': 'rear_camera',  # Front Camera Column
        'Front Camera Quality': 'rear_camera',  # Front Camera Column
        'Loud Speaker': 'power_button',  # Loudspeaker Column
        'Microphone': 'rear_housing',  # Microphone Column
        'Network Connectivity': None,  # HAS NO Column
        'Power Button': 'charging_port',  # Power Button Column
        'Proximity Sensor': 'rear_camera',  # Front Camera Column
        'Rear Camera': 'bluetooth',  # Rear Camera Column
        'Rear Camera Quality': 'bluetooth',  # Rear Camera Column
        'Rear Video Camera': 'bluetooth',  # Rear Camera Column
        'Telephoto Camera': 'bluetooth',  # Rear Camera Column
        'Telephoto Camera Quality': 'bluetooth',  # Rear Camera Column
        'Vibration': 'siri',  # Haptic Column
        'Video Microphone': 'charging_port',  # Power Button Column
        'Volume Down Button': 'charging_port8',  # Mute/Volume Column
        'Volume Up Button': 'charging_port8',  # Mute/Volume Column
        'Wifi': 'power_button9',  # Wifi Column
        'Face ID': 'front_screen5',  # Face ID Check Column
        'Glass Cracked': 'status_1',  # Front Screen Column
        'LCD': 'status_1',  # Front Screen Column
        'NFC': 'haptic3'  # NFC Column
    }

    def __init__(self, monday_id, user_id):

        self.refurb_id = monday_id
        self.user_id = user_id

        for pulse in self.boards['main'].get_items(ids=[monday_id], limit=1):
            self.refurb_item = pulse
            break

        self.imei = self.refurb_item.get_column_value(id='text3').text

    def get_device_info(self):

        dictionary = {
            'Apikey': os.environ['PHONECHECK'],
            'Username': 'icorrect1',
            'IMEI': self.imei
        }

        form = parse.urlencode(dictionary)
        bytes_obj = BytesIO()
        crl = pycurl.Curl()
        crl.setopt(crl.URL, 'https://clientapiv2.phonecheck.com/cloud/cloudDB/GetDeviceInfo')
        crl.setopt(crl.WRITEDATA, bytes_obj)
        crl.setopt(crl.POSTFIELDS, form)
        crl.perform()
        crl.close()
        response = bytes_obj.getvalue()
        self.phone_check_raw = response.decode('utf8')
        check_info = json.loads(self.phone_check_raw)
        if check_info:
            return check_info
        else:
            return False

    def convert_check_info(self, check_info):
        code_to_apply = self.get_next_code()
        col_vals = {
            'numbers17': int(check_info['BatteryHealthPercentage']),
            'text84': code_to_apply
        }
        self.batt_percentage = int(check_info['BatteryHealthPercentage'])
        if self.batt_percentage < 84:
            col_vals['haptic2'] = {'index': 2}
        else:
            col_vals['haptic2'] = {'index': 3}

        all_checks = []
        ignore = ['Face ID', 'LCD', 'Glass Cracked']

        for fault in check_info['Failed'].split(','):
            all_checks.append([fault, 'Failed'])
            if fault in ignore:
                continue
            if fault in self.standard_checks and self.standard_checks[fault]:
                col_vals[self.standard_checks[fault]] = {'index': 2}

        for passed in check_info['Passed'].split(','):
            all_checks.append([passed, 'Passed'])
            if passed in ignore:
                continue

            if (passed in self.standard_checks)\
                    and (self.standard_checks[passed])\
                    and (self.standard_checks[passed] not in col_vals):

                col_vals[self.standard_checks[passed]] = {'index': 3}

        return [all_checks, col_vals]

    def record_check_info(self):

        info = self.get_device_info()

        if not info:
            manager.add_update(
                self.refurb_id,
                'error',
                status=[
                    'status_14',
                    'Unable to Fetch'
                ],
                notify=[
                    'Unable to Find this IMEI on Phonecheck',
                    self.user_id
                ]
            )
            return False
        add_to_board = self.convert_check_info(info)
        add_to_board[1]['status_14'] = {'label': 'Complete'}
        for item in add_to_board[1]:
            value = {item: add_to_board[1][item]}
            print(value)
            self.refurb_item.change_multiple_column_values(value)
        update = [str(item[0]) + ': ' + str(item[1]) for item in add_to_board[0]]
        self.refurb_item.add_update("\n".join(update))

    def get_next_code(self):

        for pulse in monday_client.get_items(ids=[906832350], limit=1):
            item = pulse

        code = item.get_column_value(id='text0').text
        letter = code.split('-')[0]
        number = code.split('-')[1]
        new_code = str(letter) + str(int(number) + 1)
        replace_code = str(letter) + '-' + str(int(number) + 1)
        item.change_multiple_column_values({
            'text0': replace_code
        })
        return new_code


class BackMarketSale:

    api_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Language': 'en-gb',
        'User-Agent': 'iCorrect'
    }

    boards = {
    }

    def __init__(self, monday_id=False, production=False):

        if production:
            self.api_headers['Authorization'] = 'Basic {}'.format(os.environ['BACKMARKET'])
            self.url_start = 'https://www.backmarket.fr/ws'
        else:
            self.api_headers['Authorization'] = 'Basic {}'.format(os.environ['BACKMARKETSAND'])
            self.url_start = 'https://preprod.backmarket.fr/ws'

        self.refurb_item = None
        self.refurb_id = None
        self.refurb_name = None
        self.refurb_col_vals = []

        if monday_id:
            self.get_refurb_pulse(monday_id)

    def get_order(self, back_market_id):

        url = '{}/orders/{}'.format(self.url_start, back_market_id)
        response = requests.request('GET', url=url, headers=self.api_headers)
        formatted = json.loads(response.text)

        return formatted


    def get_refurb_pulse(self, monday_id):
        self.refurb_id = monday_id
        for pulse in manager.monday_clients['system'][0].get_items(ids=[self.refurb_id], limit=1):
            self.refurb_item = pulse
            self.refurb_name = pulse.name
            self.refurb_col_vals = pulse.get_column_values()
            break

    def format_order_for_monday(self, order_dictionary):
        print(order_dictionary)

    def move_order_info_to_monday(self):

        for value in self.refurb_col_vals:
            if value.id == 'text8':
                backmarket_id = value.text

        if not backmarket_id:
            print('No Backmarket ID Provided  - Cannot Get Data')
            return False

        details = self.get_order(backmarket_id)

        update_vals = []

        update_dictionary = {
            'numbers2': {
                'attribute': 'number',
                'value': details['price']
            },
            'text89': {
                'attribute': 'text',
                'value': details['billing_address']['first_name'] + ' ' + details['billing_address']['first_name']
            },
            'packing_sheet_': {
                'attribute': 'text',
                'value': details['tracking_url']
            },
            'text28': {
                'attribute': 'text',
                'value': str(details['orderlines'][0]['listing_id'])
            }
        }

        for value in self.refurb_col_vals:
            if value.id in update_dictionary:
                setattr(value, update_dictionary[value.id]['attribute'], update_dictionary[value.id]['value'])
                update_vals.append(value)

        self.refurb_item.change_multiple_column_values(update_vals)
        update_body = []
        for item in details:
            update_body.append('{}: {}'.format(item, details[item]))
        self.refurb_item.add_update(body='\n'.join(update_body))


    def edit_listing(self, catalog_string, test=False):

        url = '{}/listings'.format(self.url_start)
        print(catalog_string)
        if test:
            body = self.standard_catalog()
        else:
            body = {
                "encoding": "latin1",
                "delimiter": ";",
                "quotechar": "\"",
                "catalog": catalog_string
            }

        print(body)

        body = json.dumps(body)
        response = requests.request('POST', url=url, headers=self.api_headers, data=body)

        print(response)
        print(response.text)

    def create_catalog_string(self, listing_model):

        catalog = ''
        headers_list = []

        for item in listing_model:
            headers_list.append(item)

        headers_string = ';'.join(headers_list) + ';\\n'

        values_list = []

        for item in listing_model:
            values_list.append(str(listing_model[item]))

        values_string = ';'.join(values_list)

        final_string = headers_string + values_string + ';'

        return final_string

    def format_listing_model(self, backmarket_id, sku, quantity, price, grading, touchid_broken=False):

        required = {
            'backmarket_id': int(backmarket_id),  # REQUIRED[int] - Backmarket Product ID (Must be known)
            'sku': str(sku),  # REQUIRED[string] - SKU of offer, taken from backmarket
            'quantity': int(quantity),  # REQUIRED[string] - Quantity of units available for this sale
            'price': int(price),  # REQUIRED[float] - Price of Sale
            'state': int(grading),  # REQUIRED[int] - Grading of iPhone
            'warranty': 12,  # REQUIRED[int] - Months of Warranty (6/12 minimum??)
        }

        optional = {
            'comment': None,  # [string:500] Comment for the sale (description)
            'currency': None,  # [string:10] Type of currency (Defaults to EUR)
            'shipper_1': None,  # [string:**kwargs] Company that will ship the sale
            'shipping_price_1': None,  # [float] Cost of this shipping option
            'shipper_delay_1': None,  # [float] # Delay before the package will be collected (in hours)
        }

        for item in optional:
            if optional[item]:
                required[item] = optional[item]

        return required

    def standard_catalog(self):

        body = {
            "encoding": "latin1",
            "delimiter": ";",
            "quotechar": "\"",
            "header": True,
            "catalog": "sku;backmarket_id;quantity;warranty_delay;price;state;\n1111111111112;1151;2;6;180;2;\n1111111111113;1151;13;12;220;1;"
        }

        return body