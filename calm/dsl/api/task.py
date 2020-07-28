#import os

from .resource import ResourceAPI
#from .connection import REQUEST
#from .util import strip_secrets, patch_secrets
#from calm.dsl.config import get_config
#from .project import ProjectAPI


class RunbookAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="app_tasks")