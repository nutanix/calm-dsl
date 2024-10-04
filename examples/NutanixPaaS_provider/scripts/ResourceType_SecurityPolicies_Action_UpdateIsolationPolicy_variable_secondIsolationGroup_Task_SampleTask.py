import requests

PC_USERNAME = "@@{username}@@"
PC_PASSWORD = "@@{password}@@"
PC_IP = "@@{pc_server}@@"
PC_PORT = "@@{pc_port}@@"


def list_category():
    headers = {
        "Accept": "application/json",
    }
    url = "https://{}:{}/api/prism/{}/config/categories".format(
        PC_IP, PC_PORT, "v4.0.b1"
    )
    page = 0
    results_len = 1
    tmp = []

    while results_len != 0:
        params = {"$limit": 100, "$orderby": "key", "$page": page}
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
                # print(each['key']+':'+each['value'])
                tmp.append(each["key"] + ":" + each["value"])
            results_len = len(data)
            page += 1
        except:
            break
    print(",".join(tmp))


list_category()
