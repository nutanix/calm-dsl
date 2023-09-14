from calm.dsl.constants import CACHE


class MockConstants:
    CACHE_FILE_NAME = "cache_data.json"
    TEST_CONFIG_FILE_NAME = "config_test.json"


CONSTANT_ENTITIES = [
    CACHE.ENTITY.USER,
    CACHE.ENTITY.ROLE,
    CACHE.ENTITY.DIRECTORY_SERVICE,
    CACHE.ENTITY.USER_GROUP,
    CACHE.ENTITY.AHV_NETWORK_FUNCTION_CHAIN,
    CACHE.ENTITY.POLICY_EVENT,
    CACHE.ENTITY.POLICY_ACTION_TYPE,
    CACHE.ENTITY.POLICY_ATTRIBUTES,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.DATABASE,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.PROFILE,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SLA,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.CLUSTER,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TIME_MACHINE,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SNAPSHOT,
    CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.TAG,
]

PROJECTS = [
    "default",
    "test_snapshot_policy_project",
    "test_vmw_snapshot_policy_project",
    "rbac_bp_test_project",
    "test_approval_policy",
    "test_approval_policy_rbac",
    "test_quota_project",
    "test_dyn_cred_project",
    "test_vpc_project",
]

PROVIDERS = ["AzureVault_Cred_Provider", "HashiCorpVault_Cred_Provider", "NDB"]

SERIALISED_KEYS = [
    "data",
    "auth_schema_list",
    "tags",
    "action_list",
    "accounts_data",
    "whitelisted_subnets",
    "whitelisted_clusters",
    "whitelisted_vpcs",
    "platform_data",
    "slas",
]
