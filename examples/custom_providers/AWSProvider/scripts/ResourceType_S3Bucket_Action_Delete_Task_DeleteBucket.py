# flake8: noqa
# pylint: skip-file
# type: ignore

# script

# Delete bucket

import boto3

bucket_name = "@@{bucket_name}@@"

s3_client = boto3.client(
    "s3",
    aws_access_key_id="@@{access_key_id}@@",
    aws_secret_access_key="@@{secret_access_key}@@",
)
response = s3_client.delete_bucket(Bucket=bucket_name)

print(response)
