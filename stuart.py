# PyCURL Tutorial




import pycurl
from io import BytesIO




def example1():


    # Simple Operation of sending a curl request and examining the response



    b_obj = BytesIO()
    crl = pycurl.Curl()

    # Set URL value
    crl.setopt(crl.URL, 'https://wiki.python.org/moin/BeginnersGuide')

    # Write bytes that are utf-8 encoded
    crl.setopt(crl.WRITEDATA, b_obj)

    # Perform a file transfer
    crl.perform()

    # End curl session
    crl.close()

    # Get the content stored in the BytesIO object (in byte characters)
    get_body = b_obj.getvalue()

    # Decode the bytes stored in get_body to HTML and print the result
    print('Output of GET request:\n%s' % get_body.decode('utf8'))


def example2():

    # Operation to examine the response headers of a given URL
    # Allows you to examine response headers and errors if you are experiencing them

    headers = {}

    def display_header(header_line):
        header_line = header_line.decode('iso-8859-1')

        # Ignore all lines without a colon
        if ':' not in header_line:
            return

        # Break the header line into header name and value
        h_name, h_value = header_line.split(':', 1)

        # Remove whitespace that may be present
        h_name = h_name.strip()
        h_value = h_value.strip()
        h_name = h_name.lower() # Convert header names to lowercase
        headers[h_name] = h_value # Header name and value.

    def main():
        print('**Using PycURL to get Twitter Headers**')
        b_obj = BytesIO()
        crl = pycurl.Curl()
        crl.setopt(crl.URL, 'https://twitter.com')
        crl.setopt(crl.HEADERFUNCTION, display_header)
        crl.setopt(crl.WRITEDATA, b_obj)
        crl.perform()
        print('Header values:-')
        print(headers)
        print('-' * 20)

    main()
