def RestAPI(sslApiBaseUri, method, requestBody, username, password):
  headers = {"Accept" : "application/json", "Content-Type" : "application/json"}
  output = urlreq(sslApiBaseUri, verb=method, params=json.dumps(requestBody), headers=headers, verify=False, auth="BASIC", user=username, passwd=password)
  if output.status_code != 202:
    if output.status_code == 500:
      print output.json()
      exit(1)
    else:
      print "Failed to Connect/Authenticate."
      exit(1)
  return output

pc_ip = "10.135.20.2"
pc_username = "admin"
pc_password = "Nutanix@123"
objectstore_uuid = "72b52b34-98ac-4774-7ed3-3e882b35b85e"
resources_blob = @@{resources_blob}@@
bucket_name = resources_blob["bucket_name"]

ObjectsDeleteurl = "https://{}:9440/oss/api/nutanix/v3/objectstores/{}/buckets/{}".format(pc_ip, objectstore_uuid,bucket_name)

output = RestAPI(ObjectsDeleteurl, "DELETE", None, pc_username, pc_password)
if output.json() == None:
   print "Bucket deleted successfully"