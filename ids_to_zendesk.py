import requests
import json
import os

import settings

url = "https://icorrect.vendhq.com/api/2.0/customers"

headers = {'authorization': os.environ["VEND"]}

response = requests.request("GET", url, headers=headers)

results = json.loads(response.text)

print(len(results["data"]))

for customer in results["data"]:
    print(customer["email"])