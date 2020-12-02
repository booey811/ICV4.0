import json
from pprint import pprint as p
import os
import requests

import settings

class StuartSandBox():

    def __init__(self):
        pass

    def authenticate(self, production=False):

        payload = {
            "scope": "api",
            "grant_type": "client_credentials",
            "client_id": os.environ["STUARTIDSAND"]
            "client_secret": os.environ["STUARTSECRETSAND"]
        }

        if production:
            url = "https://api.stuart.com/v2/ouath/token"
            payload["client_id"] = os.environ["STUARTID"]
            payload["client_secret"] = os.environ["STUARTSECRET"]
        else:
            url = "https://sandbox-api.stuart.com/v2/oauth/token"

        payload = json.dumps(payload)

        headers = {'content-type': "application/json"}

        response = requests.request('POST', url, data=payload, headers=headers)

        print(response)

        info = json.loads(response.text)

        print(info)

        print(info["access_token"])


    def validate_address(self, address_string, direction, production=False):

        if production:
            url = "https://api.stuart.com/v2/addresses/validate"
        else:
            url = "https://sandbox-api.stuart.com/v2/addresses/validate"

        payload = {
            "address": address_string,
            "type": direction
        }

        payload = json.dumps(payload)

        headers = {
            'content-type': "application/json",
            'authorization': "Bearer {}".format(os.environ["STUARTTOKENSAND"])
            }

        response = requests.request("GET", url, data=payload, headers=headers)


        p(response)
        print()
        print("=====================")
        print()
        job_info = json.loads(response.text)
        p(job_info)


    def format_details(self, client_details, monday_object):
        """Takes delivery details (client address, phone, email, direction) and creates the structure required for the create_job function

        Args:
            client_details (dict): Dictionary for client details
            monday_object (MondayRepair): Monday Object (For Status and ID Info)

        Returns:
            dict: Data structure for create_job func
        """

        icorrect = {
            'address': 'iCorrect 12 Margaret Street W1W 8JQ',
            'email': 'support@icorrect.co.uk',
            'phone': '02070998517'
        }

        if monday_object.status == "Book Return Courier":
            collect = icorrect
            deliver = client_details
            assignment_code = "RETURN: {}".format(monday_object.id)
            direction = "delivering"
        else:
            collect = client_details
            deliver = icorrect
            assignment_code = "COLLECTION: {}".format(monday_object.id)
            direction = 'picking'

        self.validate_address(client_details["address"], direction)

        return

        p(collect)
        p(deliver)


        # Map to Result

        result = {
            "job": {
                "assignment_code": "{}".format(assignment_code),
                "pickups": [{
                    "address": "{}".format(collect["address"]),
                    # "comment": "{}",
                    "contact": {
                        "firstname": "{}".format(collect["firstname"]),
                        "lastname": "{}",
                        "phone": "{}",
                        "email": "{}",
                        "company": "{}"
                    }
                }],
                "dropoffs": [{
                    "package_type": "small",
                    # "package_description": "The blue one.",
                    "client_reference": "{}", # Must Be Unique
                    "address": "{}",
                    # "comment": "2nd floor on the left",
                    "contact": {
                        "firstname": "{}",
                        "lastname": "{}",
                        "phone": "{}",
                        "email": "{}",
                        "company": "{}"
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

        if production:
            url = "https://api.stuart.com/v2/jobs"
        else:
            url = "https://sandbox-api.stuart.com/v2/jobs"

        payload = json.dumps(payload)

        headers = {
            'content-type': "application/json",
            'authorization': "Bearer {}".format(os.environ["STUARTTOKENSAND"])
            }

        response = requests.request("POST", url, data=payload, headers=headers)


        p(response)
        print()
        print("=====================")
        print()
        job_info = json.loads(response.text)
        p(job_info)

        return


