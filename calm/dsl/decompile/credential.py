from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import CredentialType
from tests.decompile.test_decompile import bp_cls


def render_credential_template(cls):

    if not isinstance(cls, CredentialType):
        raise TypeError("{} is not of type {}".format(cls, CredentialType))
    
    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    cred_type = cls.type
    if cred_type == "PASSWORD":
        user_attrs["value"] = user_attrs["secret"].get("value", "")
    
    text = render_template("cred_passwd_type.py.jinja2", obj = user_attrs)
    return text.strip()


print(render_credential_template(bp_cls.credentials[0]))
