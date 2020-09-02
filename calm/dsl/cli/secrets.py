import click
import arrow
import datetime
from prettytable import PrettyTable

from .utils import highlight_text

from calm.dsl.store import Secret
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def create_secret(name, value):
    """Creates the secret"""

    secrets = get_secrets_names()
    if name in secrets:
        LOG.error("Secret {} already present !!!".format(name))
        return

    LOG.debug("Creating secret {}".format(name))
    Secret.create(name, value)
    LOG.info(highlight_text("Secret {} created".format(name)))


def get_secrets(quiet):
    """List the secrets"""

    avl_secrets = Secret.list()

    if not avl_secrets:
        click.echo(highlight_text("No secret found !!!\n"))
        return

    if quiet:
        for secret in avl_secrets:
            click.echo(highlight_text(secret["name"]))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "CREATED ON", "LAST UPDATED", "UUID"]

    for secret in avl_secrets:
        creation_time = (secret["creation_time"]).strftime("%A, %d. %B %Y %I:%M%p")
        last_update_time = arrow.get(
            secret["last_update_time"].astimezone(datetime.timezone.utc)
        ).humanize()
        table.add_row(
            [
                highlight_text(secret["name"]),
                highlight_text(creation_time),
                highlight_text(last_update_time),
                highlight_text(secret["uuid"]),
            ]
        )

    click.echo(table)


def delete_secret(name):
    """Deletes the secret"""

    secrets = get_secrets_names()
    if name not in secrets:
        LOG.error("Secret {} not present !!!".format(name))
        return

    LOG.info("Deleting secret {}".format(name))
    Secret.delete(name)


def update_secret(name, value):
    """Updates the secret"""

    secrets = get_secrets_names()
    if name not in secrets:
        LOG.error("Secret {} not present !!!".format(name))
        return

    LOG.info("Updating secret {}".format(name))
    Secret.update(name, value)


def find_secret(name, pass_phrase=""):
    """Gives you the value stored correponding to secret"""

    secret_val = Secret.find(name, pass_phrase)
    return secret_val


def get_secrets_names():
    """To find the names stored in db"""

    secrets = Secret.list()
    secret_names = []
    for secret in secrets:
        secret_names.append(secret["name"])

    return secret_names


def clear_secrets():
    """Delete all the secrets"""

    LOG.info("Clearing the secrets")
    Secret.clear()
