# python3;success

import boto3
ec2 = boto3.client('ec2', aws_access_key_id='accessKey', aws_secret_access_key='secretKey', region_name='us-east-1')
regions = ec2.describe_regions()
region_names = []
for i in regions['Regions']:
    region_names.append(i['RegionName'])

print("us-east-2" in region_names)