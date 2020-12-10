import pycurl
from urllib.parse import urlencode
import io
import os
from pprint import pprint

import settings

data = {
    'Apikey': os.environ['PHONECHECK'],
    'Username': 'icorrect1',
    'IMEI': '357281098586196'
}

def test_request(dictionary_of_post_data):

    form = urlencode(dictionary_of_post_data)

    bytes_obj = io.BytesIO()
    crl = pycurl.Curl()

    crl.setopt(crl.URL, 'https://clientapiv2.phonecheck.com/cloud/cloudDB/GetDeviceInfo')

    crl.setopt(crl.WRITEDATA, bytes_obj)

    crl.setopt(crl.POSTFIELDS, form)

    crl.perform()

    crl.close()

    response = bytes_obj.getvalue()

    info = response.decode('utf8')

    pprint(info)

test_request(data)