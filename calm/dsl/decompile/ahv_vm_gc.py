import sys
import os
from ruamel import yaml

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.credential import get_cred_var_name
from calm.dsl.decompile.file_handler import get_specs_dir, get_specs_dir_key
from calm.dsl.builtins import RefType
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm_gc(cls, vm_name_prefix=""):

    schema_file = ""
    user_attrs = {}

    user_attrs = cls.get_dict()
    cloud_init = user_attrs.get("cloud_init", {})
    sys_prep = user_attrs.get("sysprep", {})

    file_name = ""
    spec_dir = get_specs_dir()
    if cloud_init:
        schema_file = "ahv_vm_cloud_init.py.jinja2"
        file_name = "{}_cloud_init_data.yaml".format(vm_name_prefix)
        user_attrs["filename"] = "os.path.join('{}', '{}')".format(
            get_specs_dir_key(), file_name
        )
        cloud_init_user_data = cloud_init.get("user_data", "")
        if not cloud_init_user_data:
            return

        with open(os.path.join(spec_dir, file_name), "w+") as fd:
            # TODO take care of macro case
            fd.write(yaml.dump(cloud_init_user_data, default_flow_style=False))

    elif sys_prep:
        file_name = "{}_sysprep_unattend_xml.xml".format(vm_name_prefix)
        user_attrs["filename"] = "os.path.join('{}', '{}')".format(
            get_specs_dir_key(), file_name
        )
        sysprep_unattend_xml = sys_prep.get("unattend_xml", "")
        with open(os.path.join(spec_dir, file_name), "w+") as fd:
            fd.write(sysprep_unattend_xml)

        install_type = sys_prep.get("install_type", "PREPARED")
        is_domain = sys_prep.get("is_domain", False)

        if is_domain and sys_prep.get("domain_credential_reference"):
            cred = RefType.decompile(sys_prep["domain_credential_reference"])
            user_attrs["credential"] = "ref({})".format(
                get_cred_var_name(cred.__name__)
            )

        if install_type == "FRESH":
            if is_domain:
                schema_file = "ahv_vm_fresh_sysprep_with_domain.py.jinja2"
            else:
                schema_file = "ahv_vm_fresh_sysprep_without_domain.py.jinja2"

        elif install_type == "PREPARED":
            if is_domain:
                schema_file = "ahv_vm_prepared_sysprep_with_domain.py.jinja2"
            else:
                schema_file = "ahv_vm_prepared_sysprep_without_domain.py.jinja2"

        else:
            LOG.error(
                "Unknown install type '{}' for sysprep guest customization".format(
                    install_type
                )
            )
            sys.exit(-1)

    else:
        return None

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
