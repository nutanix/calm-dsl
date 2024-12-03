raise Exception(
    "Not reccommented to use this script with @@{objects_api_version}@@ API version"
)

# import requests

# PC_USERNAME = "@@{account.username}@@"
# PC_PASSWORD = "@@{account.password}@@"
# PC_IP = "@@{account.pc_server}@@"
# PC_PORT = "@@{account.pc_port}@@"
# session = requests.Session()
# session.auth = (PC_USERNAME, PC_PASSWORD)
# session.verify = False
# payload = {}


# def get_resource_ext_id(url, name, id_key="extId"):
#     response = session.get(
#         url,
#         headers={
#             "accept": "application/json",
#         },
#         params={"$page": 0, "$limit": 1, "$filter": f"name eq '{name}'"},
#     )
#     print(f"get {name} response: {response.json()}")
#     response.raise_for_status()
#     data = response.json().get("data")
#     if data:
#         if isinstance(data, list):
#             if id_key in data[0] and data[0]["name"] == name:
#                 return data[0][id_key]
#         else:
#             if id_key in data:
#                 return data[id_key]
#     raise Exception(f"failed to get extId for {name}")


# def wait(task_uuid, timeout=1800):
#     max_count = timeout / 10
#     count = 0
#     task_status_response = None
#     while count <= 18:
#         task_status_response = session.get(
#             "https://{}:{}/api/prism/{}/config/tasks/{}".format(
#                 PC_IP, PC_PORT, "@@{prism_api_version}@@",task_uuid
#             ),
#         )
#         if task_status_response.status_code != 200:
#             raise Exception(
#                 f"failed to get task, got response {task_status_response.json()}"
#             )
#         print(f"task status is {task_status_response.json()['data']['status']}")
#         if task_status_response.json()["data"]["status"] in {"QUEUED", "RUNNING"}:
#             count += 1
#             sleep(10)
#         else:
#             count = 0
#             break
#     print(f"task_status = {task_status_response.json()['data']['status']}")
#     if count != 0:
#         raise Exception("timed out waiting for task to complete")


# def delete(name):
#     object_store_ext_id = get_resource_ext_id(
#         "https://{}:{}/api/objects/{}/operations/object-stores".format(PC_IP, PC_PORT, "@@{objects_api_version}@@"), name
#     )
#     ## get the object store
#     get_object_store_response = session.get(
#         "https://{}:{}/api/objects/{}/operations/object-stores/{extId}".format(
#             PC_IP, PC_PORT, "@@{objects_api_version}@@",object_store_ext_id
#         )
#     )
#     print(f"get object store response : {get_object_store_response.json()}")
#     get_object_store_response.raise_for_status()
#     delete_object_store_response = session.delete(
#         "https://{}:{}/api/objects/{}/operations/object-stores/{}".format(
#             PC_IP, PC_PORT, "@@{objects_api_version}@@",object_store_ext_id
#         ),
#         headers={"If-Match": get_object_store_response.headers["Etag"]},
#     )
#     print(f"delete object store response : {delete_object_store_response.json()}")
#     delete_object_store_response.raise_for_status()
#     task_uuid = delete_object_store_response.json()["data"]["extId"]
#     print(f"task_uuid = {task_uuid}")
#     if "@@{wait}@@":
#         wait(task_uuid)


# delete("@@{object_store_name}@@")
