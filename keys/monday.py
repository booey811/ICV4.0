user_ids = {
        "systems": 12304876, "errors": 15365289, "emails": 11581083
}

col_ids_to_attributes = {
    'check': {'title': 'Invoiced?', 'value_type': ['checked'], 'attribute': "invoiced"},
    'text410': {'title': 'Link to Ticket', 'value_type': ['text'], 'attribute': "zendesk_url"},
    'status5': {'title': 'ZenLink', 'value_type': ["index", "label"], 'attribute': "m_zenlink"},
    'status4': {'title': 'Status', 'value_type': ["index", "label"], 'attribute': "m_status"},
    'service': {'title': 'Service', 'value_type': ["index", "label"], 'attribute': "m_service"},
    'status': {'title': 'Client', 'value_type': ["index", "label"], 'attribute': "m_client"},
    'status24': {'title': 'Type', 'value_type': ["index", "label"], 'attribute': "m_type"},
    'person': {'title': 'Technician', 'value_type': 'persons_and_teams', 'attribute': None},
    'device0': {'title': 'Device', 'value_type': ["ids", "label"], 'attribute': 'm_device'},
    'repair': {'title': 'Repair', 'value_type': ["ids", "label"], 'attribute': 'm_repairs'},
    'screen_condition': {'title': 'Screen Condition', 'value_type': ["ids", "label"], 'attribute': "m_screen_condition"},
    'status8': {'title': 'Colour', 'value_type': ["index", "label"], 'attribute': 'm_colour'},
    'text4': {'title': 'IMEI/SN', 'value_type': ['text'], 'attribute': 'imei_sn'},
    'status_15': {'title': 'Refurb Type', 'value_type': ['index', 'label'], 'attribute': 'm_refurb'},
    'status55': {'title': 'Data', 'value_type': ["index", "label"], 'attribute': "m_data"},
    'text8': {'title': 'Passcode', 'value_type': ['text'], 'attribute': 'passcode'},
    'text2': {'title': 'DCPS', 'value_type': ['text'], 'attribute': None},
    'text93': {'title': 'Post Code', 'value_type': ['text'], 'attribute': 'postcode'},
    'date4': {'title': 'Date Received', 'value_type': ['date', 'time'], 'attribute': "date_received"},
    'text00': {'title': 'Tel.No', 'value_type': ['text'], 'attribute': 'phone'},
    'text5': {'title': 'Email', 'value_type': ['text'], 'attribute': 'email'},
    'repair_complete': {'title': 'Repaired Date', 'value_type': ['date', 'time'], 'attribute': "date_repaired"},
    'date3': {'title': 'Collection Date', 'value_type': ['date', 'time'], 'attribute': "date_collected"},
    'dropdown4': {'title': 'Notifications', 'value_type': ['ids', 'label'], 'attribute': "m_notifications"},
    'time_tracking98': {'title': 'Total Time', 'value_type': None, 'attribute': None},
    'time_tracking': {'title': 'Diagnostic Time', 'value_type': None, 'attribute': None},
    'time_tracking9': {'title': 'Repair Time', 'value_type': None, 'attribute': None},
    'item_id': {'title': 'Item ID', 'value_type': None, 'attribute': None},
    'text6': {'title': 'ZenDeskID', 'value_type': ['text'], 'attribute': 'z_ticket_id'},
    'text88': {'title': 'Vend Sale ID', 'value_type': ['text'], 'attribute': 'v_id'},
    'blocker': {'title': 'End Of Day', 'value_type': ["index", "label"], 'attribute': "m_eod"},
    "passcode": {"title": "Street Name/Number", 'value_type': ["text"], "attribute": "address1"},
    "dup__of_passcode": {"title": "Company/Flat", 'value_type': ["text"], "attribute": "address2"},
    "check71": {"title": "Deactivate", "value_type": ["checked"], "attribute": "deactivate"},
    "date6": {"title": "Booking Time ", "value_type": ['date', 'time'], "attribute": "m_date"},
    "status_14": {"title": "Has Case", "value_type": ["index", "label"], "attribute": "m_has_case"},
    "dropdown8": {"title": "Notifications", "value_type": ["ids", "label"], "attribute": "m_notifications"}
}

