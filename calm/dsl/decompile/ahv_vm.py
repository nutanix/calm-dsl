from calm.dsl.builtins import AhvVmType

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ahv_vm_resources import render_ahv_vm_resources
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm(cls, boot_config):

    LOG.debug("Rendering {} ahv_vm template".format(cls.__name__))
    if not isinstance(cls, AhvVmType):
        raise TypeError("{} is not of type {}".format(cls, AhvVmType))

    user_attrs = cls.get_user_attrs()
    vm_name = cls.__name__
    user_attrs["name"] = vm_name

    # Update service name map and gui name
    gui_display_name = getattr(cls, "name", "") or vm_name
    if gui_display_name != vm_name:
        user_attrs["gui_display_name"] = gui_display_name

    # render resources template
    user_attrs["resources_cls_name"] = "{}Resources".format(vm_name)
    cls.resources.__name__ = user_attrs["resources_cls_name"]
    user_attrs["resources"] = render_ahv_vm_resources(
        cls.resources, boot_config=boot_config, vm_name_prefix=vm_name
    )

    text = render_template(schema_file="ahv_vm.py.jinja2", obj=user_attrs)
    return text.strip()
