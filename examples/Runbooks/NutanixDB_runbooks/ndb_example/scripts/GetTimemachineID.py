#Lets get the timemachine ID and create a snapshot
time_machines = json.loads('''@@{time_machine}@@''')
print "time_machine_id={}".format(time_machines[0]["id"])