# flake8: noqa
# pylint: skip-file
# type: ignore

# script
import boto3

# Create bucket
region = "@@{location}@@"
bucket_name = "@@{bucket_name}@@"
ACL = "@@{ACL}@@"

if region is None:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id="@@{access_key_id}@@",
        aws_secret_access_key="@@{secret_access_key}@@",
    )
    response = s3_client.create_bucket(Bucket=bucket_name)
else:
    s3_client = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id="@@{access_key_id}@@",
        aws_secret_access_key="@@{secret_access_key}@@",
    )
    location = {"LocationConstraint": region}
    response = s3_client.create_bucket(
        Bucket=bucket_name, CreateBucketConfiguration=location
    )

bucket_arn = response["Location"]
print("ARN={}".format(bucket_arn))