status_column_dictionary = {
    "ZenLink": {
        "col_id": "status5",
        "values": [
            {"title": 'Not Active',
                'index': 5,
                'label': 'Not Active',
                'z_tag': 'not_active'
             },
            {"title": 'Create Connection',
                'index': 16,
                'label': 'Create Connection',
                'z_tag': 'create_connection'
             },
            {"title": 'Active',
                'index': 1,
                'label': 'Active',
                'z_tag': 'active'
             },
            {"title": 'Unable to Connect',
                'index': 19,
                'label': 'Unable to Connect',
                'z_tag': 'unable_to_connect'
             },
            {"title": "Error",
             "index": 2,
             "label": "Error",
             "z_tag": ""
             },
            {"title": "Severed",
             "index": 15,
             "label": "Severed",
             "z_tag": ""
            }
        ]
    },

    'Status': {
        'col_id': 'status4',
        'values': [
            {"title": "New Repair",
             'index': 5,
             "label": 'New Repair',
             'z_tag': "new_repair"
             },
            {"title": "Booking Confirmed",
             'index': 106,
             "label": 'Booking Confirmed',
             'z_tag': "booking_confirmed"
             },
            {"title": 'Awaiting Confirmation',
                'index': 0,
                'label': 'Awaiting Confirmation',
                'z_tag': 'awaiting_confirmation'
             },
            {"title": 'Book Courier',
                'index': 108,
                'label': 'Book Courier',
                'z_tag': 'book_courier'
             },
            {"title": 'Book Return Courier',
                'index': 103,
                'label': 'Book Return Courier',
                'z_tag': 'book_return_courier'
             },
            {"title": 'Courier Booked',
                'index': 3,
                'label': "Courier Booked",
                'z_tag': 'courier_booked'
             },
            {"title": 'Client Contacted',
                'index': 10,
                'label': 'Client Contacted',
                'z_tag': 'client_contacted'
             },
            {"title": 'Diagnostic Complete',
                'index': 2,
                'label': 'Diagnostic Complete',
                'z_tag': 'diagnostic_complete'
             },
            {"title": 'Diagnostics',
                'index': 13,
                'label': 'Diagnostics',
                'z_tag': 'diagnostics'
             },
            {"title": 'Invoiced',
                'index': 11,
                'label': 'Invoiced',
                'z_tag': 'invoiced'
             },
            {"title": 'New Repair',
                'index': 5,
                'label': 'New Repair',
                'z_tag': 'new_repair'
             },
            {"title": 'Paid',
                'index': 9,
                'label': 'Paid',
                'z_tag': 'paid'
             },
            {"title": 'Quote Accepted',
                'index': 4,
                'label': 'Quote Accepted',
                'z_tag': 'quote_accepted'
             },
            {"title": 'Quote Rejected',
                'index': 18,
                'label': 'Quote Rejected',
                'z_tag': 'quote_rejected'
             },
            {"title": 'Quote Sent',
                'index': 8,
                'label': 'Quote Sent',
                'z_tag': 'quote_sent'
             },
            {"title": 'Received',
                'index': 1,
                'label': 'Received',
                'z_tag': 'received'
             },
            {"title": 'Repair Paused',
                'index': 14,
                'label': 'Repair Paused',
                'z_tag': 'repair_paused'
             },
            {"title": 'Repaired',
                'index': 16,
                'label': 'Repaired',
                'z_tag': 'repaired'
             },
            {"title": 'Return Booked',
                'index': 19,
                'label': 'Return Booked',
                'z_tag': 'return_booked'
             },
            {"title": 'Returned',
                'index': 6,
                'label': 'Returned',
                'z_tag': 'returned'
             },
            {"title": 'Under Repair',
                'index': 12,
                'label': 'Under Repair',
                'z_tag': 'under_repair'
             },
            {"title": 'Unrepairable',
                'index': 17,
                'label': 'Unrepairable',
                'z_tag': 'unrepairable'
             },
            {"title": 'With Rico',
                'index': 7,
                'label': 'With Rico',
                'z_tag': 'with_rico'
             },
            {"title": "!! See Updates !!",
             "index": 101,
             "label": "!! See Updates !!",
             "z_tag": "___updates___"
             }
        ]
    },

    "Service": {
        "col_id": "service",
        "values": [
            {"title": "Walk-In",
                "index": 1,
                "label": "Walk-In",
                "z_tag": "walk-in"
             },
            {"title": "Courier",
                "index": 0,
                "label": "Courier",
                "z_tag": "courier"
             },
            {"title": "Mail-In",
                "index": 14,
                "label": "Mail-In",
                "z_tag": "walk-in"
             }
        ]
    },

    "Colour": {
        "col_id": "status8",
        "values": [
            {"title": "White",
                "index": 16,
                "label": "White",
                "z_tag": ""
            },
            {"title": "Black",
                "index": 10,
                "label": "Black",
                "z_tag": ""
            },
            {"title": "Coral",
                "index": 9,
                "label": "Coral",
                "z_tag": ""
            },
            {"title": "Blue",
                "index": 7,
                "label": "Blue",
                "z_tag": ""
            },
            {"title": "Red",
                "index": 2,
                "label": "Red",
                "z_tag": ""
            },
            {"title": "Space Grey",
                "index": 17,
                "label": "Space Grey",
                "z_tag": ""
            },
            {"title": "Silver",
                "index": 0,
                "label": "Silver",
                "z_tag": ""
            },
            {"title": "Yellow",
                "index": 8,
                "label": "Yellow",
                "z_tag": ""
            },
            {"title": "Rose Gold",
                "index": 101,
                "label": "Rose Gold",
                "z_tag": ""
            },
            {"title": "Champagne Gold",
                "index": 103,
                "label": "Champagne Gold",
                "z_tag": ""
            },
            {"title": "Gold",
                "index": 19,
                "label": "Gold",
                "z_tag": ""
            },
            {"title": "Green",
                "index": 6,
                "label": "Green",
                "z_tag": ""
            },
            {"title": "Purple",
                "index": 14,
                "label": "Purple",
                "z_tag": ""
            },
            {"title": "Midnight Green",
                "index": 5,
                "label": "Midnight Green",
                "z_tag": ""
            }
        ]
    },

    "Client": {
        "col_id": "status",
        "values": [
            {"title": "End User",
                "index": 16,
                "label": "End User",

                "z_tag": "enduser",
                "v_register": "02dcd191-aeab-11e8-ed44-5430fcb18594",
                "v_outlet": "02dcd191-aeab-11e8-ed44-53a67f2405f0"},
            {"title": "Corporate",
                "index": 0,
                "label": "Corporate",
                "z_tag": "corporate",
                "v_register": "02dcd191-aeab-11e8-ed44-54315eafa0b5",
                "v_outlet": "02dcd191-aeab-11e8-ed44-54314d2215be"},
            {"title": "Warranty",
             "index": 19,
             "label": "Warranty",
             "z_tag": "warranty",
            "v_register": "02dcd191-aeab-11e8-ed44-8c05daf03628",
            "v_outlet": "02dcd191-aeab-11e8-ed44-868426f262b9"}
        ]
    },

    "Type": {
        "col_id": "status24",
        "values": [
            {"title": "Repair",
                "index": 15,
                "label": "Repair",
                "z_tag": "repair"
             },
            {"title": "Diagnostic",
                "index": 2,
                "label": "Diagnostic",
                "z_tag": "diagnostic"
             },
            {"title": "Unrepairable",
                "index": 18,
                "label": "Unrepairable",
                "z_tag": "unrepairable"
             },
            {"title": "Quote Rejected",
                "index": 4,
                "label": "Quote Rejected",
                "z_tag": "quote_rejected"
             },
            {"title": "Lead",
                "index": 3,
                "label": "Lead",
                "z_tag": "lead"
             }
        ]
    },

    "End Of Day": {
        "col_id": "blocker",
        "values": [
            {"title": "Not Done",
                "index": 5,
                "label": "Not Done",
                "z_tag": ""},
            {"title": "Complete",
                "index": 109,
                "label": "Complete",
                "z_tag": ""},
            {"title": "Failed",
                "index": 2,
                "label": "Failed",
                "z_tag": ""}
        ]
    },

    "Has Case": {
        "col_id": "status_14",
        "values": [
            {"title": "HAS CASE",
                "index": 19,
                "label": "HAS CASE",
                "z_tag": ""},
            {"title": "Does Not",
                "index": 15,
                "label": "Does Not",
                "z_tag": ""}
        ]
    },

    "Refurb Type": {
        "col_id": "status_15",
        "values": [
            {"title": "Glass Only",
                "index": 1,
                "label": "Glass Only",
                "z_tag": ""},
            {"title": "Glass & Touch",
                "index": 8,
                "label": "Glass & Touch",
                "z_tag": ""},
            {"title": "Glass & Backlight",
                "index": 0,
                "label": "Glass & Backlight",
                "z_tag": ""},
            {"title": "Glass, Touch & Backlight",
                "index": 19,
                "label": "Glass, Touch & Backlight",
                "z_tag": ""},
            {"title": "China Screen",
                "index": 2,
                "label": "China Screen",
                "z_tag": ""}
        ]
    }
}