#!/usr/bin/python
import boto3

elb_client = boto3.client('elbv2',aws_access_key_id='@@{AWS_ACCESS_KEY_ID}@@',aws_secret_access_key='@@{AWS_SECRET_ACCESS_KEY}@@',region_name='us-east-1')
PORT_INTERNAL=80
PORT_EXTERNAL=80

# Register targets
instance_ids = '@@{APACHE_PHP.aws_instance_id}@@'
targetIds = []
for i in instance_ids.split(','):
	targetIds.append(i)

targets_list = [dict(Id=target_id, Port=PORT_INTERNAL) for target_id in targetIds]
reg_targets_response = elb_client.register_targets(TargetGroupArn='@@{TG_ID}@@', Targets=targets_list)

# check register group returned successfully
if reg_targets_response['ResponseMetadata']['HTTPStatusCode'] == 200:
    print "Successfully registered targets"
else:
    print ("Register targets failed")
