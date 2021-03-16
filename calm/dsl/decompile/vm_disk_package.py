from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import VmDiskPackageType
from calm.dsl.decompile.ref_dependency import update_package_name


def render_vm_disk_package_template(cls):

    if not isinstance(cls, VmDiskPackageType):
        raise TypeError("{} is not of type {}".format(cls, VmDiskPackageType))

    # It will be used for image reference in ahv vm disks
    gui_display_name = getattr(cls, "name", "") or cls.__name__
    update_package_name(gui_display_name, cls.__name__)

    disk_data = cls.get_dict()
    user_attrs = {
        "name": cls.__name__,
        "description": disk_data.pop("description"),
        "config": disk_data,
    }

    # Escape new line character. As it is inline parameter for vm_disk_package helper
    user_attrs["description"] = user_attrs["description"].replace("\n", "\\n")

    text = render_template("vm_disk_package.py.jinja2", obj=user_attrs)
    return text.strip()
