columns = [
          {
            "title": "Name",
            "id": "name"
          },
          {
            "title": "Invoiced?",
            "id": "check"
          },
          {
            "title": "Link to Ticket",
            "id": "text410"
          },
          {
            "title": "ZenLink",
            "id": "status5"
          },
          {
            "title": "Status",
            "id": "status4"
          },
          {
            "title": "Service",
            "id": "service"
          },
          {
            "title": "Client",
            "id": "status"
          },
          {
            "title": "Type",
            "id": "status24"
          },
          {
            "title": "Case?",
            "id": "status_14"
          },
          {
            "title": "Booking Time",
            "id": "date6"
          },
          {
            "title": "Technician",
            "id": "person"
          },
          {
            "title": "Device",
            "id": "device0"
          },
          {
            "title": "Repair",
            "id": "repair"
          },
          {
            "title": "Part Colour",
            "id": "status8"
          },
          {
            "title": "Screen Condition",
            "id": "screen_condition"
          },
          {
            "title": "IMEI/SN",
            "id": "text4"
          },
          {
            "title": "Data",
            "id": "status55"
          },
          {
            "title": "Passcode",
            "id": "text8"
          },
          {
            "title": "DCPS",
            "id": "text2"
          },
          {
            "title": "Post Code",
            "id": "text93"
          },
          {
            "title": "Company/Flat",
            "id": "dup__of_passcode"
          },
          {
            "title": "Street Name/Number",
            "id": "passcode"
          },
          {
            "title": "Date Received",
            "id": "date4"
          },
          {
            "title": "Tel.No",
            "id": "text00"
          },
          {
            "title": "Email",
            "id": "text5"
          },
          {
            "title": "ETA",
            "id": "hour0"
          },
          {
            "title": "Repaired Date",
            "id": "collection_date"
          },
          {
            "title": "Collection Date",
            "id": "date3"
          },
          {
            "title": "Notifications",
            "id": "dropdown4"
          },
          {
            "title": "Total Time",
            "id": "time_tracking98"
          },
          {
            "title": "Diagnostic Time",
            "id": "time_tracking"
          },
          {
            "title": "Repair Time",
            "id": "time_tracking9"
          },
          {
            "title": "Item ID",
            "id": "item_id"
          },
          {
            "title": "ZenDeskID",
            "id": "text6"
          },
          {
            "title": "Chased",
            "id": "status_1"
          },
          {
            "title": "Vend Sale ID",
            "id": "text88"
          },
          {
            "title": "End Of Day",
            "id": "blocker"
          },
          {
            "title": "Deactivate",
            "id": "check71"
          }
        ]

for item in columns:
    print("'{}': '{}'".format(item["title"].lower().replace(" ", "_"), item["id"]))