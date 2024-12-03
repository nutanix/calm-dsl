import requests

pc_user = "@@{account.username}@@"
pc_passwd = "@@{account.password}@@"
subnetuuid = "@@{subnet_list}@@".split(":")[1]

headers = {
    "accept": "application/json",
    "content-type": "application/json",
}

payload = {}
r = requests.delete(
    "https://@@{account.pc_server}@@:@@{account.pc_port}@@/api/nutanix/v3/subnets/{}".format(
        subnetuuid
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
print(f"task_uuid = {taskuuid}")
print("Payload submitted and status is {} and task_uuid is {}".format(state, taskuuid))

c = 0
wait_for_exec = True
if wait_for_exec:
    api = "https://@@{account.pc_server}@@:@@{account.pc_port}@@/api/nutanix/v3/tasks/{}".format(
        taskuuid
    )
    # api = 'https://10.115.150.164:9440/api/nutanix/v3/tasks/{}'.format(taskuuid)
    r1 = requests.get(api, auth=(pc_user, pc_passwd), verify=False)
    state = r1.json()["status"]
    while state != "SUCCEEDED":
        c += 1
        sleep(10)
        print("Waiting For Task To Finish, state:", state)
        r = requests.get(api, auth=(pc_user, pc_passwd), verify=False)
        state = r.json()["status"]
        if c >= 18:
            print("Timed out after 3min, Check task status on UI")
            exit(1)

    print(f"task_status = {state}")
