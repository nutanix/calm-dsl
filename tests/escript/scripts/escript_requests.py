# python3;success
print("python3")
output = urlreq("https://pypi.org/pypi/sampleproject/json", verb="GET")
email = output.json()["info"]["author_email"]

pprint(email)
print(uuid.uuid4() == uuid.uuid4())

import requests

req_out = requests.get("https://pypi.org/pypi/sampleproject/json")
print(req_out.text == output.text)
