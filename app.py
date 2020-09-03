from threading import Thread

from flask import Flask

from objects import Repair

# APP SET UP
app = Flask(__name__)

# APP FUNCTIONS
def monday_handshake(webhook):
    """Takes webhook information, authenticates if required, and decodes information

    Args:
        webhook (request): Payload received from Monday's Webhooks

    Returns:
        dictionary: contains various information from Monday, dependent on type of webhook sent
    """
    data = webhook.decode('utf-8')
    data = json.loads(data)

    if "challenge" in data.keys():
        authtoken = {"challenge": data["challenge"]}
        return authtoken
    else:
        return data


# ROUTES // MONDAY
# Status Change
@app.route("/monday/status")
def monday_status_change():
    webhook = request.get_data()
    data = monday_handshake(webhook)
    repair = Repair(monday=int(data["event"]["pulseId"]))
    repair.debug("Status Change: {} ==> {}".format(data["event"]["previousValue"]["label"]["text"], data["event"]["value"]["label"]["text"]))




# ROUTES // VEND
# Sale Update
@app.route("/vend/sale_update")
def vend_sale_update():

    def process(sale):

        sale = sale.decode('utf-8')
        sale = parse_qs(sale)
        sale = json.loads(sale['payload'][0])

    thread = Thread(target=process, kwargs={"sale": request.get_data()})
    thread.start()
    return ""


# Top Line Driver Code
if __name__ == "__main__":
    icv3.run(load_dotenv=True)
