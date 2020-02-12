from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import DeploymentType, BlueprintType
from tests.next_demo.test_next_demo import NextDslBlueprint
from calm.dsl.decompile.ref import render_ref_template


def render_deployment_template(cls):

    if not isinstance(cls, DeploymentType):
        raise TypeError("{} is not of type {}".format(cls, DeploymentType))
    
    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    depends_on_list = []
    for entity in user_attrs.get("dependencies", []):
        depends_on_list.append(render_ref_template(entity))

    if cls.substrate:
        user_attrs["substrate"] = render_ref_template(cls.substrate)
    
    package_list = []
    for entity in user_attrs.get("packages", []):
        package_list.append(render_ref_template(entity))

    user_attrs["packages"] = ", ".join(package_list)
    user_attrs["dependencies"] = ",".join(depends_on_list)

    text = render_template("deployment.py.jinja2", obj=user_attrs)
    return text.strip()

bp_dict = NextDslBlueprint.get_dict()
bp_cls = BlueprintType.decompile(bp_dict)


# print(render_deployment_template(bp_cls.profiles[0].deployments[1]))
