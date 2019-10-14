from .resource import ResourceAPI
from .connection import REQUEST
from .util import strip_secrets, patch_secrets
from calm.dsl.config import get_config
from .project import ProjectAPI


class BlueprintAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="blueprints")
        self.UPLOAD = self.PREFIX + "/import_json"
        self.LAUNCH = self.ITEM + "/simple_launch"
        self.FULL_LAUNCH = self.ITEM + "/launch"
        self.LAUNCH_POLL = self.ITEM + "/pending_launches/{}"
        self.BP_EDITABLES = self.ITEM + "/runtime_editables"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD, verify=False, request_json=payload, method=REQUEST.METHOD.POST
        )

    def launch(self, uuid, payload):
        return self.connection._call(
            self.LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def full_launch(self, uuid, payload):
        return self.connection._call(
            self.FULL_LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def poll_launch(self, blueprint_id, request_id):
        return self.connection._call(
            self.LAUNCH_POLL.format(blueprint_id, request_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def _get_editables(self, bp_uuid):
        return self.connection._call(
            self.BP_EDITABLES.format(bp_uuid), verify=False, method=REQUEST.METHOD.GET
        )

    @staticmethod
    def _make_blueprint_payload(bp_name, bp_desc, bp_resources, categories=None):

        bp_payload = {
            "spec": {
                "name": bp_name,
                "description": bp_desc or "",
                "resources": bp_resources,
            },
            "metadata": {"spec_version": 1, "name": bp_name, "kind": "blueprint"},
            "api_version": "3.0",
        }

        if categories:
            bp_payload["categories"] = categories

        return bp_payload

    def upload_with_secrets(self, bp_name, bp_desc, bp_resources, categories=None):

        # check if bp with the given name already exists
        params = {"filter": "name=={};state!=DELETED".format(bp_name)}
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entities", None)
        if entities:
            if len(entities) > 0:
                err_msg = "Blueprint with name {} already exists.".format(bp_name)
                # ToDo: Add command to edit Blueprints
                err = {"error": err_msg, "code": -1}
                return None, err

        secret_map = {}
        secret_variables = []
        object_lists = [
            "service_definition_list",
            "package_definition_list",
            "substrate_definition_list",
            "app_profile_list",
        ]
        strip_secrets(bp_resources, secret_map, secret_variables, object_lists=object_lists)

        upload_payload = self._make_blueprint_payload(bp_name, bp_desc, bp_resources)

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

        # Add secrets and update bp
        bp = res.json()
        del bp["status"]

        patch_secrets(bp['spec']['resources'], secret_map, secret_variables)

        # TODO - insert categories during update as /import_json fails if categories are given!
        # Populating the categories at runtime
        config_categories = dict(config.items("CATEGORIES"))
        if categories:
            config_categories.update(categories)

        bp["metadata"]["categories"] = config_categories

        # Update blueprint
        update_payload = bp
        uuid = bp["metadata"]["uuid"]

        return self.update(uuid, update_payload)
