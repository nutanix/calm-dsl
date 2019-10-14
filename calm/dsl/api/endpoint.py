from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets
from calm.dsl.config import get_config
from .project import ProjectAPI


class EndpointAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="endpoints")
        self.UPLOAD = self.PREFIX + "/import_json"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    @staticmethod
    def _make_endpoint_payload(endpoint_name, endpoint_desc, endpoint_resources, spec_version=None):

        endpoint_payload = {
            "spec": {
                "name": endpoint_name,
                "description": endpoint_desc or "",
                "resources": endpoint_resources,
            },
            "metadata": {
                "spec_version": spec_version or 1,
                "name": endpoint_name,
                "kind": "endpoint",
            },
            "api_version": "3.0"
        }

        return endpoint_payload

    def upload_with_secrets(self, endpoint_name, endpoint_desc, endpoint_resources):

        # check if endpoint with the given name already exists
        params = {"filter": "name=={};deleted==FALSE".format(endpoint_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities:
            if len(entities) > 0:
                err_msg = "Endpoint with name {} already exists.".format(endpoint_name)
                err = {"error": err_msg, "code": -1}
                return None, err

        secret_map = {}
        secret_variables = []

        strip_secrets(endpoint_resources, secret_map, secret_variables)

        # default cred is login cred in endpoint
        endpoint_resources["login_credential_reference"] = endpoint_resources.pop("default_credential_local_reference", {})

        upload_payload = self._make_endpoint_payload(endpoint_name, endpoint_desc, endpoint_resources)

        config = get_config()
        project_name = config["PROJECT"]["name"]
        projectObj = ProjectAPI(self.connection)

        # Fetch project details
        params = {"filter": "name=={}".format(project_name)}
        res, err = projectObj.list(params=params)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        if not entities:
            raise Exception("No project with name {} exists".format(project_name))

        project_id = entities[0]["metadata"]["uuid"]

        # Setting project reference
        upload_payload["metadata"]["project_reference"] = {
            "kind": "project",
            "uuid": project_id,
            "name": project_name,
        }

        res, err = self.upload(upload_payload)

        if err:
            return res, err

        # Add secrets and update endpoint
        endpoint = res.json()
        del endpoint["status"]
        uuid = endpoint["metadata"]["uuid"]

        res, err = self.read(uuid)

        if err:
            return res, err

        # Add secrets and update endpoint
        endpoint = res.json()
        del endpoint["status"]

        # Update endpoint
        patch_secrets(endpoint['spec']['resources'], secret_map, secret_variables)

        return self.update(uuid, endpoint)
