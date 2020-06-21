import sys

from calm.dsl.decompile.render import render_template
from calm.dsl.store import Cache
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm_nic(cls):

    nic_data = cls.get_dict()

    subnet_ref = nic_data["subnet_reference"]
    nic_type = nic_data["nic_type"]
    network_function_nic_type = nic_data["network_function_nic_type"]
    subnet_cache_data = Cache.get_entity_data_using_uuid(
        entity_type="ahv_subnet", uuid=subnet_ref["uuid"]
    )

    user_attrs = {}
    user_attrs["subnet_name"] = subnet_cache_data["name"]
    user_attrs["cluster_name"] = subnet_cache_data["cluster"]
    schema_file = ""

    if nic_type == "NORMAL_NIC":
        if network_function_nic_type == "INGRESS":
            schema_file = "ahv_normal_ingress_nic.py.jinja2"

        elif network_function_nic_type == "EGRESS":
            schema_file = "ahv_normal_egress_nic.py.jinja2"

        elif network_function_nic_type == "TAP":
            schema_file = "ahv_normal_tap_nic.py.jinja2"

        else:
            LOG.error(
                "Unknown network function nic type '{}'".format(
                    network_function_nic_type
                )
            )
            sys.exit(-1)

    elif nic_type == "DIRECT_NIC":
        if network_function_nic_type == "INGRESS":
            schema_file = "ahv_direct_ingress_nic.py.jinja2"

        elif network_function_nic_type == "EGRESS":
            schema_file = "ahv_direct_egress_nic.py.jinja2"

        elif network_function_nic_type == "TAP":
            schema_file = "ahv_direct_tap_nic.py.jinja2"

        else:
            LOG.error(
                "Unknown network function nic type '{}'".format(
                    network_function_nic_type
                )
            )
            sys.exit(-1)

    else:
        LOG.error("Unknown nic type '{}'".format(nic_type))
        sys.exit(-1)

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
