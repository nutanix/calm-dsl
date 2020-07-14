from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import VmDiskPackageType


def render_vm_disk_package_template(cls):

    if not isinstance(cls, VmDiskPackageType):
        raise TypeError("{} is not of type {}".format(cls, VmDiskPackageType))

    disk_data = cls.get_dict()
    user_attrs = {
        "name": disk_data.pop("name"),
        "description": disk_data.pop("description"),
        "config": disk_data,
    }

    # Escape new line character. As it is inline parameter for vm_disk_package helper
    user_attrs["description"] = user_attrs["description"].replace("\n", "\\n")

    text = render_template("vm_disk_package.py.jinja2", obj=user_attrs)
    return text.strip()
