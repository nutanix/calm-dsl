# python2;success
print "python2"
output = urlreq("https://pypi.org/pypi/sampleproject/json", verb="GET")
author_email = output.json()['info']['author_email']

pprint(author_email)

pprint(pformat(author_email))

import requests
req_out = requests.get("https://pypi.org/pypi/sampleproject/json")
print req_out.text == output.text
