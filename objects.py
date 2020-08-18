import json
import requests
import os

import settings
import keys.vend
import keys.monday

from moncli import MondayClient


# Differentiation between 'INITIALISATION' and 'INCLUSION'


class Repair():
    
    debug_string = []
    pulses = []
    vend = None
    monday = None
    zendesk = None    
    
    def __init__(self, vend=False, monday=False, zendesk=False, test=False):
        
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
            
            # Set self.monday, if another is addded, set to None or = self.pulses
            
            self.include_monday(monday)
            self.source = "monday"
        
        elif zendesk:
            self.source = "zendesk"
            self.include_zendesk(zendesk)
            
        elif test:
            self.name = "Jeremiah Bullfrog"

    def include_vend(self, vend_sale_id):

        self.debug("Adding[VEND] ID: {}".format(vend_sale_id))
        self.vend = VendRepair(vend_sale_id)

    def include_monday(self, monday_id):

        self.debug("Adding[MONDAY] ID: {}".format(monday_id))
        
        if isinstance(self.monday, list):
            self.monday.append(MondayRepair(monday_id))
        elif self.monday:
            self.monday = [self.monday, MondayRepair(monday_id)]
        elif not self.monday:
            self.monday = MondayRepair(monday_id)
        

    def include_zendesk(self, zendesk_ticket_id):
        
        self.debug("Adding[ZENDESK] ID: {}".format(zendesk_ticket_id))
        self.zendesk = ZendeskRepair(zendesk_ticket_id)
        
    def debug(self, message, line=True, func_s=False, func_e=False):
        
        if line:
            self.debug_string.append(message)
        elif func_s:
            self.debug_string.append("$$$$  " + message + "  $$$$")            
        elif func_e:
            self.debug_string.append("//$$  " + message + "  $$\\\\")
        
    def debug_print(self):
        
        print("\n".join(self.debug_string))
        
class VendRepair(Repair):
    
    def __init__(self, vend_sale_id):
        
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
        
        self.phone = self.customer_info["phone"]
        self.mobile = self.customer_info["mobile"]
        self.fax = self.customer_info["fax"]
        self.email = self.customer_info["email"]
        
        self.client = "End User"
        self.service = "Walk-In"
        self.type = "Repair"
        
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
                self.type = "Diagnostic"
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
                      
class MondayRepair(Repair):
         
    moncli = MondayClient(user_name='systems@icorrect.co.uk',
                                   api_key_v1=os.environ["MONV1SYS"],
                                   api_key_v2=os.environ["MONV2SYS"])
    
    def __init__(self, monday_id):
        
        for item in self.moncli.get_items(limit=1, ids=[monday_id]):
            self.item = item
            break
            
        self.name = self.item.name.split()[0] + " " + self.item.name.split()[1]
        
        self.retreive_column_data()
        
        self.translate_column_data()
        
                

    def translate_column_data(self):

        self.debug("MONDAY translate_column_data", func_s=True)

        attributes = [["Status", "m_status", "status"], ["Service", "m_service", "service"],
                    ["Client", "m_client", "client"], ["Type", "m_type", "type"],
                    ["End Of Day", "m_eod", "eod"], ["ZenLink", "m_zenlink", "zenlink"],
                    ["Has Case", "m_has_case", "has_case"]]
        
        for column, m_attribute, attribute in attributes:

            # Check in status column dictionary for the corresponding column
            for option in keys.monday.status_column_dictionary[column]["values"]:
                
                # Take title from column dictionary and add it to the Repair object
                if option["index"] == getattr(self, m_attribute):
                    setattr(self, attribute, option["title"])
                    
        self.debug("MONDAY translate_column_data", func_e=True)

                       
    def retreive_column_data(self):
        
    
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
                                
class ZendeskRepair(Repair):
    
    def __init__(self, zendesk_ticket_number):
        
        self.ticket_id = zendesk_ticket_number
        
class MonBoards():
        
    def __init__(self):        
        
        self.boards = {}
        
    # def add_board(self, username, board):
        
        
    #     self.boards[user_ids[usern]


class PulseToAdd():
    
    title_to_id = {
        'invoiced': 'check',
        'link_to_ticket': 'text410',
        'zenlink': 'status5',
        'status': 'status4',
        'service': 'service',
        'client': 'status',
        'type': 'status24',
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
        self.type = None
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

# COMPARISONS & CORRECTIONS
# comps = []
# for item in [self.vend, self.monday, self.zendesk]:
#   if item:
#       comps.append(item)
#
# Compare this list


# WALK IN CORPORATES
# If user on zendesk and user has company - corporate