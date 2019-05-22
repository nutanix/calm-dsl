from .base import get_provider, get_providers, register_providers


# TODO - use init to register providers
if not get_providers():
    register_providers()


__all__ = ["get_provider"]
