# flake8: noqa
# pylint: skip-file
# type: ignore

"""
Note: The provided methods in this script are generic and meant to serve as a starting point for credential verification. They can be customized to fit specific use cases and requirements
"""

"""

Script Verify AWS credentials by making an sts service call using the boto3 library. It takes following parameters as macros defined in test-account/ provider.

Parameters:
`access_key_id`: The AWS access key ID.
`secret_access_key`: The AWS secret access key.
Process: 

Creates an sts client with the provided credentials and calls get_caller_identity. Checks for client errors to determine the validity of the credentials.

"""


import boto3

try:
    client = boto3.client(
        "sts",
        aws_access_key_id="@@{access_key_id}@@",
        aws_secret_access_key="@@{secret_access_key}@@",
    )
    client.get_caller_identity()
    print("AWS credentials are valid")
    exit(0)
except client.exceptions.ClientError as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "InvalidClientTokenId":
        print("Invalid AWS access key ID.")
    elif error_code == "SignatureDoesNotMatch":
        print("Invalid AWS secret access key.")
    else:
        print(f"AWS credentials are invalid. Error: {str(e)}")
except Exception as e:
    print(f"Script execution failed with error: {e}")
exit(1)
