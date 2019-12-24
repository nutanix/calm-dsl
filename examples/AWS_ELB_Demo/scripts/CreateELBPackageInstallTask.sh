#!/usr/bin/python
import boto3

elb_client = boto3.client('elbv2',aws_access_key_id='***REMOVED***',aws_secret_access_key='***REMOVED***',region_name='us-east-1')
PORT_INTERNAL=80
PORT_EXTERNAL=80


#Create load balancer
create_lb_response = elb_client.create_load_balancer(
    Name='dnd-wp-@@{calm_unique}@@',
    Subnets=[
        'subnet-c599a5ef',
        'subnet-0d281b615b2fe06b8'
    ],
    SecurityGroups=[
        'sg-184ead62',
    ],
    Scheme='internet-facing',
    Type='application',
    IpAddressType='ipv4'
)

# check create lb returned successfully
if create_lb_response['ResponseMetadata']['HTTPStatusCode'] == 200:
    lbId = create_lb_response['LoadBalancers'][0]['LoadBalancerArn']
    #print "Successfully created load balancer %s" % lbId
else:
    print ("Create load balancer failed")

#Create target group
create_tg_response = elb_client.create_target_group(Name='wordpress-@@{calm_unique}@@',
                                             Protocol='HTTP',
                                             Port=80,
                                             VpcId='vpc-ffd54d98')

 # check create target-group returned successfully
if create_tg_response['ResponseMetadata']['HTTPStatusCode'] == 200:
    tgId = create_tg_response['TargetGroups'][0]['TargetGroupArn']
    print "Successfully created target group %s" % tgId
else:
    print ("Create target group failed")




# Register targets

instance_ids = '@@{APACHE_PHP.aws_instance_id}@@'
targetIds = []
for i in instance_ids.split(','):
	targetIds.append(i)

targets_list = []
for target_id in targetIds:
    targets_list.append(
        {
            'Id': target_id,
            'Port': PORT_INTERNAL
        }
    )

reg_targets_response = elb_client.register_targets(TargetGroupArn=tgId, Targets=targets_list)

# check register group returned successfully
if reg_targets_response['ResponseMetadata']['HTTPStatusCode'] == 200:
    print "Successfully registered targets"
else:
    print ("Register targets failed")

# create Listener
create_listener_response = elb_client.create_listener(LoadBalancerArn=lbId,
                                                      Protocol='HTTP', Port=PORT_EXTERNAL,
                                                       DefaultActions=[{'Type': 'forward',
                                                                        'TargetGroupArn': tgId}])

# check create listener returned successfully
if create_listener_response['ResponseMetadata']['HTTPStatusCode'] == 200:
    print "Successfully created listener %s" % tgId
else:
    print ("Create listener failed")

print "TG_ID=",tgId
print "WP_ELB=",create_lb_response['LoadBalancers'][0]['DNSName']



