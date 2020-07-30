import requests
import json
import os

import settings
import keys.vend
import keys.monday

class VendRepair():
    
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
                      

class MondayRepair():
    
    def __init__(self, monday_id):
        
        self.id = monday_id
        
class ZendeskRepair():
    
    def __init__(self, zendesk_ticket_number):
        
        self.ticket_id = zendesk_ticket_number

class Repair():
    
    def __init__(self, vend=False, monday=False, zendesk=False):
        
        self.debug_string = []
        
        if vend:
            self.source = "vend"
            self.vend = VendRepair(vend)
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
            

        if monday:
            self.source = "monday"
            self.monday = MondayRepair(monday)
        
        if zendesk:
            self.source = "zendesk"
            self.zendesk = ZendeskRepair(zendesk)

    def include_vend(self, vend_sale_id):
        
        self.vend = VendRepair(vend_sale_id)            

    def include_monday(self, monday_id):
        
        self.monday = MondayRepair(monday_id)
        
    def include_zendesk(self, zendesk_ticket_id):
        
        self.zendesk = ZendeskRepair(zendesk_ticket_id)
        
    def debug(self, message):
        
        self.debug_string.append(message)
        
    def debug_print(self):
        
        print("\n".join(self.debug_string))
        
        



# COMPARISONS & CORRECTIONS
# comps = []
# for item in [self.vend, self.monday, self.zendesk]:
#   if item:
#       comps.append(item)
#
# Compare this list


# WALK IN CORPORATES
# If user on zendesk and user has company - corporate