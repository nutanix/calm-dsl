from .resource import ResourceAPI
from .connection import REQUEST


from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class AccountsAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="accounts")
        self.VERIFY = self.PREFIX + "/{}/verify"
        self.VMS_LIST = self.ITEM + "/vms/list"
        self.RESOURCE_TYPES_LIST_BASED_ON_ACCOUNT = (
            self.PREFIX + "/{}/resource_types/list"
        )
        self.PLATFORM_SYNC = self.PREFIX + "/{}/sync"
        self.CREATE = self.PREFIX
        self.UPDATE = self.PREFIX + "/{}"

    def verify(self, id):
        return self.connection._call(
            self.VERIFY.format(id), verify=False, method=REQUEST.METHOD.GET
        )

    def vms_list(self, id, params=dict()):
        """returns the vms list for given account"""

        return self.connection._call(
            self.VMS_LIST.format(id),
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def get_uuid_type_map(self, params=dict()):
        """returns map containing {account_uuid: account_type} details"""

        res_entities, err = self.list_all(base_params=params, ignore_error=True)
        if err:
            raise Exception(err)

        uuid_type_map = {}
        for entity in res_entities:
            a_uuid = entity["metadata"]["uuid"]
            a_type = entity["status"]["resources"]["type"]
            uuid_type_map[a_uuid] = a_type

        return uuid_type_map

    def platform_sync(self, id):
        """sync platform account"""

        return self.connection._call(
            self.PLATFORM_SYNC.format(id),
            verify=False,
            method=REQUEST.METHOD.POST,
        )

    def create(self, account_name, account_payload, force_create):

        # check if account with the given name already exists
        params = {
            "filter": "name=={};state!=DELETED;child_account==True".format(account_name)
        }
        res, err = self.list(params=params)
        if err:
            return None, err

        response = res.json()
        entities = response.get("entitites", None)
        if entities:
            if len(entities) > 0:
                if not force_create:
                    err_msg = "Account {} already exists. Use --force to first delete existing account before create.".format(
                        account_name
                    )
                    err = {"error": err_msg, "code": -1}
                    return None, err

                # --force option used in create. Delete existing account with same name.
                account_uuid = entities[0]["metadata"]["uuid"]
                _, err = self.delete(account_uuid)
                if err:
                    return None, err

        return self.connection._call(
            self.CREATE,
            verify=False,
            request_json=account_payload,
            method=REQUEST.METHOD.POST,
            timeout=(5, 300),
        )

    def update(self, uuid, account_payload):
        """Updates an account with given uuid with the provided payload"""

        return self.connection._call(
            self.UPDATE.format(uuid),
            verify=False,
            request_json=account_payload,
            method=REQUEST.METHOD.PUT,
        )

    def resource_types_list(self, account_uuid):
        return self.connection._call(
            self.RESOURCE_TYPES_LIST_BASED_ON_ACCOUNT.format(account_uuid),
            verify=False,
            request_json={},
            method=REQUEST.METHOD.POST,
        )
