from collections import OrderedDict
from io import StringIO
import json

from ruamel import yaml
from jinja2 import Environment, PackageLoader
import jsonref
from calm.dsl.tools import StrictDraft7Validator
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class ProviderBase:

    providers = OrderedDict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        provider_type = getattr(cls, "provider_type")

        if provider_type:

            # Init Provider
            cls._init()

            # Register Provider
            cls.providers[provider_type] = cls


class Provider(ProviderBase):

    provider_type = None
    spec_template_file = None
    package_name = None

    @classmethod
    def _init(cls):

        if cls.package_name is None:
            raise NotImplementedError("Package name not given")

        if cls.spec_template_file is None:
            raise NotImplementedError("Spec file not given")

        loader = PackageLoader(cls.package_name, "")
        env = Environment(loader=loader)
        template = env.get_template(cls.spec_template_file)
        tdict = yaml.safe_load(StringIO(template.render()))
        tdict = jsonref.loads(json.dumps(tdict))

        # TODO - Check if keys are present
        cls.provider_spec = tdict["components"]["schemas"]["provider_spec"]
        cls.Validator = StrictDraft7Validator(cls.provider_spec)

    @classmethod
    def get_provider_spec(cls):
        return cls.provider_spec

    @classmethod
    def get_validator(cls):
        return cls.Validator

    @classmethod
    def validate_spec(cls, spec):
        Validator = cls.get_validator()
        Validator.validate(spec)

    @classmethod
    def create_spec(cls):
        raise NotImplementedError("Create spec not implemented")

    @classmethod
    def get_api_obj(cls):
        """returns object to call provider specific apis"""

        raise NotImplementedError("Api object not implemented")

    @classmethod
    def get_runtime_editables(
        cls, runtime_spec, project_id, substrate_spec, vm_img_map={}
    ):
        # Not implemented right now
        pass


def get_provider(provider_type):

    if provider_type not in ProviderBase.providers:
        LOG.debug("Registered providers: {}".format(ProviderBase.providers))
        raise Exception("provider not registered")

    return ProviderBase.providers[provider_type]


def get_providers():
    return ProviderBase.providers


def get_provider_types():
    return ProviderBase.providers.keys()


def get_provider_interface():
    return Provider
