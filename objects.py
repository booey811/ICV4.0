import json
import os
import requests
from datetime import datetime, timedelta

from moncli import MondayClient, create_column_value, ColumnType
from zenpy import Zenpy
from zenpy.lib import exception as zenpyExceptions

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
    logging_board = monday_client.get_board_by_id(id=736027251)

    def __init__(self, vend=False, monday=False, zendesk=False, test=False):

        self.debug_string = []
        self.vend = None
        self.monday = []
        self.zendesk = None

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
            self.name = self.monday[0].name
            self.email = self.monday[0].email
            self.number = self.monday[0].phone

        elif zendesk:
            self.source = "zendesk"
            self.include_zendesk(zendesk)

        elif test:
            self.name = "Jeremiah Bullfrog"

        self.query_applications()

    def include_vend(self, vend_sale_id):

        self.debug("Adding[VEND] ID: {}".format(vend_sale_id))
        self.vend = Repair.VendRepair(self, vend_sale_id)

    def include_monday(self, monday_id):

        self.debug("Adding[MONDAY] ID: {}".format(monday_id))
        self.monday.append(Repair.MondayRepair(self, monday_id=monday_id))

    def include_zendesk(self, zendesk_ticket_id):

        self.debug("Adding[ZENDESK] ID: {}".format(zendesk_ticket_id))
        self.zendesk = Repair.ZendeskRepair(self, zendesk_ticket_id)

    def query_applications(self):

        """Searches the specified applications for information related to the current repair"""

        self.debug(start="query_applications")

        if self.source == 'monday':
            if self.monday[0].v_id:
                self.include_vend(self.monday[0].v_id)

            for pulse in self.monday:
                if pulse.z_ticket_id:
                    self.include_zendesk(pulse.z_ticket_id)

        elif self.source == 'vend':
            col_val = create_column_value(id='text88', column_type=ColumnType.text, value=str(self.vend.id))
            for item in self.monday_client.get_board(id="349212843").get_items_by_column_values(col_val):
                self.include_monday(item.id)

            for pulse in self.monday:
                if pulse.z_ticket_id:
                    self.include_zendesk(pulse.z_ticket_id)
                    break

        elif self.source == 'zendesk':
            col_val = create_column_value(id='text6', column_type=ColumnType.text, value=str(self.zendesk.ticket_id))
            for item in self.monday_client.get_board(id="349212843").get_items_by_column_values(col_val):
                self.include_monday(item.id)

            for pulse in self.monday:
                if pulse.v_id:
                    self.include_vend(pulse.v_id)
                    break

        else:
            self.debug("Source of Repair not set")

        self.debug(end="query_applications")

    def add_to_monday(self):

        self.debug("add_to_monday", start=True)

        main_board = self.monday_client.get_board_by_id(id=349212843)

        for pulse in self.monday:

            pulse.columns = MondayColumns(pulse)

            main_board.add_item(item_name=self.name, column_values=pulse.columns.column_values )

        self.debug("add_to_monday", end=True)

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
            for pulse in  self.monday:
                col_vals["text"] = str(pulse.id)
            if self.vend:
                col_vals["text3"] = str(self.vend.id)
            if self.zendesk:
                col_vals["text1"] = str(self.zendesk.ticket_id)
            time = str(now.strftime("%X"))
            log = self.logging_board.add_item(item_name=time + " // " + str(self.name) + " -- FROM APPV4", column_values=col_vals)
            log.add_update("\n".join(self.debug_string))
        else:
            print("\n".join(self.debug_string))

    class VendRepair():

        def __init__(self, repair_object, vend_sale_id):

            self.parent = repair_object

            self.id = vend_sale_id
            self.sale_info = self.query_for_sale()
            self.customer_id = str(self.sale_info["customer_id"])
            self.customer_info = self.query_for_customer()

            self.passcode = None
            self.imeisn = None

            self.pre_checks = []
            self.post_checks = []
            self.products = []
            self.notes = []

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
                        self.imeisn = product["note"].split(":")[1].strip()


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

            self.parent.monday.append(monday_object)

            # setattr(super(), 'monday', monday_object)

    class MondayRepair():

        def __init__(self, repair_object, monday_id=False, created=False):

            self.parent = repair_object

            self.initialise_attributes()

            if monday_id:

                for item in self.parent.monday_client.get_items(limit=1, ids=[int(monday_id)]):
                    self.item = item
                    self.id = item.id
                    break

                self.name = str(self.item.name.split()[0]) + " " + str(self.item.name.split()[1])

                self.retreive_column_data()

                self.translate_column_data()

            if created:

                self.name = created
                self.id = None

            # self.columns = MondayColumns(self)

        def initialise_attributes(self):

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
            self.booking_time = None # Not currently used in program
            self.deadline = None # Not currently used in program
            self.time = None # Not currently used in program
            self.technician = None # Not currently used in program
            self.device = []
            self.repairs = []
            self.colour = None
            self.screen_condition = None # Not currently used in program
            self.imeisn = None
            self.data = None
            self.passcode = None
            self.postcode = None
            self.address_2 = None
            self.address_1 = None
            self.date_received = None
            self.number = None
            self.email = None
            self.eta = None # Not currently used in program
            self.date_repaired = None # Not currently used in program
            self.date_collected = None # Not currently used in program
            self.end_of_day = None
            self.deactivated = None

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
                ["Has Case", "m_has_case", "case"]
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
                ["Repairs", "m_repairs", "repairs"]
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

    class ZendeskRepair():

        def __init__(self, repair_object, zendesk_ticket_number):

            self.parent = repair_object

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
            else:
                self.debug("Unable to find Zendesk ticket: {}".format(self.ticket_id))

