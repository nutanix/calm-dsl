def get_vpc_tunnel_using_account(config):
    vpc = ""  # set default, if found set that value
    accounts = config.get("ACCOUNTS", {}).get("NUTANIX_PC", [])
    for acc in accounts:
        if acc.get("NAME") == "NTNX_LOCAL_AZ":
            for subnet in acc.get("OVERLAY_SUBNETS", []):
                if subnet.get("VPC", "") == "vpc_name_1":
                    vpc = "vpc_name_1"
                    break
    vpc_tunnel = config.get("VPC_TUNNELS", {}).get("NTNX_LOCAL_AZ", {}).get(vpc, {})

    return vpc_tunnel.get("name", "")


def get_vpc_project(config):
    vpc_project = (
        config.get("VPC_PROJECTS", {}).get("PROJECT1", {}).get("NAME", "") or "default"
    )
    return vpc_project
