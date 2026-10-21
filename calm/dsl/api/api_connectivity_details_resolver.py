from dataclasses import dataclass
from calm.dsl.api.connection import Connection, MultiConnection, NCMultiConnection
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import RESOURCE
from calm.dsl.api.meta import SingletonMeta

import sys

LOG = get_logging_handle(__name__)


@dataclass
class APIConnectivityDetails:
    """
    Holds the API connectivity details needed to contact the API of interest.
    """

    connection: Connection
    # e.g. /api/nutanix/v3/blueprints, /dm/v3/groups
    api_path: str = None


class APIConnectivityDetailsResolver(metaclass=SingletonMeta):
    """
    Responsible for resolving the API connectivity details based on the resource type and connection.
    """

    # NCM 1.5 API components specific to PC and NCM.
    _NCM_V15_PC_COMPONENTS = {
        RESOURCE.API_TYPE.PC_API,
        RESOURCE.API_TYPE.DM_API,
        RESOURCE.API_TYPE.IAM_AUTHN_API,
        RESOURCE.API_TYPE.IAM_AUTHZ_API,
    }

    _NCM_V15_NCM_COMPONENTS = {RESOURCE.API_TYPE.CALM_API}

    # NCM 2.0+ API components
    # NCM 2.0+ supports multiple subdomains in NC, so we need
    # to differentiate between PC and NC components.
    _NCM_V20_PC_COMPONENTS = {
        RESOURCE.API_TYPE.PC_API,
    }
    _NCM_V20_NC_COMPONENTS = {
        RESOURCE.API_TYPE.CALM_API,
        RESOURCE.API_TYPE.NC_API,
        RESOURCE.API_TYPE.DM_API,
        RESOURCE.API_TYPE.IAM_AUTHN_API,
        RESOURCE.API_TYPE.IAM_AUTHZ_API,
    }

    _API_TYPES_PREFIXES = {
        RESOURCE.API_TYPE.PC_API: RESOURCE.API_PREFIX.V3_API_PATH_PREFIX,
        RESOURCE.API_TYPE.DM_API: RESOURCE.API_PREFIX.V3_API_PATH_PREFIX,
        RESOURCE.API_TYPE.IAM_AUTHN_API: RESOURCE.API_PREFIX.IAM_V4_API_AUTHN_PATH_PREFIX,
        RESOURCE.API_TYPE.IAM_AUTHZ_API: RESOURCE.API_PREFIX.IAM_V4_API_AUTHZ_PATH_PREFIX,
        RESOURCE.API_TYPE.CALM_API: RESOURCE.API_PREFIX.V3_API_PATH_PREFIX,
        RESOURCE.API_TYPE.NC_API: "",
    }

    # specific API path prefixes for DM and CALM APIs
    _API_TYPE_PATH_PREFIXES = {
        RESOURCE.API_TYPE.DM_API: RESOURCE.API_PREFIX.DM_API_PATH_PREFIX,
        RESOURCE.API_TYPE.CALM_API: RESOURCE.API_PREFIX.CALM_API_PATH_PREFIX,
    }

    def __init__(self):
        self._api_owner_resolver = APIOwnerResolver()

    def resolve(
        self,
        connection: Connection,
        resource_type: str,
        nc_enabled=False,
        ncm_enabled=False,
        determine_root_path_by_resource=False,
        multi_owned=False,
    ) -> APIConnectivityDetails:
        """
        Resolves the API connectivity details based on the resource type and connection.
        Args:
            connection (Connection): The connection object to use for API calls.
            resource_type (str): The type of resource for which the API connectivity details are needed.
            nc_enabled (bool): Flag indicating if NC is enabled.
            ncm_enabled (bool): Flag indicating if NCM is enabled.
            determine_root_path_by_resource (bool): If True, the path prefix is determined by the
                                                    resource type. Defaults to False.
            multi_owned (bool): Flag indicating if the resource is multi-owned, meaning the same API exists in multiple (sub)domains/components.
              Defaults to False.
        Returns:
            APIConnectivityDetails: An object containing the API connectivity details.
        """
        # TODO: we should improve this. As of now, only groups API is multi-owned, but
        # we can have more APIs in the future that are multi-owned and we should make this resolution more flexible.
        # For now, we return the default values for multi-owned resources.
        # This is to avoid the complexity of resolving the API connectivity details for multi-owned resources and not to change much the client code.
        if multi_owned:
            LOG.debug(
                f"Multi-owned resources type {resource_type}, the default values will be returned."
            )
            return APIConnectivityDetails(
                connection, f"{RESOURCE.API_PREFIX.V3_API_PATH_PREFIX}/{resource_type}"
            )

        LOG.debug(
            f"Resolving API connectivity details for resource type: {resource_type}, "
            f"nc_enabled: {nc_enabled}, ncm_enabled: {ncm_enabled}, "
            f"determine_root_path_by_resource: {determine_root_path_by_resource}, multi_owned: {multi_owned}"
        )
        api_type = self._api_owner_resolver.resolve(resource_type)
        api_connection = self._get_connection_by_deployment(
            connection,
            api_type,
            ncm_enabled=ncm_enabled,
            nc_enabled=nc_enabled,
        )
        api_path = self._get_api_path(
            api_type,
            resource_type,
            determine_root_path_by_resource,
        )
        return APIConnectivityDetails(api_connection, api_path)

    def _get_connection_by_deployment(
        self,
        connection,
        api_type: RESOURCE.API_TYPE,
        ncm_enabled=False,
        nc_enabled=False,
    ) -> Connection:
        """
        Resolves the connection based on the deployment type.
        Args:
            connection (Connection): The connection object to use for API calls.
            ncm_enabled (bool): Flag indicating if NCM is enabled.
            nc_enabled (bool): Flag indicating if NC is enabled.
        Returns:
            Connection: The resolved connection object.
        """
        if not ncm_enabled:
            LOG.debug("Resolving the API connectivity details...")
            return self._get_pc_connection(connection)

        if nc_enabled:
            LOG.debug("Resolving the NC connectivity details...")
            # use the NCM 2.0+ mapping
            if api_type in self._NCM_V20_PC_COMPONENTS:
                return self._get_pc_connection(connection)

            # NCM 2.0+ supports multiple subdomains in NC
            elif api_type in self._NCM_V20_NC_COMPONENTS:
                return self._get_nc_subdomain_connection(connection, api_type)

            else:
                err_message = f"Invalid API type '{api_type.name}' for NCM 2.0+"
                LOG.error(err_message)
                sys.exit(err_message)
        else:
            # use the NCM 1.5 mapping
            if api_type in self._NCM_V15_PC_COMPONENTS:
                LOG.debug("Resolving the PC connectivity details...")
                return self._get_pc_connection(connection)

            elif api_type in self._NCM_V15_NCM_COMPONENTS:
                LOG.debug("Resolving the NCM connectivity details...")
                return self._get_ncm_connection(connection)

            else:
                err_message = f"Invalid API type '{api_type.name}' for NCM"
                LOG.warning(err_message)
                return None

    def _get_api_path(
        self,
        api_type: RESOURCE.API_TYPE,
        resource_type: str,
        determine_root_path_by_resource=False,
    ):
        """
        Determines the API path root based on the API type and resource type.
        Args:
            api_path (str): The base API path.
            api_type (RESOURCE.API_TYPE): The type of API.
            resource_type (str): The type of resource.
            determine_root_path_by_resource (bool): If True, the path prefix is determined by the
                                                    resource. Defaults to False.
        Returns:
            str: The complete API path
        """
        LOG.debug(
            f"Creating API path for resource type: {resource_type}, API type: {api_type.name}, "
            f"determine_root_path_by_resource: {determine_root_path_by_resource}"
        )
        # if the resource type is in the predefined set of APIs without a prefix,
        # return it as is
        if resource_type in RESOURCE.APIS_WITHOUT_PREFIX:
            return resource_type

        # if the resource type is in the predefined set of APIs with a prefix,
        # return it with the prefix
        if determine_root_path_by_resource:
            root_path = self._API_TYPE_PATH_PREFIXES.get(
                api_type, RESOURCE.API_PREFIX.V3_API_PATH_PREFIX
            )
        else:
            root_path = self._API_TYPES_PREFIXES.get(
                api_type, RESOURCE.API_PREFIX.V3_API_PATH_PREFIX
            )

        if not root_path:
            return resource_type
        return f"{root_path}/{resource_type}"

    def _get_pc_connection(self, connection) -> Connection:
        """
        Resolves the PC connection from the provided connection object.
        """
        if isinstance(connection, Connection):
            return connection
        elif isinstance(connection, MultiConnection):
            return connection.get_pc_object()
        elif isinstance(connection, NCMultiConnection):
            return connection.pc_connection
        else:
            LOG.error("Invalid connection type")
            raise TypeError(
                "Resolution requires Connection or Multiconnection types..."
            )

    def _get_ncm_connection(self, connection) -> Connection:
        """
        Resolves the NCM connection from the provided connection object.
        """
        if isinstance(connection, Connection):
            return connection
        elif isinstance(connection, MultiConnection):
            return connection.get_ncm_object()
        elif isinstance(connection, NCMultiConnection):
            return connection.ncm_connection
        else:
            LOG.error("Invalid connection type")
            raise TypeError(
                "Resolution requires Connection or Multiconnection types..."
            )

    def _get_nc_subdomain_connection(
        self, connection: NCMultiConnection, api_type: RESOURCE.API_TYPE
    ) -> Connection:
        """
        Resolves the NC subdomain connection from the provided connection object.
        """
        subdomain_connection = connection.get_connection_by_api_type(api_type)
        if not subdomain_connection:
            raise ValueError(
                f"Unable to retrieve the NC subdomain connection for the API type {api_type.name}"
            )

        return subdomain_connection


