# python3;success

from kubernetes import client as k8client
aToken = 'token_a'
configuration=k8client.Configuration()
configuration.host="https://{}:{}".format('server', 'kube_port')
configuration.verify_ssl=False
configuration.debug=True
configuration.api_key={"authorization":"Bearer "+ aToken}
k8client.Configuration.set_default(configuration)
v1=k8client.CoreV1Api()
nodes=v1.list_node(watch=False)
print(nodes.items[0].metadata.name == "master0")