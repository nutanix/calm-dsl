import pytest

from calm.dsl.api.api_connectivity_details_resolver import (
    APIOwnerResolver,
    APIConnectivityDetailsResolver,
)
from calm.dsl.constants import RESOURCE
from calm.dsl.api.connection import (
    Connection,
    NCMultiConnection,
    MultiConnection,
    build_url,
)


API_RESOURCE_PATH_OWNER_PARAMS = [
    ("categories/AppFamily", RESOURCE.API_TYPE.PC_API),
    ("categories/AppFamily/123", RESOURCE.API_TYPE.PC_API),
    ("users", RESOURCE.API_TYPE.IAM_AUTHN_API),
    ("users_groups/123", RESOURCE.API_TYPE.IAM_AUTHN_API),
    ("roles", RESOURCE.API_TYPE.IAM_AUTHZ_API),
    ("roles/list", RESOURCE.API_TYPE.IAM_AUTHZ_API),
    ("roles/uuid-example", RESOURCE.API_TYPE.IAM_AUTHZ_API),
    ("roles/uuid-example", RESOURCE.API_TYPE.IAM_AUTHZ_API),
    ("blueprints/123", RESOURCE.API_TYPE.CALM_API),
    ("runbooks", RESOURCE.API_TYPE.CALM_API),
    ("features/approval_policy", RESOURCE.API_TYPE.CALM_API),
    ("features/policy", RESOURCE.API_TYPE.DM_API),
    ("projects_internal/<uuid>", RESOURCE.API_TYPE.DM_API),
    ("dm/v3/groups", RESOURCE.API_TYPE.DM_API),
]


class TestAPIOwnerResolver:
    """
    Test cases for APIOwnerResolver class.
    """

    def setup_method(self):
        self._api_owner_resolver = APIOwnerResolver()

    @pytest.mark.parametrize(
        "resource_path, expected_owner", API_RESOURCE_PATH_OWNER_PARAMS
    )
    def test_resolve(self, resource_path, expected_owner):
        """
        Tests the API owner resolve method with various inputs.
        """
        owner = self._api_owner_resolver.resolve(resource_path)
        assert owner == expected_owner, f"Expected {expected_owner}, got {owner}"

    def test_resolve_invalid_resource_path(self):
        """
        Tests the API owner resolve method with an invalid resource path.
        """
        with pytest.raises(ValueError, match="Invalid resource type 'invalid/path'"):
            self._api_owner_resolver.resolve("invalid/path")


