# -*- coding: utf-8 -*-
"""
connection: Provides a HTTP client to make requests to calm

Example:

pc_ip = "<pc_ip>"
pc_port = 9440
client = get_connection(pc_ip, pc_port,
                        auth=("admin", "***REMOVED***"))

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


class Connection:
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
