import json
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.builtins.models.metadata import Metadata
from calm.dsl.builtins.models.calm_ref import Ref

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

DEFAULT_PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]["NAME"]


HttpEndpoint = Endpoint.HTTP(url="https://jsonplaceholder.typicode.com")


class EndpointMetadata(Metadata):
    project = Ref.Project(DEFAULT_PROJECT)
