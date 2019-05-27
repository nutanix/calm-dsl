import click
from .entity import EntityAPI


def create_resource(obj, relURL, payload):
    """ will create the resource """
    entity = EntityAPI(relURL, obj.connection)
    res, err = entity.create(payload)


def read_resource(obj, relURL, resourceID):
    """ will read the resource """
    entity = EntityAPI(relURL, obj.connection)
    res, err = entity.read(resourceID)


def update_resource(obj, relURL, resourceID, payload):
    """ will update the resource """
    entity = EntityAPI(relURL, obj.connection)
    res, err = entity.update(resourceID, payload)


def delete_resource(obj, relURL, resourceID):
    """ will delete the resource """
    entity = EntityAPI(relURL, obj.connection)
    res, err = entity.delete(resourceID)


def list_resource(obj, relURL, payload):
    """ will list the resources """
    entity = EntityAPI(relURL, obj.connection)
    res, err = entity.list(payload)
