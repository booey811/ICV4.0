import json
from pprint import pprint as p
import os
import requests

import settings

class StuartSandBox():

    def __init__(self):
        pass

    def format_details(self, client_details, monday_status):
        """Takes delivery details (client address, phone, email, direction) and creates the structure required for the create_job function

        Args:
            client_details (dict): Dictionary for client details
            monday_status (string): Status of Courier Job (Collecting or Returning)

        Returns:
            dict: Data structure for create_job func
        """

        icorrect = "" # WIll be icorrects address details for use in below !!! SAME FORMAT AS ARGUMENT FOR THIS FUNCTION

        if monday_status == "Book Return Courier":
            collect = icorrect
            deliver = client_details
            assignment_code = "RETURN: {}".format(self.id)
        else:
            collect = client_details
            deliver = icorrect
            assignment_code = "COLLECTION: {}".format(self.id)

        # Map to Result

        result = {
            "job": {
                "assignment_code": " {}}",
                "pickups": [{
                    "address": "{}", 
                    "comment": "{}",
                    "contact": {
                        "firstname": "Client",
                        "lastname": "Sucker",
                        "phone": "+447984305338",
                        "email": "gabriel@icorrect.co.uk",
                        "company": "iCorrect"
                    }
                }],
                "dropoffs": [{
                    "package_type": "small",
                    # "package_description": "The blue one.",
                    "client_reference": "Ref TEST 1", # Must Be Unique
                    "address": "30 Warwick Street W1B 5NH",
                    # "comment": "2nd floor on the left",
                    "contact": {
                        "firstname": "Dany",
                        "lastname": "Dan",
                        "phone": "+33611112222",
                        "email": "client1@email.com",
                        "company": "Sample Company Inc."
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


    def create_job(self):
        pass



ls = ""

print(ls.strip())