class TestAPIConnectivityDetailsResolver:
    """
    Test cases for API connectivity details resolver.
    """

    def setup_method(self):
        self._api_connectivity_details_resolver = APIConnectivityDetailsResolver()

    def test_resolve_api_details_multiowned_resource(self):
        """
        Tests the API connectivity details resolver with a multi-owned resource.
        """
        connection = Connection(host="test.host", port=443)
        resource_type = "test-resource"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection, resource_type=resource_type, multi_owned=True
        )

        assert connectivity_details.connection == connection, "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/nutanix/v3/test-resource"
        ), "API path mismatch"

    def test_resolve_api_details_ncm_not_enabled(self):
        """
        Tests the API connectivity details resolver when NCM is not enabled.
        """
        connection = Connection(host="test.host", port=443)
        resource_type = "blueprints"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection, resource_type=resource_type, ncm_enabled=False
        )

        assert connectivity_details.connection == connection, "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/nutanix/v3/blueprints"
        ), "API path mismatch"

    def test_resolve_api_details_ncm_not_enabled_calm_api(self):
        """
        Tests the API connectivity details resolver when NC is not enabled for CALM API.
        """
        connection = Connection(host="test.host", port=443)
        resource_type = "apps"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection,
            resource_type=resource_type,
            ncm_enabled=False,
            determine_root_path_by_resource=True,
        )

        assert connectivity_details.connection == connection, "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/calm/v3.0/apps"
        ), "API path mismatch"

    def test_resolve_api_details_nc_enabled_pc_api(self):
        """
        Tests the API connectivity details resolver when NCM is enabled for PC API.
        """
        connection = NCMultiConnection(
            host="test.host", port=443, nc_host="test-nc-onprem.ntnx.com"
        )
        resource_type = "categories/AppFamily"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection,
            resource_type=resource_type,
            nc_enabled=True,
            ncm_enabled=True,
        )

        assert (
            connectivity_details.connection == connection.pc_connection
        ), "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/nutanix/v3/categories/AppFamily"
        ), "API path mismatch"

    def test_resolve_api_details_nc_enabled_dm_api(self):
        """
        Tests the API connectivity details resolver when NCM is enabled for DM API.
        """
        connection = NCMultiConnection(
            host="test.host", port=443, nc_host="test-nc-onprem.ntnx.com"
        )
        resource_type = "projects/123"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection,
            resource_type=resource_type,
            nc_enabled=True,
            ncm_enabled=True,
        )

        assert (
            connectivity_details.connection == connection.dm_connection
        ), "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/nutanix/v3/projects/123"
        ), "API path mismatch"

    def test_resolve_api_details_nc_enabled_calm_api(self):
        """
        Tests the API connectivity details resolver when NCM is enabled for CALM API.
        """
        connection = NCMultiConnection(
            host="test.host", port=443, nc_host="test-nc-onprem.ntnx.com"
        )
        resource_type = "blueprints/123"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection,
            resource_type=resource_type,
            nc_enabled=True,
            ncm_enabled=True,
        )

        assert (
            connectivity_details.connection == connection.ncm_connection
        ), "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/nutanix/v3/blueprints/123"
        ), "API path mismatch"

    def test_resolve_api_details_nc_enabled_iam_authn_api(self):
        """
        Tests the API connectivity details resolver when NCM is enabled for IAM authn API.
        """
        connection = NCMultiConnection(
            host="test.host", port=443, nc_host="test-nc-onprem.ntnx.com"
        )
        resource_type = "users/123"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection,
            resource_type=resource_type,
            nc_enabled=True,
            ncm_enabled=True,
        )

        assert (
            connectivity_details.connection == connection.iam_connection
        ), "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/iam/v4.0/authn/users/123"
        ), "API path mismatch"

    def test_resolve_api_details_nc_enabled_iam_authz_api(self):
        """
        Tests the API connectivity details resolver when NCM is enabled for IAM authz API.
        """
        connection = NCMultiConnection(
            host="test.host", port=443, nc_host="test-nc-onprem.ntnx.com"
        )
        resource_type = "roles/123"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=connection,
            resource_type=resource_type,
            nc_enabled=True,
            ncm_enabled=True,
        )

        assert (
            connectivity_details.connection == connection.iam_connection
        ), "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/iam/v4.0/authz/roles/123"
        ), "API path mismatch"

    def test_resolve_api_details_ncm_enabled(self):
        """
        Tests the API connectivity details resolver when NCM is enabled for CALM and DM API.
        """
        multi_connection = MultiConnection()
        pc_connection = Connection(host="test.host", port=443)
        ncm_connection = Connection(host="ncm.test.host", port=443)
        setattr(multi_connection, "pc_connection", pc_connection)
        setattr(multi_connection, "ncm_connection", ncm_connection)
        resource_type = "blueprints/123"

        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=multi_connection,
            resource_type=resource_type,
            ncm_enabled=True,
        )

        assert (
            connectivity_details.connection == multi_connection.get_ncm_object()
        ), "Connection mismatch"
        assert (
            connectivity_details.api_path == "api/nutanix/v3/blueprints/123"
        ), "API path mismatch"

        resource_type = "dm/v3/groups"
        connectivity_details = self._api_connectivity_details_resolver.resolve(
            connection=multi_connection,
            resource_type=resource_type,
            ncm_enabled=True,
        )

        assert (
            connectivity_details.connection == multi_connection.get_pc_object()
        ), "Connection mismatch"
        assert connectivity_details.api_path == "dm/v3/groups", "API path mismatch"

    @pytest.mark.parametrize(
        "resource_type",
        ["internal/healthz", "multidomain"],
    )
    def test_get_api_path_nc_api_empty_prefix(self, resource_type):
        """
        NC_API uses an empty prefix; the path must not gain a leading slash
        (build_url would otherwise produce //resource).
        """
        api_path = self._api_connectivity_details_resolver._get_api_path(
            RESOURCE.API_TYPE.NC_API, resource_type
        )
        assert api_path == resource_type
        assert not api_path.startswith("/")
        url = build_url("nc.example", 443, endpoint=api_path)
        assert f"/{resource_type}" in url
        assert f"//{resource_type}" not in url
