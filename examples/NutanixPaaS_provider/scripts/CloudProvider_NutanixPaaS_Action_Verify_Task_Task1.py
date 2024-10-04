"""
Note: The provided methods in this script are generic and meant to serve as a starting point for credential verification. They can be customized to fit specific use cases and requirements
"""
"""
Script Verify Nutanix credentials by sending a POST request to the Nutanix API. It takes following parameters as macros defined in test-account/ provider.
Parameters:
\`pc_server\`: The Nutanix pc server.
\`pc_port\`: The Nutanix pc port.
\`username\`: The username for Nutanix authentication.
\`password\`: The password for Nutanix authentication.
Process: 
Sends a POST request with the credentials to the Nutanix API. Checks the response status code to determine the validity of the credentials.
"""
import requests
import base64

url = "https://@@{pc_server}@@:@@{pc_port}@@/api/nutanix/v3/clusters/list"
credentials = "@@{username}@@:@@{password}@@"
encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
payload = json.dumps({})
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {encoded_credentials}",
}
try:
    response = requests.post(url, headers=headers, data=payload, verify=False)
    if response.status_code == 200:
        print("Nutanix credentials are valid.")
        exit(0)
    elif response.status_code == 401:
        print("Unauthorized: Invalid Nutanix credentials.")
    elif response.status_code == 403:
        print("Forbidden: Insufficient privileges for Nutanix.")
    else:
        print(
            f"Nutanix credentials are invalid. Response code: {response.status_code}, Response: {response.text}"
        )
except Exception as e:
    print("Script execution failed with error: {}".format(e))
exit(1)
