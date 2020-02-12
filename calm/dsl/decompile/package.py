from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import PackageType, BlueprintType
from tests.next_demo.test_next_demo import NextDslBlueprint
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.decompile.action import render_action_template


def render_package_template(cls):

    if not isinstance(cls, PackageType):
        raise TypeError("{} is not of type {}".format(cls, PackageType))
    
    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    service_list = []
    for entity in user_attrs.get("services", []):
        service_list.append(render_ref_template(entity))

    variable_list = []
    for entity in user_attrs.get("variables", []):
        variable_list.append(render_variable_template(entity))
    
    action_list = []
    if hasattr(cls, "__install__"):
        cls.__install__.__name__ = "__install__"
        action_list.append(render_action_template(cls.__install__))
    
    if hasattr(cls, "__uninstall__"):
        cls.__uninstall__.__name__ = "__uninstall__"
        action_list.append(render_action_template(cls.__uninstall__))

    user_attrs["services"] = ",".join(service_list)
    user_attrs["variables"] = variable_list
    user_attrs["actions"] = action_list

    text = render_template("package.py.jinja2", obj=user_attrs)
    return text.strip()


bp_dict = NextDslBlueprint.get_dict()
bp_cls = BlueprintType.decompile(bp_dict)

#print(render_package_template(bp_cls.packages[1]))  

