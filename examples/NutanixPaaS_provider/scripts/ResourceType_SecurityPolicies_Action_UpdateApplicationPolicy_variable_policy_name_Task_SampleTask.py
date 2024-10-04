import requests

PC_USERNAME = "@@{username}@@"
PC_PASSWORD = "@@{password}@@"
PC_IP = "@@{pc_server}@@"
PC_PORT = "@@{pc_port}@@"


def list_policies():
    headers = {
        "Accept": "application/json",
    }
    url = "https://{}:{}/api/microseg/{}/config/policies".format(
        PC_IP, PC_PORT, "v4.0.b1"
    )
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
        response.raise_for_status()
        try:
            data = response.json()["data"]
            for each in data:
                if each["type"] == "APPLICATION":
                    tmp.append(each["name"])
            results_len = len(data)
            page += 1
        except:
            break
    print(",".join(tmp))


list_policies()
