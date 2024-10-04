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


# def delete(bucket_name):
#     object_store_uuid = get_resource_ext_id(
#         "https://{}:{}/api/objects/{}/operations/object-stores".format(
#             PC_IP, PC_PORT, "@@{objects_api_version}@@"
#         ),
#         "@@{object_store_name}@@",
#     )
#     for x in range(3):
#         try:
#             response = session.delete(
#                 f"https://{PC_IP}:{PC_PORT}/oss/api/nutanix/v3/objectstores/{object_store_uuid}/buckets/{bucket_name}",
#                 timeout=120,
#             )
#             print(f"delete response: {response.text}")
#             response.raise_for_status()
#             return
#         except Exception as e:
#             continue
#     raise Exception("unable to delete the bucket")


# delete("@@{bucket_name}@@")
