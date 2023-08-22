from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import MetadataType


def render_metadata_template(cls):

    if not cls:
        return

    if not isinstance(cls, MetadataType):
        raise TypeError("{} is not of type {}".format(cls, MetadataType))

    cls_data = cls.get_dict()
    user_attrs = {}

    if cls_data.get("categories"):
        user_attrs["categories"] = cls_data["categories"]

    if cls_data.get("project_reference", {}):
        user_attrs["project_name"] = cls_data["project_reference"]["name"]

    # NOTE: Project and Owner info is not provided by calm export_file api yet.
    # When available add their rendered_text to user_attrs and modify jinja template accordingly

    # NOTE: Name of class is constant i.e. EntityMetadata

    # If metadata is not available, return empty string
    if not user_attrs:
        return ""

    text = render_template("metadata.py.jinja2", obj=user_attrs)

    return text.strip()
