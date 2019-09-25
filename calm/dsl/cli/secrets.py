import click
import arrow
import datetime
from prettytable import PrettyTable

from .utils import highlight_text
from calm.dsl.builtins import _create_secret, _delete_secret, _update_secret, list_secrets, _find_secret


def create_secret(name, value, pass_phrase=""):
    """Creates the secret"""

    secrets = get_secrets_names()
    if name in secrets:
        click.echo(highlight_text("Secret Already present !!!\nTry to update secret\n"))
        return

    _create_secret(name, value, pass_phrase)
    click.echo(highlight_text("\nSecret created !!! \n"))


def get_secrets(quiet):
    """List the secrets"""

    avl_secrets = list_secrets()

    if not avl_secrets:
        click.echo(highlight_text("No secrets found !!!\n"))
        return

    if quiet:
        for secret in avl_secrets:
            click.echo(highlight_text(secret["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "CREATED ON",
        "LAST UPDATED",
        "UUID",
    ]

    for secret in avl_secrets:
        creation_time = (secret["creation_time"]).strftime("%A, %d. %B %Y %I:%M%p")
        last_update_time = arrow.get(secret["last_update_time"].astimezone(datetime.timezone.utc)).humanize()
        table.add_row(
            [
                highlight_text(secret["name"]),
                highlight_text(creation_time),
                highlight_text(last_update_time),
                highlight_text(secret["uuid"])
            ]
        )

    click.echo(table)


def delete_secret(name):
    """Deletes the secret"""

    secrets = get_secrets_names()
    if name not in secrets:
        click.echo(highlight_text("\nSecret not present !!!\n"))
        return

    _delete_secret(name)
    click.echo(highlight_text("\nSecret deleted !!!\n"))


def update_secret(name, value, pass_phrase):
    """Updates the secret"""

    secrets = get_secrets_names()
    if name not in secrets:
        click.echo(highlight_text("\nSecret not present !!!\n"))
        return

    _update_secret(name, value, pass_phrase)
    click.echo(highlight_text("\nSecret updated !!!\n"))


def find_secret(name, pass_phrase=""):
    """ Gives you the value stored correponding to secret"""

    secret_val = _find_secret(name, pass_phrase)
    return secret_val


def get_secrets_names():

    secrets = list_secrets()
    secret_names = []
    for secret in secrets:
        secret_names.append(secret["name"])

    return secret_names