class PulseToAdd():

    title_to_id = {
        'invoiced': 'check',
        'link_to_ticket': 'text410',
        'zenlink': 'status5',
        'status': 'status4',
        'service': 'service',
        'client': 'status',
        'repair_type': 'status24',
        'case': 'status_14',
        'booking_time': 'date6',
        'technician': 'person',
        'device': 'device0',
        'repair': 'repair',
        'part_colour': 'status8',
        'screen_condition': 'screen_condition',
        'imei_sn': 'text4',
        'data': 'status55',
        'passcode': 'text8',
        'dcps': 'text2',
        'post_code': 'text93',
        'company_flat': 'dup__of_passcode',
        'street_name_number': 'passcode',
        'date_received': 'date4',
        'number': 'text00',
        'email': 'text5',
        'eta': 'hour0',
        'repaired_date': 'collection_date',
        'collection_date': 'date3',
        'notifications': 'dropdown4',
        'total_time': 'time_tracking98',
        'diagnostic_time': 'time_tracking',
        'repair_time': 'time_tracking9',
        'item_id': 'item_id',
        'zendeskid': 'text6',
        'chased': 'status_1',
        'vend_sale_id': 'text88',
        'end_of_day': 'blocker',
        'deactivate': 'check71'
    }



    def __init__(self):

        self.name = None

        self.invoiced = None
        self.link_to_ticket = None
        self.zenlink = None
        self.status = None
        self.service = None
        self.client = None
        self.repair_type = None
        self.case = None
        self.booking_time = None
        self.technician = None
        self.device = None
        self.repair = None
        self.part_colour = None
        self.screen_condition = None
        self.imei_sn = None
        self.data = None
        self.passcode = None
        self.dcps = None
        self.post_code = None
        self.company_flat = None
        self.street_name_number = None
        self.date_received = None
        self.number = None
        self.email = None
        self.eta = None
        self.repaired_date = None
        self.collection_date = None
        self.notifications = None
        self.total_time = None
        self.diagnostic_time = None
        self.repair_time = None
        self.item_id = None
        self.zendeskid = None
        self.chased = None
        self.vend_sale_id = None
        self.end_of_day = None
        self.deactivate = None

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
                "end_of_day": "blocker" # End Of Day Column
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
            },

            "structure": lambda id, value: [id, value]
        },

        "dropdown": {
            "values": {
                "device": "device0", # Device Column
                "repairs": "repair", # Repairs Column
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

            print(self.column_values)
