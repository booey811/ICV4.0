import requests
import json

url = "https://icorrect.vendhq.com/api/2.0/customers"

headers = {'authorization': 'Bearer 5Ladw3FITzySnwpPrgaiq_vMDjr0Rx6I5nqxOiT3'}

response = requests.request("GET", url, headers=headers)

results = json.loads(response.text)

print(len(results["data"]))

for customer in results["data"]:
    print(customer["email"])