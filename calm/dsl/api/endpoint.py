import os

from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets
from calm.dsl.config import get_context
from .project import ProjectAPI


class EndpointAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="endpoints")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.EXPORT_FILE = self.ITEM + "/export_file"
        self.IMPORT_FILE = self.PREFIX + "/import_file"
        self.EXPORT_JSON = self.ITEM + "/export_json"
        self.EXPORT_JSON_WITH_SECRETS = self.ITEM + "/export_json?keep_secrets=true"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    @staticmethod
    def _make_endpoint_payload(
        endpoint_name, endpoint_desc, endpoint_resources, spec_version=None
    ):

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
            "api_version": "3.0",
        }

        return endpoint_payload

    def upload_with_secrets(
        self, endpoint_name, endpoint_desc, endpoint_resources, force_create=False
    ):

        # check if endpoint with the given name already exists
        params = {"filter": "name=={};deleted==FALSE".format(endpoint_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities:
            if len(entities) > 0:
                if not force_create:
                    err_msg = "Endpoint {} already exists. Use --force to first delete existing blueprint before create.".format(
                        endpoint_name
                    )
                    err = {"error": err_msg, "code": -1}
                    return None, err

                # --force option used in create. Delete existing endpoint with same name.
                ep_uuid = entities[0]["metadata"]["uuid"]
                _, err = self.delete(ep_uuid)
                if err:
                    return None, err

        secret_map = {}
        secret_variables = []

        strip_secrets(endpoint_resources["attrs"], secret_map, secret_variables)
        endpoint_resources["attrs"].pop("default_credential_local_reference", None)
        upload_payload = self._make_endpoint_payload(
            endpoint_name, endpoint_desc, endpoint_resources
        )

        ContextObj = get_context()
        project_config = ContextObj.get_project_config()
        project_name = project_config["name"]
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

        endpoint = res.json()
        del endpoint["status"]

        # Add secrets and update endpoint
        patch_secrets(
            endpoint["spec"]["resources"]["attrs"], secret_map, secret_variables
        )

        # Update endpoint
        uuid = endpoint["metadata"]["uuid"]

        return self.update(uuid, endpoint)

    def export_file(self, uuid, passphrase=None):
        current_path = os.path.dirname(os.path.realpath(__file__))
        if passphrase:
            res, err = self.connection._call(
                self.EXPORT_FILE.format(uuid),
                verify=False,
                method=REQUEST.METHOD.POST,
                request_json={"passphrase": passphrase},
                files=[],
            )
        else:
            res, err = self.connection._call(
                self.EXPORT_FILE.format(uuid), verify=False, method=REQUEST.METHOD.GET
            )

        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        with open(current_path + "/" + uuid + ".json", "wb") as downloaded_file:
            for chunk in res.iter_content(chunk_size=2048):
                downloaded_file.write(chunk)

        return current_path + "/" + uuid + ".json"

    def import_file(self, file_path, name, project_uuid, passphrase=None):

        payload = {"name": name, "project_uuid": project_uuid}
        if passphrase:
            payload["passphrase"] = passphrase
        files = {"file": ("file", open(file_path, "rb"))}

        return self.connection._call(
            self.IMPORT_FILE,
            verify=False,
            files=files,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def export_json(self, uuid):
        url = self.EXPORT_JSON.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def export_json_with_secrets(self, uuid):
        url = self.EXPORT_JSON_WITH_SECRETS.format(uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)
