vmip = "127.0.0.1"
vm_url = "http://{0}:12345/health".format(vmip)


def get_resource_list(url):
    headers = {"Content-Type": "text/html", "Accept": "text/html"}
    try:
        r = urlreq(url, verb="GET", headers=headers, auth="NONE")
    except Exception as e:
        print(e)
    return r


res = get_resource_list(vm_url)
print(res)
print("var1=" + vmip)
