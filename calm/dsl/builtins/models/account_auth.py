from .utils import is_compile_secrets


class AccountAuth:
    class K8s:
        def __new__(cls, username="", password=""):
            return cls.basic(username, password)

        def basic(username="", password=""):
            auth_dict = {
                "type": "basic",
                "username": username,
                "password": {
                    "attrs": {"is_secret_modified": True},
                    "value": password if is_compile_secrets() else "",
                },
            }

            return auth_dict

        def client_certificate(client_certificate="", client_key=""):
            auth_dict = {
                "type": "client_certificate",
                "client_certificate": {
                    "attrs": {"is_secret_modified": True},
                    "value": client_certificate if is_compile_secrets() else "",
                },
                "client_key": {
                    "attrs": {"is_secret_modified": True},
                    "value": client_key if is_compile_secrets() else "",
                },
            }

            return auth_dict

        def ca_certificate(ca_certificate="", client_certificate="", client_key=""):
            auth_dict = {
                "type": "ca_certificate",
                "ca_certificate": {
                    "attrs": {"is_secret_modified": True},
                    "value": ca_certificate if is_compile_secrets() else "",
                },
                "client_certificate": {
                    "attrs": {"is_secret_modified": True},
                    "value": client_certificate if is_compile_secrets() else "",
                },
                "client_key": {
                    "attrs": {"is_secret_modified": True},
                    "value": client_key if is_compile_secrets() else "",
                },
            }

            return auth_dict

        def service_account(ca_certificate="", token=""):
            auth_dict = {
                "type": "service_account",
                "token": {
                    "attrs": {"is_secret_modified": True},
                    "value": token if is_compile_secrets() else "",
                },
                "ca_certificate": {
                    "attrs": {"is_secret_modified": True},
                    "value": ca_certificate if is_compile_secrets() else "",
                },
            }

            return auth_dict
