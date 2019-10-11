from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets


class EndpointAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="endpoints")
        self.UPLOAD = self.PREFIX + "/import_json"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    @staticmethod
    def _make_endpoint_payload(endpoint_name, endpoint_desc, endpoint_resources, project_ref=None, spec_version=None):

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

        if project_ref:
            endpoint_payload['metadata']['project_reference'] = project_ref

        return endpoint_payload

    def upload_with_secrets(self, endpoint_name, endpoint_desc, endpoint_resources, project_ref=None):

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

        upload_payload = self._make_endpoint_payload(endpoint_name, endpoint_desc, endpoint_resources, project_ref=project_ref)

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
        update_payload = patch_secrets(endpoint, secret_map, secret_variables)

        return self.update(uuid, update_payload)
