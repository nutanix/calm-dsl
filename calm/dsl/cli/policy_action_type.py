import json
import click

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from .utils import (
    highlight_text,
)

LOG = get_logging_handle(__name__)


def get_policy_action_types():
    """function to get list of policy actions supported"""

    client = get_api_client()
    res, err = client.policy_action_types.list()
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    entities = res.get("entities", [])

    if not entities:
        click.echo(highlight_text("No policy_action_types found !!!\n"))
        return None
    return res
