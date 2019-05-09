# -*- coding: utf-8 -*-
"""
server_interface: Provides a HTTP client to make requests to calm

Example:

pc_ip = "<pc_ip>"
pc_port = 9440
client = get_bp_api_handle(pc_ip, pc_port,
                           auth=("admin", "***REMOVED***"))

res, err = client.list()

"""

import traceback
import logging
import json
import urllib3

from requests import Session as NonRetrySession
from requests.adapters import HTTPAdapter


urllib3.disable_warnings()
log = logging.getLogger(__name__)


class REQUEST:
    """Request related constants"""

    class SCHEME:
        """
        Connection schemes
        """

        HTTP = "http"
        HTTPS = "https"

    class AUTH_TYPE:
        """
        Types of auth
        """

        NONE = "none"
        BASIC = "basic"
        JWT = "jwt"

    class METHOD:
        """
        Request methods
        """

        DELETE = "delete"
        GET = "get"
        POST = "post"
        PUT = "put"


def build_url(host, port, endpoint="", scheme=REQUEST.SCHEME.HTTPS):
    """Build url.

    Args:
        host (str): hostname/ip
        port (int): port of the service
        endpoint (str): url endpoint
        scheme (str): http/https/tcp/udp
    Returns:
    Raises:
    """
    url = "{scheme}://{host}".format(scheme=scheme, host=host)
    if port is not None:
        url += ":{port}".format(port=port)
    url += "/{endpoint}".format(endpoint=endpoint)
    return url


class Connection(object):
    def __init__(
        self,
        host,
        port,
        auth_type,
        scheme=REQUEST.SCHEME.HTTPS,
        auth=None,
        pool_maxsize=20,
        pool_connections=20,
        pool_block=True,
        base_url="",
        response_processor=None,
        session_headers=None,
        retries_enabled=False,
        **kwargs
    ):
        """Generic client to connect to server.

        Args:
            host (str): Hostname/IP address
            port (int): Port to connect to
            pool_maxsize (int): The maximum number of connections in the pool
            pool_connections (int): The number of urllib3 connection pools
                                    to cache
            pool_block (bool): Whether the connection pool should block
                               for connections
            base_url (str): Base URL
            scheme (str): http scheme (http or https)
            response_processor (dict): response processor dict
            session_headers (dict): session headers dict
            auth_type (str): auth type that needs to be used by the client
            auth (tuple): authentication
            retries_enabled (bool): Flag to perform retries (default: false)
        Returns:
        Raises:
        """
        self.base_url = base_url
        self.host = host
        self.port = port
        self.session_headers = session_headers or {}
        self._pool_maxsize = pool_maxsize
        self._pool_connections = pool_connections
        self._pool_block = pool_block
        self.session = None
        self.auth = auth
        self.scheme = scheme
        self.auth_type = auth_type
        self.response_processor = response_processor
        self.retries_enabled = retries_enabled

    def connect(self):
        """Connect to api server, create http session pool.

        Args:
        Returns:
            api server session
        Raises:
        """

        # TODO: Add retries
        # if self.retries_enabled:
        #     self.session = RetrySession()
        # else:
        self.session = NonRetrySession()
        if self.auth and self.auth_type == REQUEST.AUTH_TYPE.BASIC:
            self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})

        http_adapter = HTTPAdapter(
            pool_block=bool(self._pool_block),
            pool_connections=int(self._pool_connections),
            pool_maxsize=int(self._pool_maxsize),
        )
        self.session.mount("http://", http_adapter)
        self.session.mount("https://", http_adapter)
        self.base_url = build_url(self.host, self.port, scheme=self.scheme)
        log.info("{} session created".format(self.__class__.__name__))
        return self.session

    def close(self):
        """
        Close the session.

        Args:
            None
        Returns:
            None
        """
        self.session.close()

    def _call(
        self,
        endpoint,
        method=REQUEST.METHOD.POST,
        cookies=None,
        request_json=None,
        request_params=None,
        verify=True,
    ):
        """Private method for making http request to calm

        Args:
            endpoint (str): calm server endpoint
            method (str): calm server http method
            cookies (dict): cookies that need to be forwarded.
            request_json (dict): request data
            request_params (dict): request params
        Returns:
            (tuple (requests.Response, dict)): Response
        """
        if request_params is None:
            request_params = {}

        request_json = request_json or {}
        log.info(
            """Server Request- '{method}' at '{endpoint}' with body:
            '{body}'""".format(
                method=method, endpoint=endpoint, body=request_json
            )
        )
        res = None
        err = None
        try:
            res = None
            url = build_url(self.host, self.port, endpoint=endpoint, scheme=self.scheme)
            log.info("URL is: {}".format(url))
            base_headers = self.session.headers

            if method == REQUEST.METHOD.POST:
                res = self.session.post(
                    url,
                    params=request_params,
                    data=json.dumps(request_json),
                    verify=verify,
                    headers=base_headers,
                    cookies=cookies,
                )
            elif method == REQUEST.METHOD.PUT:
                res = self.session.put(
                    url,
                    params=request_params,
                    data=json.dumps(request_json),
                    verify=verify,
                    headers=base_headers,
                    cookies=cookies,
                )
            elif method == REQUEST.METHOD.GET:
                res = self.session.get(
                    url,
                    params=request_params or request_json,
                    verify=verify,
                    headers=base_headers,
                    cookies=cookies,
                )
            elif method == REQUEST.METHOD.DELETE:
                res = self.session.delete(
                    url,
                    params=request_params,
                    data=json.dumps(request_json),
                    verify=verify,
                    headers=base_headers,
                    cookies=cookies,
                )
            res.raise_for_status()
            log.info("Server Response: {}".format(res.json()))
        except Exception as ex:
            log.error("Got the traceback\n{}".format(traceback.format_exc()))
            err_msg = res.text if hasattr(res, "text") else "{}".format(ex)
            status_code = res.status_code if hasattr(res, "status_code") else 500
            err = {"error": err_msg, "code": status_code}
            log.error("Error Response: {}".format(err))
        return res, err


