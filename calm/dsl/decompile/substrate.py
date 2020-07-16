from ruamel import yaml
import os
import sys

from calm.dsl.builtins import AhvVmType
from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.readiness_probe import render_readiness_probe_template
from calm.dsl.decompile.file_handler import get_specs_dir, get_specs_dir_key
from calm.dsl.builtins import SubstrateType, get_valid_identifier
from calm.dsl.decompile.ahv_vm import render_ahv_vm
from calm.dsl.decompile.ref_dependency import update_substrate_name
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_substrate_template(cls, vm_images=[]):

    LOG.debug("Rendering {} substrate template".format(cls.__name__))
    if not isinstance(cls, SubstrateType):
        raise TypeError("{} is not of type {}".format(cls, SubstrateType))

    # Entity context
    entity_context = "Substrate_" + cls.__name__

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or ""

    # Update substrate name map and gui name
    gui_display_name = getattr(cls, "name", "") or cls.__name__
    if gui_display_name != cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    # updating ui and dsl name mapping
    update_substrate_name(gui_display_name, cls.__name__)

    provider_spec_editables = user_attrs.get("provider_spec_editables", {})
    create_spec_editables = provider_spec_editables.get("create_spec", {})
    readiness_probe_editables = provider_spec_editables.get("readiness_probe", {})

    # Handle readiness probe for substrate
    rp_editable_list = []
    for k, v in readiness_probe_editables.items():
        if v:
            rp_editable_list.append(k)

    # Appending readiness_probe editables to readiness_probe object
    readiness_probe = user_attrs["readiness_probe"]
    readiness_probe.editables_list = rp_editable_list
    user_attrs["readiness_probe"] = render_readiness_probe_template(
        user_attrs["readiness_probe"]
    )

    spec_dir = get_specs_dir()

    # Handle create spec runtime editables
    if create_spec_editables:
        create_spec_editable_file_name = cls.__name__ + "_create_spec_editables.yaml"
        file_location = os.path.join(spec_dir, create_spec_editable_file_name)
        dsl_file_location_alias = "os.path.join('{}', '{}')".format(
            get_specs_dir_key(), create_spec_editable_file_name
        )
        user_attrs["provider_spec_editables"] = "read_spec({})".format(
            dsl_file_location_alias
        )

        # Write editable spec to separate file
        with open(file_location, "w+") as fd:
            fd.write(yaml.dump(create_spec_editables, default_flow_style=False))

    # Handle provider_spec for substrate
    provider_spec = cls.provider_spec
    if cls.provider_type == "AHV_VM":
        boot_config = provider_spec["resources"].get("boot_config", {})
        if not boot_config:
            LOG.error(
                "Boot config not present in {} substrate spec".format(cls.__name__)
            )
            sys.exit(-1)
        vm_cls = AhvVmType.decompile(
            provider_spec, context=[cls.__schema_name__, gui_display_name]
        )
        user_attrs["provider_spec"] = vm_cls.__name__
        ahv_vm_str = render_ahv_vm(vm_cls, boot_config)

    else:
        # creating a file for storing provider_spec
        provider_spec_file_name = cls.__name__ + "_provider_spec.yaml"
        user_attrs["provider_spec"] = get_provider_spec_string(
            spec=provider_spec,
            filename=provider_spec_file_name,
            provider_type=cls.provider_type,
            vm_images=vm_images,
        )

        # Write provider spec to separate file
        file_location = os.path.join(spec_dir, provider_spec_file_name)
        with open(file_location, "w+") as fd:
            fd.write(yaml.dump(provider_spec, default_flow_style=False))

    # Actions
    action_list = []
    system_actions = {v: k for k, v in SubstrateType.ALLOWED_FRAGMENT_ACTIONS.items()}
    for action in user_attrs.get("actions", []):
        if action.__name__ in list(system_actions.keys()):
            action.name = system_actions[action.__name__]
            action.__name__ = system_actions[action.__name__]
        action_list.append(render_action_template(action, entity_context))

    user_attrs["actions"] = action_list

    substrate_text = render_template(schema_file="substrate.py.jinja2", obj=user_attrs)
    if cls.provider_type == "AHV_VM":
        # Append definition for ahv vm class on top of substrate class
        substrate_text = "{}\n{}".format(ahv_vm_str, substrate_text)

    return substrate_text.strip()


def get_provider_spec_string(spec, filename, provider_type, vm_images):

    # TODO add switch to use YAML_file/Helper_class for ahv provider
    dsl_file_location_alias = "os.path.join('{}', '{}')".format(
        get_specs_dir_key(), filename
    )
    if provider_type == "AHV_VM":
        disk_list = spec["resources"]["disk_list"]

        disk_ind_img_map = {}
        for ind, disk in enumerate(disk_list):
            data_source_ref = disk.get("data_source_reference", {})
            if data_source_ref:
                if data_source_ref.get("kind") == "app_package":
                    disk_ind_img_map[ind + 1] = get_valid_identifier(
                        data_source_ref.get("name")
                    )
                    data_source_ref.pop("uuid", None)

        disk_pkg_string = ""
        for k, v in disk_ind_img_map.items():
            disk_pkg_string += ",{}: {}".format(k, v)
        if disk_pkg_string.startswith(","):
            disk_pkg_string = disk_pkg_string[1:]
        disk_pkg_string = "{" + disk_pkg_string + "}"

        res = "read_ahv_spec({}, disk_packages = {})".format(
            dsl_file_location_alias, disk_pkg_string
        )

    elif provider_type == "VMWARE_VM":
        spec_template = get_valid_identifier(spec["template"])

        if spec_template in vm_images:
            spec["template"] = ""
            res = "read_vmw_spec({}, vm_template={})".format(
                dsl_file_location_alias, spec_template
            )

        else:
            res = "read_vmw_spec({})".format(dsl_file_location_alias)

    else:
        res = "read_provider_spec({})".format(dsl_file_location_alias)

    return res
