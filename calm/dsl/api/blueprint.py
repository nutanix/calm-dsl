from .resources import ResourceAPI
from .connection import REQUEST


class BlueprintAPI(ResourceAPI):

    PREFIX = ResourceAPI.PREFIX + "blueprints"
    LIST = PREFIX + "/list"
    UPLOAD = PREFIX + "/import_json"
    ITEM = PREFIX + "/{}"
    LAUNCH = ITEM + "/simple_launch"
    FULL_LAUNCH = ITEM + "/launch"
    LAUNCH_POLL = ITEM + "/pending_launches/{}"
    BP_EDITABLES = PREFIX + "/{}/runtime_editables"

    def upload(self, payload):
        return self.connection._call(
            self.UPLOAD,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
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
            self.BP_EDITABLES.format(bp_uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    @staticmethod
    def _make_blueprint_payload(bp_name, bp_desc, bp_resources):

        bp_payload = {
            "spec": {
                "name": bp_name,
                "description": bp_desc or "",
                "resources": bp_resources,
            },
            "metadata": {"spec_version": 1, "name": bp_name, "kind": "blueprint"},
            "api_version": "3.0",
        }

        return bp_payload

    def upload_with_secrets(self, bp_name, bp_desc, bp_resources):

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

        # Remove creds before upload
        creds = bp_resources["credential_definition_list"]
        secret_map = {}
        for cred in creds:
            name = cred["name"]
            secret_map[name] = cred.pop("secret", {})
            # Explicitly set defaults so that secret is not created at server
            # TODO - Fix bug in server: {} != None
            cred["secret"] = {
                "attrs": {"is_secret_modified": False, "secret_reference": None}
            }

        # Make first cred as default for now
        # TODO - get the right cred default
        # TODO - check if no creds
        bp_resources["default_credential_local_reference"] = {
            "kind": "app_credential",
            "name": creds[0]["name"],
        }

        upload_payload = self._make_blueprint_payload(bp_name, bp_desc, bp_resources)

        res, err = self.upload(upload_payload)

        if err:
            return res, err

        # Add secrets and update bp
        bp = res.json()
        del bp["status"]

        # Add secrets back
        creds = bp["spec"]["resources"]["credential_definition_list"]
        for cred in creds:
            name = cred["name"]
            cred["secret"] = secret_map[name]

        # Update blueprint
        update_payload = bp
        uuid = bp["metadata"]["uuid"]

        return self.update(uuid, update_payload)
