import click
import arrow
import datetime
from prettytable import PrettyTable

from .utils import highlight_text
from calm.dsl.builtins import Secret


def create_secret(name, value):
    """Creates the secret"""

    secrets = get_secrets_names()
    if name in secrets:
        click.echo(highlight_text("Secret Already present !!!\nTry to update secret\n"))
        return

    Secret.create(name, value)
    click.echo(highlight_text("\nSecret created !!! \n"))


def get_secrets(quiet):
    """List the secrets"""

    avl_secrets = Secret.list()

    if not avl_secrets:
        click.echo(highlight_text("No secrets found !!!\n"))
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
        click.echo(highlight_text("\nSecret not present !!!\n"))
        return

    Secret.delete(name)
    click.echo(highlight_text("\nSecret deleted !!!\n"))


def update_secret(name, value):
    """Updates the secret"""

    secrets = get_secrets_names()
    if name not in secrets:
        click.echo(highlight_text("\nSecret not present !!!\n"))
        return

    Secret.update(name, value)
    click.echo(highlight_text("\nSecret updated !!!\n"))


def find_secret(name, pass_phrase=""):
    """ Gives you the value stored correponding to secret"""

    secret_val = Secret.find(name, pass_phrase)
    return secret_val


def get_secrets_names():
    """ To find the names stored in db"""

    secrets = Secret.list()
    secret_names = []
    for secret in secrets:
        secret_names.append(secret["name"])

    return secret_names
