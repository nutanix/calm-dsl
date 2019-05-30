import json
import click
from ..api.cloud import CloudAPI


def create_resource(obj, relURL, payload):
    """ will create the resource """
    entity = CloudAPI(relURL, obj.connection)
    payload = json.loads(payload)
    res, err = entity.create(payload)
    click.echo(res.json())


def read_resource(obj, relURL, resourceID):
    """ will read the resource """
    entity = CloudAPI(relURL, obj.connection)
    res, err = entity.read(resourceID)
    click.echo(res.json())


def update_resource(obj, relURL, resourceID, payload):
    """ will update the resource """
    entity = CloudAPI(relURL, obj.connection)
    payload = json.loads(payload)
    res, err = entity.update(resourceID, payload)
    click.echo(res.json())


def delete_resource(obj, relURL, resourceID):
    """ will delete the resource """
    entity = CloudAPI(relURL, obj.connection)
    res, err = entity.delete(resourceID)
    click.echo(res.json())


def list_resource(obj, relURL, payload):
    """ will list the resources """
    entity = CloudAPI(relURL, obj.connection)
    payload = json.loads(payload)
    res, err = entity.list(payload)
    click.echo(res.json())
