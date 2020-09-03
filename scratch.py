import requests
import json
import os

import settings



query = """query {
  items (ids: 703224936) {
    column_values {
      title
      value
    }
  }
}"""

query2 = """:query {
  item
}"""

json = {'query': query}

headers = {
  "Authorization":os.environ["MONV2SYS"]
}

url="https://api.monday.com/v2"

print(json)

response = requests.post(url=url, headers=headers, json=json)

print(response.status_code)
print(response.text)