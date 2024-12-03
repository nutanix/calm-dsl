import requests

pc_user = "@@{account.username}@@"
pc_passwd = "@@{account.password}@@"
vpclist = "@@{vpc_name}@@".split(",")
vpcuuidlist = [vpc.split(":")[1] for vpc in vpclist]

headers = {
    "accept": "application/json",
    "content-type": "application/json",
}

payload = {}

for vpcuuid in vpcuuidlist:
    r = requests.delete(
        "https://@@{account.pc_server}@@:@@{account.pc_port}@@/api/nutanix/v3/vpcs/{}".format(
            vpcuuid
        ),
        headers=headers,
        json=payload,
        verify=False,
        auth=(pc_user, pc_passwd),
    )
    r = json.loads(r.content)
    print("response:", r)
    state = r["status"]["state"]
    print("-----------------------------------------------")
    taskuuid = r["status"]["execution_context"]["task_uuid"]

    print(f"vpc_task_uuid = {taskuuid}")
    print(
        "Payload submitted and status is {} and task_uuid is {}".format(state, taskuuid)
    )

    c = 0

    api = "https://@@{account.pc_server}@@:@@{account.pc_port}@@/api/nutanix/v3/tasks/{}".format(
        taskuuid
    )
    r1 = requests.get(api, auth=(pc_user, pc_passwd), verify=False)
    state = r1.json()["status"]
    while state != "SUCCEEDED" or state != "SUCCESS":
        c += 1
        sleep(10)
        print("Waiting For Task To Finish, state:", state)
        r = requests.get(api, auth=(pc_user, pc_passwd), verify=False)
        state = r.json()["status"]
        if state == "SUCCEEDED":
            break
        if c >= 18:
            print("Timed out after 3min, Check task status on UI")
            exit(1)

    print(f"vpc_task_status = {state}")
