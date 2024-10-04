import requests

PC_USERNAME = "@@{username}@@"
PC_PASSWORD = "@@{password}@@"
PC_IP = "@@{pc_server}@@"
PC_PORT = "@@{pc_port}@@"


def list_policies():
    headers = {"Accept": "application/json"}
    url = "https://{}:{}/api/microseg/{}/config/service-groups".format(
        PC_IP, PC_PORT, "v4.0.b1"
    )
    limit = 100
    page = 0
    results_len = 1
    tmp = []
    while results_len != 0:
        params = {"$limit": 100, "$orderby": "name", "$page": page}
        response = requests.get(
            url,
            auth=(PC_USERNAME, PC_PASSWORD),
            params=params,
            headers=headers,
            verify=False,
        )
        try:
            data = response.json()["data"]
            for each in data:
                if "tcpServices" in each.keys():
                    port_data = [
                        str(d["startPort"])
                        if d["startPort"] == d["endPort"]
                        else str(d["startPort"]) + "-" + str(d["endPort"])
                        for d in each["tcpServices"]
                    ]
                else:
                    port_data = [
                        str(d["startPort"])
                        if d["startPort"] == d["endPort"]
                        else str(d["startPort"]) + "-" + str(d["endPort"])
                        for d in each["udpServices"]
                    ]
                tmp.append(each["name"] + ":" + ",".join(port_data))
            results_len = len(data)
            page += 1
        except:
            break
    print(",".join(tmp))


list_policies()
