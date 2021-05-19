import os

from moncli import MondayClient, NotificationTargetType, ColumnType, create_column_value

import settings


class Manager():

    monday_clients = {

        "system": [
            MondayClient(
                user_name='systems@icorrect.co.uk',
                api_key_v1=os.environ["MONV1SYS"],
                api_key_v2=os.environ["MONV2SYS"]
                ),
            12304876],

        "error": [
            MondayClient(
                user_name='admin@icorrect.co.uk',
                api_key_v1=os.environ["MONV1ERR"],
                api_key_v2=os.environ["MONV2ERR"]
                ),
            15365289
        ],

        "email": [
            MondayClient(
                user_name='icorrectltd@gmail.com',
                api_key_v1=os.environ["MONV1EML"],
                api_key_v2=os.environ["MONV2EML"]
                ),
            11581083
        ]
    }

    def __init__(self):
        pass

    def add_update(self, monday_id, user, update=False, status=False, notify=False, non_main=False, checkbox=False):
        # Select Client (Which User Will be posting updates/notificaitons)
        """Adds updates or notifies monday users, with options to adjust statuses

        Args:
            monday_id (int): ID of the Monday ite mthat the update will be centered around
            user (str): Name of the user and client to be used to post the update/notification
            update (bool, optional): Provide the text of the update required. Defaults to False.
            status (list[2], optional): List containing the ID of the status column to be changed and the label to be changed to. Defaults to False.
            notify (list[2], optional): Contains text for the notification to be sent and the ID of the user to send it to. Defaults to False.
            non_main (bool, optional): [description]. Defaults to False.

        Returns:
            False: No item could be found for the provided ID
        """
        client = self.monday_clients[user][0]
        user_id = self.monday_clients[user][1]
        # Get Item
        item = None
        for pulse in client.get_items(ids=[monday_id], limit=1):
            item = pulse
            break
        # Check Item Can Be Found
        if not item:
            return False
        # Post Update, if provided
        if update:
            item.add_update(body=update)
        # Change Status, if provided
        if status:
            # Ensure 'status' is a 2 length list
            if len(status) == 2:
                item.change_column_value(column_id=status[0], column_value={"label": status[1]})
            else:
                print("status list has not been provided correctly")
        # Send Notification, if requested
        if notify:
            # Check 'notify' is a 2 length list
            if len(notify) == 2:
                client.create_notification(text=notify[0], user_id=notify[1], target_id=monday_id, target_type=NotificationTargetType.Project)
            else:
                print("notify list has not been provided correctly")
                
        # Check checkbox value if needed
        if checkbox:
            
            if len(checkbox) == 2:
                            
                for pulse in self.monday_clients['system'][0].get_items(ids=[monday_id], limit=1):
                    if checkbox[1]:
                        values = {'check3': {'checked': 'true'}}
                    elif not checkbox[1]:
                        values = {"check3": None}
                    item.change_multiple_column_values(values)
                    break
                
                
                
                
            


manager = Manager()
