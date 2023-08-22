from .resource import ResourceAPI
from .connection import REQUEST


class ResourceTypeAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="resource_types", calm_api=True)
        self.CREATE = self.PREFIX
        self.TEST_RUNBOOK = self.PREFIX + "/{}/test_runbook/{}/run"
        self.PLATFORM_LIST = self.PREFIX + "/platform_list"
        self.UPDATE = self.PREFIX + "/{}"

    def create(self, resource_type_payload):
        return self.connection._call(
            self.CREATE,
            verify=False,
            request_json=resource_type_payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )

    def update(self, uuid, resource_type_payload):
        return self.connection._call(
            self.UPDATE.format(uuid),
            verify=False,
            request_json=resource_type_payload,
            method=REQUEST.METHOD.PUT,
        )

    def run_test_runbook(self, resource_type_id, action_id, payload):
        return self.connection._call(
            self.TEST_RUNBOOK.format(resource_type_id, action_id),
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
        )

    def get_platform_list(
        self, resource_type, account_id, args=None, outargs=None, action=None
    ):
        """get platform data based on attributes given
        Args:
            resource_type (string): name of resource type
            acccount_id (string): uuid of account
            args ([dict]): array of dict -> {
                "name": (string),
                "value: (string),
                } which accepts filter name and value in given form
            outargs ([string]): keys for which platform data has to be provided.
            action: (string) name of the list action
        Returns:
            dict:
        """
        payload = {"resource_type_name": resource_type, "account_uuid": account_id}

        if args:
            payload["args"] = args

        if outargs:
            payload["outargs"] = outargs

        if action:
            payload["action_name"] = action

        return self.connection._call(
            self.PLATFORM_LIST,
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
            timeout=(5, 60),
        )
