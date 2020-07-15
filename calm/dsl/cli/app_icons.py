import click
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from .utils import highlight_text, get_name_query

LOG = get_logging_handle(__name__)


def create_app_icon(name, file):
    """creates app icon"""

    client = get_api_client()
    client.app_icon.upload(name, file)


def delete_app_icon(icon_names):
    """deletes app_icons in icon_names"""

    client = get_api_client()
    app_icon_name_uuid_map = client.app_icon.get_name_uuid_map()

    for icon_name in icon_names:
        app_icon_uuid = app_icon_name_uuid_map.get(icon_name, None)
        if not app_icon_uuid:
            LOG.error("APP icon: {} not found")
            sys.exit(-1)
        client.app_icon.delete(app_icon_uuid)
        LOG.info("App Icon {} deleted".format(icon_name))


def get_app_icon_list(name, limit, offset, quiet, marketplace_use=False):
    """Get list of app icons"""

    client = get_api_client()
    params = {"length": limit, "offset": offset}
    if name:
        params["filter"] = get_name_query([name])

    app_icon_name_uuid_map = client.app_icon.get_name_uuid_map(params)
    if quiet:
        for name in app_icon_name_uuid_map.keys():
            click.echo(highlight_text(name))
        return

    table = PrettyTable()
    field_names = ["NAME", "UUID"]
    if marketplace_use:
        field_names.append("IS_MARKETPLACE_ICON")

    table.field_names = field_names
    for name, uuid in app_icon_name_uuid_map.items():
        data_row = [highlight_text(name), highlight_text(uuid)]
        if marketplace_use:
            res, err = client.app_icon.is_marketplace_icon(uuid)
            if err:
                LOG.error("[{}] - {}".format(err["code"], err["error"]))
                sys.exit(-1)
            res = res.json()
            data_row.append(highlight_text(res["is_marketplaceicon"]))

        table.add_row(data_row)

    click.echo(table)
