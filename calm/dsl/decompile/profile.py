from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ProfileType, BlueprintType
from tests.next_demo.test_next_demo import NextDslBlueprint
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.variable import render_variable_template


def render_profile_template(cls):

    if not isinstance(cls, ProfileType):
        raise TypeError("{} is not of type {}".format(cls, ProfileType))
    
    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    action_list = []
    for action in user_attrs.get("actions", []):
        action_list.append(render_action_template(action))

    deployment_list = []
    for deployment in user_attrs.get("deployments", []):
        deployment_list.append(deployment.__name__)
    
    variable_list = []
    for entity in user_attrs.get("variables", []):
        variable_list.append(render_variable_template(entity))
    
    user_attrs["variables"] = variable_list
    user_attrs["deployments"] = ", ".join(deployment_list)
    user_attrs["actions"] = action_list
    
    text = render_template("profile.py.jinja2", obj=user_attrs)
    return text.strip()


bp_dict = NextDslBlueprint.get_dict()
bp_cls = BlueprintType.decompile(bp_dict)


print(render_profile_template(bp_cls.profiles[0]))