_CONNECTION = None


def get_connection(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """Get api server (aplos/styx) handle.

    Args:
        host (str): Hostname/IP address
        port (int): Port to connect to
        auth_type (str): auth type that needs to be used by the client
        scheme (str): http scheme (http or https)
        session_headers (dict): session headers dict
        auth (tuple): authentication
    Returns:
        Client handle
    Raises:
        Exception: If cannot connect
    """
    global _CONNECTION
    if not _CONNECTION:
        _CONNECTION = Connection(host, port, auth_type, scheme=scheme, auth=auth)
    return _CONNECTION


class BlueprintAPI:

    _PREFIX = "api/nutanix/v3/"
    BP_PREFIX = _PREFIX + "blueprints"
    LIST = BP_PREFIX + "/list"
    UPLOAD = BP_PREFIX + "/import_json"
    ITEM = BP_PREFIX + "/{}"
    LAUNCH = ITEM + "/simple_launch"
    FULL_LAUNCH = ITEM + "/launch"
    LAUNCH_POLL = ITEM + "/pending_launches/{}"
    APP_PREFIX = _PREFIX + "apps"
    APP_LIST = APP_PREFIX + "/list"
    APP_ITEM = APP_PREFIX + "/{}"
    ACTION_RUN = APP_PREFIX + "/{}/actions/{}/run"
    BP_EDITABLES = BP_PREFIX + "/{}/runtime_editables"

    def __init__(self, connection):
        self.connection = connection

    def list(self, params=None):
        return self.connection._call(
            BlueprintAPI.LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def get(self, blueprint_id):
        return self.connection._call(
            BlueprintAPI.ITEM.format(blueprint_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def update(self, uuid, payload):
        return self.connection._call(
            BlueprintAPI.ITEM.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.PUT,
        )

    def upload(self, payload):
        return self.connection._call(
            BlueprintAPI.UPLOAD,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def delete(self, uuid):
        return self.connection._call(
            BlueprintAPI.ITEM.format(uuid), verify=False, method=REQUEST.METHOD.DELETE
        )

    def launch(self, uuid, payload):
        return self.connection._call(
            BlueprintAPI.LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def full_launch(self, uuid, payload):
        return self.connection._call(
            BlueprintAPI.FULL_LAUNCH.format(uuid),
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def poll_launch(self, blueprint_id, request_id):
        return self.connection._call(
            BlueprintAPI.LAUNCH_POLL.format(blueprint_id, request_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def list_apps(self, params=None):
        return self.connection._call(
            BlueprintAPI.APP_LIST,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
        )

    def get_app(self, app_id):
        return self.connection._call(
            BlueprintAPI.APP_ITEM.format(app_id),
            verify=False,
            method=REQUEST.METHOD.GET,
        )

    def run_action(self, app_id, action_id, payload):
        return self.connection._call(
            BlueprintAPI.ACTION_RUN.format(app_id, action_id),
            request_json=payload,
            verify=False,
            method=REQUEST.METHOD.POST,
        )

    def poll_action_run(self, poll_url, payload=None):
        if payload:
            return self.connection._call(
                poll_url, request_json=payload, verify=False, method=REQUEST.METHOD.POST
            )
        else:
            return self.connection._call(
                poll_url, verify=False, method=REQUEST.METHOD.GET
            )

    def delete_app(self, app_id, soft_delete=False):
        delete_url = BlueprintAPI.APP_ITEM.format(app_id)
        if soft_delete:
            delete_url += "?type=soft"
        return self.connection._call(
            delete_url, verify=False, method=REQUEST.METHOD.DELETE
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

    def upload_with_secrets(self, bp, bp_name=None):

        bp_resources = json.loads(bp.json_dumps())

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

        upload_payload = self._make_blueprint_payload(
            bp_name or bp.__name__, bp.__doc__, bp_resources
        )

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

    def _get_editables(self, bp_uuid):
        return self.connection._call(
            BlueprintAPI.BP_EDITABLES.format(bp_uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )


_BP_API_HANDLE = None


def get_blueprint_api_handle(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):

    global _BP_API_HANDLE
    if not _BP_API_HANDLE:
        connection = get_connection(host, port, auth_type, scheme=scheme, auth=auth)
        connection.connect()
        _BP_API_HANDLE = BlueprintAPI(connection)
    return _BP_API_HANDLE