class APIOwnerResolver:
    """
    Resolves the API owner based on the resource path/type. Contains mostly static methods.
    Still used as a regular class if we decide to define more flexible mappings in the future (e.g. with multi-owning APIs).
    """

    API_OWNER_TYPES = {
        RESOURCE.API_TYPE.PC_API: RESOURCE.PC,
        RESOURCE.API_TYPE.NC_API: RESOURCE.NC,
        RESOURCE.API_TYPE.DM_API: RESOURCE.DM,
        RESOURCE.API_TYPE.IAM_AUTHN_API: RESOURCE.IAM_AUTHN,
        RESOURCE.API_TYPE.IAM_AUTHZ_API: RESOURCE.IAM_AUTHZ,
        RESOURCE.API_TYPE.CALM_API: RESOURCE.CALM,
    }

    def resolve(self, resource_path) -> RESOURCE.API_TYPE:
        """
        Resolves the API owner based on the resource path/type.
        Args:
            resource_path (str): The resource type for which the API owner is to be resolved.
        Returns:
            RESOURCE.API_TYPE: The API type that owns the resource.
        Raises:path/
            ValueError: If the resource type does not belong to any of the API owners.
        """
        LOG.debug(f"Resolving API owner for resource type: {resource_path}")
        # first check for exact match
        for owner in self.API_OWNER_TYPES:
            if self._is_resource_owner_exact_match(owner, resource_path):
                return owner

        # if no exact match, check for subpath match
        for owner in self.API_OWNER_TYPES:
            if self._is_resource_owner_subpath_match(owner, resource_path):
                return owner

        err_message = f"Invalid resource type '{resource_path}'"
        LOG.error(err_message)
        raise ValueError(err_message)

    def _is_resource_owner_exact_match(
        self, owner: RESOURCE.API_TYPE, resource_path: str
    ) -> bool:
        """
        Checks if the given resource type belongs to the specified API owner.
        Args:
            owner (RESOURCE.API_TYPE): The API owner to check against.
            resource_path (str): The resource path to check.
        Returns:
            bool: True if the resource path matches the API owner's resource path,
                  False otherwise.
        """
        return resource_path in self.API_OWNER_TYPES.get(owner, set())

    def _is_resource_owner_subpath_match(
        self, owner: RESOURCE.API_TYPE, resource_path: str
    ) -> bool:
        """
        Checks if the given resource path (type) is a subpath of the specified resource path belonging to the API owner.
        Args:
            owner (RESOURCE.API_TYPE): The API owner to check against.
            resource_path (str): The resource path to check.
        Returns:
            bool: True if the resource path is a subpath of the API owner's resource path,
                  False otherwise.
        """
        return any(
            existing_resource in resource_path
            for existing_resource in self.API_OWNER_TYPES.get(owner, set())
        )
