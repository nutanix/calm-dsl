from calm.dsl.constants import AUTH


def k8s_basic_auth(username, password):
    return {
        "username": username,
        "password": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": password,
        },
        "type": AUTH.KUBERNETES.BASIC,
    }


def k8s_client_certificate_auth(client_key, client_certificate):
    return {
        "client_certificate": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_certificate,
        },
        "client_key": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_key,
        },
        "type": AUTH.KUBERNETES.CLIENT_CERTIFICATE,
    }


def k8s_ca_ceritificate_auth(client_key, client_certificate, ca_certificate):
    return {
        "client_certificate": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_certificate,
        },
        "client_key": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_key,
        },
        "ca_certificate": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": ca_certificate,
        },
        "type": AUTH.KUBERNETES.CA_CERTIFICATE,
    }


class Auth:
    class Kubernetes:
        basic = k8s_basic_auth
        client_certificate = k8s_client_certificate_auth
        ca_certificate = k8s_ca_ceritificate_auth
