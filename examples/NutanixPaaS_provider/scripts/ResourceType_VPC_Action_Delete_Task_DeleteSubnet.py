import requests

pc_user = "@@{account.username}@@"
pc_passwd = "@@{account.password}@@"
subnets = "@@{subnet_name}@@".split("|")
if len(subnets) == 1 and subnets[0] == "":
    print("No subnet assiciated with this VPC, skipping subnet deletion.")
    exit(0)
subnetuuids = [sname.split(":")[2] for sname in subnets]

headers = {
    "accept": "application/json",
    "content-type": "application/json",
}

payload = {}

for suuid in subnetuuids:
    r = requests.delete(
        "https://@@{account.pc_server}@@:@@{account.pc_port}@@/api/nutanix/v3/subnets/{}".format(
            suuid
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
    print(f"subnet_task_uuid = {taskuuid}")
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

    print(f"subnet_task_status = {state}")
