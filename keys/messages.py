messages = {
    # "Corporate Courier Returned": """Hi {},\n\nThank you for arranging a repair with iCorrect today.\n\nWe can confirm the device has been successfully re-delivered to it's collection point.\n\nPlease do get in touch if you experience any difficulty locating the package.\n\nKind Regards,\n\nThe iCorrect Team\n+442070998517""",

    # "Corporate Walk-In Repaired": """Hi {},\n\nThank you for bringing a device into iCorrect for repair.\n\nWe can confirm the repairs have been successfully completed and your device is available for collection at your convenience.\n\nWe shall look forward to seeing you./nKind Regards,\n\nThe iCorrect Team\n+442070998517""",

    "End User Courier Returned": """Hi {},\n\nThank you for arranging to have your device repaired with iCorrect.\n\nWe can confirm your device has been successfully re-delivered to it's collection point.\n\nPlease do get in touch if you experience any difficulty locating the package.\n\nKind Regards,\n\nThe iCorrect Team\n+442070998517""",

    "End User Walk-In Repaired": """Hi {},\n\nThank you for bringing your device into iCorrect for repair.\n\nWe can confirm the repairs have been successfully completed and your device is available for collection at your convenience - we are open between 9am and 6pm Monday to Friday, and 11am to 4pm on Saturdays.\n\nWe shall look forward to seeing you.\n\nKind Regards,\n\nThe iCorrect Team\n+442070998517""",

    "End User Walk-In Booking Confirmed": """Hi {},\n\nThank you for booking in to have your device repaired with iCorrect.\n\nShould you experience any isssues in making your appointment, or struggle to find our offices, please don't hesitate to get in contact.\n\nWe shall look forward to seeing you.\n\nKind Regards,\n\nThe iCorrect Team\n+442070998517""",

    "End User Walk-In Diagnostic Booking Confirmed": """Hi {},\n\nThank you for booking in to have your device repaired with iCorrect.\n\nShould you experience any isssues in making your appointment, or struggle to find our offices, please don't hesitate to get in contact.\n\nWe shall look forward to seeing you.\n\nKind Regards,\n\nThe iCorrect Team\n+442070998517""",

    "End User Walk-In Diagnostic Received": """Hi {},\n\nThank you for dropping your device off with iCorrect.\n\nWe will aim to get back with you within 24-48 hours, but if you would like an update sooner, please reply to this text with 'Update'.\n\nKind regards,\n\nThe iCorrect Team\n02070998517"""
    }



message_dictionary = {

    "Booking Confirmed": {

        "Walk-In": {

            "Repair": {
                "End User": messages["End User Walk-In Booking Confirmed"],
                "Corporate": False,
                "Warranty": messages["End User Walk-In Booking Confirmed"]
            },

            "Diagnostic": {
                "End User": messages["End User Walk-In Booking Confirmed"],
                "Corporate": False,
                "Warranty": messages["End User Walk-In Booking Confirmed"]
            }
        },
        "Courier": {

            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            },
            "Diagnostic": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        }
    },

    
    "Courier Booked": {

        "Mail-In": {

            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            },

            "Diagnostic": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        },
        
        "Courier": {

            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            },
            "Diagnostic": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        }

    },

    "Received": {
        "Courier": {
            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            },
            "Diagnostic": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        },
        "Mail-In": {
            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            },
            "Diagnostic": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        },
        "Walk-In": {
            "Diagnostic": {
                "End User": messages["End User Walk-In Diagnostic Received"],
                "Warranty": messages["End User Walk-In Diagnostic Received"]
            }
        }
    },

    "Repaired": {
        "Courier": {
            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            },
            "Diagnostic": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        }, 
        "Mail-In": {
            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        },
        "Walk-In": {
            "Repair": {
                "End User": messages["End User Walk-In Repaired"],
                "Corporate": False,
                "Warranty": messages["End User Walk-In Repaired"]
            },
            
            "Diagnostic": {
                "End User": messages["End User Walk-In Repaired"],
                "Corporate": False,
                "Warranty": messages["End User Walk-In Repaired"]
            }
        }
    },

    "Return Booked": {
        "Courier": {
            "Repair": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            },
            "Diagnostic": {
                "End User": False,
                "Corporate": False,
                "Warranty": False
            }
        }
    }
}



