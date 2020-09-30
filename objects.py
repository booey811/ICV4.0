import json
import os
import requests
from datetime import datetime, timedelta
from pprint import pprint

from moncli import MondayClient, create_column_value, ColumnType, NotificationTargetType
from moncli.api_v2.exceptions import MondayApiError
from zenpy import Zenpy
from zenpy.lib import exception as zenpyExceptions
from zenpy.lib.api_objects import CustomField

import settings
import keys.vend
import keys.monday


class Repair():

    # Application Clients
    monday_client = MondayClient(
        user_name='systems@icorrect.co.uk',
        api_key_v1=os.environ["MONV1SYS"],
        api_key_v2=os.environ["MONV2SYS"]
        )

    zendesk_client = Zenpy(
        email='zendesk@icorrect.co.uk',
        token=os.environ["ZENDESK"],
        subdomain="icorrect"
        )

    # Monday Boards
    boards = {
        "logging": monday_client.get_board_by_id(id=736027251),
        "inventory": monday_client.get_board_by_id(id=703218230),
        "main": monday_client.get_board_by_id(id=349212843),
        "usage": monday_client.get_board_by_id(id=722437885),
        "zendesk_tags": monday_client.get_board_by_id(id=765453815),
        "macros": monday_client.get_board_by_id(id=762417852)
    }

    def __init__(self, webhook_payload=False, vend=False, monday=False, zendesk=False, test=False):

        self.debug_string = []
        self.vend = None
        self.monday = None
        self.zendesk = None
        if webhook_payload:
            self.payload = webhook_payload
        else:
            self.payload = None

        if vend:
            self.include_vend(vend)
            self.source = "vend"
            self.name = self.vend.customer_info["first_name"] + " " + self.vend.customer_info["last_name"]
            self.email = self.vend.customer_info["email"]
            self.number = None
            self.alt_numbers = []
            for number in [self.vend.mobile, self.vend.phone, self.vend.fax]:
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
            self.number = self.monday.phone

        elif zendesk:
            self.source = "zendesk"
            self.include_zendesk(zendesk)
            self.name = self.zendesk.name
            self.email = self.zendesk.email
            self.number = self.zendesk.number

        elif test:
            self.name = "Jeremiah Bullfrog"

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

        elif self.source == 'vend':
            col_val = create_column_value(id='text88', column_type=ColumnType.text, value=str(self.vend.id))
            for item in self.monday_client.get_board(id="349212843").get_items_by_column_values(col_val):
                self.include_monday(item.id)

            if self.monday:
                if self.monday.z_ticket_id:
                    self.include_zendesk(self.monday.z_ticket_id)

        elif self.source == 'zendesk':
            col_val = create_column_value(id='text6', column_type=ColumnType.text, value=str(self.zendesk.ticket_id))
            for item in self.monday_client.get_board(id="349212843").get_items_by_column_values(col_val):
                self.include_monday(item.id)

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
            if self.source == "zendesk":
                self.monday.columns.column_values["status5"] = {"label": "Active"}
                self.monday.columns.column_values["text6"] = str(self.zendesk.id)
            item = self.boards["main"].add_item(item_name=self.name, column_values=self.monday.columns.column_values)

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

    def debug_print(self, console=False):
        if not console:
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
        else:
            print("\n".join(self.debug_string))

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

            if vend_sale_id:

                self.id = vend_sale_id
                self.sale_info = self.query_for_sale()
                self.customer_id = str(self.sale_info["customer_id"])
                self.customer_info = self.query_for_customer()

                self.name = "{} {}".format(self.customer_info["first_name"], self.customer_info["last_name"])
                self.phone = self.customer_info["phone"]
                self.mobile = self.customer_info["mobile"]
                self.fax = self.customer_info["fax"]
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

        def convert_to_monday_codes(self):

            inv_board = self.parent.monday_client.get_board_by_id(id=703218230)

            monday_object = MondayRepair(created=self.name)

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

            self.parent.monday = monday_object

        def create_eod_sale(self):

            self.parent.debug(start="create_eod_sale")

            if not self.parent.monday:
                self.parent.debug("No Monday Object to Generate Repairs From")
            else:
                self.sale_to_post = self.VendSale(self)
                self.sale_to_post.create_register_sale_products(self.parent.monday.vend_codes)
                self.sale_to_post.sale_attributes["status"] = "ONACCOUNT_CLOSED"

                if self.id:
                    self.sale_to_post.sale_attributes["id"] = self.id

            self.parent.debug(end="create_eod_sale")

        def post_sale(self, vend_sale):

            self.parent.debug(start="post_sale")

            url = "https://icorrect.vendhq.com/api/register_sales"

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

                setattr(self, attribute, getattr(self, m_attribute))

            self.parent.debug(end="translate_column_data")

        def retreive_column_data(self):
            self.parent.debug(start="retreive_column_data")
            column_values = self.item.get_column_values()
            for item in keys.monday.col_ids_to_attributes:
                if keys.monday.col_ids_to_attributes[item]['attribute'] is not None:
                    col_id = item
                    for value in column_values:
                        if value is None:
                            continue
                        else:
                            if value.id == col_id:
                                try:
                                    setattr(self, keys.monday.col_ids_to_attributes[item]['attribute'],
                                            getattr(value, keys.monday.col_ids_to_attributes[item]["value_type"][0]))
                                except KeyError:
                                    print(
                                        "*811*ERROR: KEY: Cannot set {} Attribute in Class".format(keys.monday.col_ids_to_attributes[item]['attribute']))
                                except TypeError:
                                    print(
                                        "*811*ERROR: TYPE: Cannot set {} Attribute in Class".format(keys.monday.col_ids_to_attributes[item]['attribute']))
            self.parent.debug(end="retreive_column_data")


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
                    notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name)
                )
                return False
            # Check if some type of screen repair has been completed
            if any(repair in self.m_repairs for repair in [69, 74, 84, 89, 90, 83]):
                # Check that screen condition has been selected/not left blank
                if not self.m_screen_condition:
                    self.add_update(
                        "You have not selected a screen condition for this repair - please select an option from the dropdown menu and try again",
                        user="error",
                        notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name)
                    )
                    return False
                # Check that colour has been selected/not left blank
                elif self.m_colour is None or self.m_colour == 5:
                    self.add_update(
                        "You have not selected a colour for the screen of this device - please select a colour option and try again",
                        user="error",
                        notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name)
                    )
                    return False
                # Check that a refurb type has been selected/not left blank
                elif not self.m_refurb or self.m_refurb == 5:
                    self.add_update(
                        "You have not selected what refurb variety of screen was used with this repair - please select a refurbishmnet option and try again",
                        user="error",
                        notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name)
                    )
                    return False
            # Check that IMEI has been recorded
            if not self.imei_sn:
                self.add_update(
                    "This device does not have an IMEI or SN given - please input this and try again",
                    user="error",
                    notify="You have missed out essential infromation from {}'s repair. Please check the pulse updates and correct this before proceeding".format(self.name)
                )
                return False
            return True
            self.parent.debug(end="check_column_presence")


        def add_update(self, update, user=False, notify=False):
            self.parent.debug(start="add_update")
            if user == 'error':
                client =  MondayClient(user_name='admin@icorrect.co.uk', api_key_v1=os.environ["MONV1ERR"], api_key_v2=os.environ["MONV2ERR"])
                for item in client.get_items(ids=[int(self.id)], limit=1):
                    monday_object = item
                    item.change_column_value(column_id="status4", column_value={"label": "!! See Updates !!"})
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
            self.convert_to_vend_codes()
            if len(self.vend_codes) != len(self.repairs):
                self.parent.debug("Cannot Adjust Stock -- vend_codes {} :: {} m_repairs".format(len(self.vend_codes), len(self.repairs)))
                self.add_update("Cannot Adjust Stock - Vend Codes Lost During Conversion", user="error")
            else:
                self.parent.vend = Repair.VendRepair(self.parent)
                self.parent.vend.create_eod_sale()
                self.parent.vend.post_sale(self.parent.vend.sale_to_post)
                for repair in self.repair_names:
                    col_vals = {
                        "text": self.name,
                        "text2": self.parent.source.capitalize(),
                        "numbers": self.repair_names[repair][3],
                        "numbers4": self.repair_names[repair][2],
                        "numbers_1": self.repair_names[repair][1]
                    }
                    try:
                        self.parent.boards["usage"].add_item(item_name=self.repair_names[repair][0], column_values=col_vals)
                    except MondayApiError:
                        self.parent.boards["usage"].add_item(item_name="Experienced Parse Error While Adding to Usage", column_values=col_vals)
                        self.parent.debug("Experienced Parse Error While Adding to Usage")
                    finally:
                        self.item.change_multiple_column_values({"blocker": {"label": "Complete"}})
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


            self.parent = repair_object


            if not created:
                self.ticket_id = zendesk_ticket_number
                try:
                    ticket = self.parent.zendesk_client.tickets(id=self.ticket_id)
                except zenpyExceptions.RecordNotFoundException:
                    self.debug("Ticket {} Does Not Exist".format(zendesk_ticket_number))
                    ticket = False

                if ticket:
                    self.ticket = ticket
                    self.user = self.ticket.requester
                    self.user_id = self.user.id

                    self.name = self.user.name
                    self.email = self.user.email
                    self.number = self.user.phone


                    self.convert_to_attributes()

                else:
                    self.debug("Unable to find Zendesk ticket: {}".format(self.ticket_id))
            else:
                pass

        def convert_to_attributes(self):

            self.parent.debug(start="convert_to_attributes")

            self.tag_conversion()

            custom_fields = {
                "imei_sn": 360004242638,
                "monday_id": 360004570218,
                "passcode": 360005102118,
                "postcode": 360006582758,
                "address1": 360006582778,
                "address2": 360006582798,
                "monday_id": 360004570218
            }

            for field in self.ticket.custom_fields:
                for attribute in custom_fields:
                    if field["value"]:
                        if field["id"] == custom_fields[attribute]:
                            setattr(self, attribute, field["value"])

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



        # def convert_to_attributes(self):
        #     self.parent.debug(start="convert_to_attributes")
        #     self.tag_conversion()
        #     custom_fields = {
        #         "imei_sn": [False, 360004242638],
        #         "monday_id": [False, 360004570218],
        #         "passcode": [False, 360005102118],
        #         "postcode": [False, 360006582758],
        #         "address1": [False, 360006582778],
        #         "address2": [False, 360006582798],
        #         "client": [True, 360010408778],
        #         "service": [True, 360010444117],
        #         "repair_type": [True, 360010444077],
        #         "monday_id": [False, 360004570218]
        #     }
        #     for field in self.ticket.custom_fields:
        #         for attribute in custom_fields:
        #             if field["value"]:
        #                 if field["id"] == custom_fields[attribute][1]:
        #                     if custom_fields[attribute][0]:
        #                         text = str(field["value"])
        #                         col_val = create_column_value(id="text", column_type=ColumnType.text, value=text)
        #                         results = self.parent.boards["zendesk_tags"].get_items_by_column_values(col_val)
        #                         if len(results) > 1:
        #                             self.parent.debug("Too many results from tag board")
        #                         elif len(results) == 0:
        #                             self.parent.debug("No results from tag board")
        #                         else:
        #                             setattr(self, attribute, results[0].name)
        #                     else:
        #                         setattr(self, attribute, field["value"])
        #     self.parent.debug(end="convert_to_attributes")


        # def tag_conversion(self):
        #     self.parent.debug(start="tag conversion")
        #     # Cycle Through Tags on Ticket
        #     for tag in self.ticket.tags:
        #         # Create Column Value with Tag for Text Value
        #         col_val = create_column_value(id="text", column_type=ColumnType.text, value=tag)
        #         results = self.parent.boards["zendesk_tags"].get_items_by_column_values(col_val)
        #         if len(results) > 1:
        #             self.parent.debug("Multiple Tags Found - Ending Early")
        #             continue
        #         elif len(results) == 0:
        #             self.parent.debug("No Tags Found - Ending Early")
        #             continue
        #         else:
        #             for result in results:
        #                 self.parent.debug("Found Tag: {}".format(tag))
        #                 attribute = result.get_column_value(id="text9").text
        #                 value = result.name
        #                 value_type = result.get_column_value(id="status7").index
        #                 # Status type value
        #                 if value_type == 15:
        #                     setattr(self, attribute, value)
        #                 # Dropdown type value
        #                 elif value_type == 4:
        #                     getattr(self, attribute).append([value, result.get_column_value(id="text3").text])
        #                 else:
        #                     self.parent.debug("'type' Status Column index not matched")
        #     self.parent.debug(start="tag conversion")


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
                    "repair_type"
                ]

                for attribute in attributes:
                    value = getattr(self, attribute, None)
                    if value:
                        setattr(self.parent.monday, attribute, value)
                self.parent.monday.z_ticket_id = self.ticket_id
                if self.ticket.organization:
                    self.parent.monday.name += " ({})".format(self.ticket.organization.name)
                for notification in self.notifications:
                    self.parent.monday.notifications.append(int(notification[1]))
            self.parent.debug(end="convert_to_monday")


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
                "zendesk_url": "text410", # Zenlink Column
                "email": "text5", # Email Column
                "number": "text00", # Tel. No. Column
                "z_ticket_id": "text6", # Zendesk ID Column
                "v_id": "text6", # Vend Sale ID Column
                "address1": "passcode", # Street Address Column
                "address2": "dup__of_passcode", # Company/Flat Column
                "postcode": "text93", # Postcode Column
                "passcode": "text8", # Passcode Column
                "imei_sn": "text4" # IMEI Column
            },

            "structure": lambda id, value: [id, value]
        },

        "dropdown": {
            "values": {
                "device": "device0", # Device Column
                "repairs": "repair", # Repairs Column
                "screen_condition": "screen_condition",
                "notifications": "dropdown8" # Screen Condition Column
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
                diction = structure(values[column], getattr(monday_object, column))
                self.column_values[diction[0]] = diction[1]

