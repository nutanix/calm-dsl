import os
import configparser
from jinja2 import Environment, PackageLoader

from .schema import validate_init_config
from .utils import make_file_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class InitConfig:

    _INIT_FILE_LOCATION = os.path.join(os.path.expanduser("~"), ".calm", "init.ini")

    @classmethod
    def get_init_data(cls):

        init_file = cls._INIT_FILE_LOCATION
        if not os.path.exists(init_file):
            raise FileNotFoundError(
                "'{}' not found. Please run: calm init dsl".format(init_file)
            )

        init_config = configparser.ConfigParser()
        init_config.optionxform = str
        init_config.read(init_file)

        # Validate init config
        if not validate_init_config(init_config):
            raise ValueError(
                "Invalid init config file: {}. Please run: calm init dsl".format(
                    init_file
                )
            )

        return init_config

    @classmethod
    def update_init_config(cls, config_file, db_file, local_dir):
        """updates the init file data"""

        # create required directories
        make_file_dir(config_file)
        make_file_dir(db_file)
        make_file_dir(local_dir, is_dir=True)

        # Note: No need to validate init data as it is rendered by template
        init_file = cls._INIT_FILE_LOCATION
        make_file_dir(init_file)

        LOG.debug("Rendering init template")
        text = cls._render_init_template(config_file, db_file, local_dir)

        # Write init configuration
        LOG.debug("Writing configuration to '{}'".format(init_file))
        with open(init_file, "w") as fd:
            fd.write(text)

    @staticmethod
    def _render_init_template(
        config_file, db_file, local_dir, schema_file="init.ini.jinja2"
    ):
        """renders the init template"""

        loader = PackageLoader(__name__, "")
        env = Environment(loader=loader)
        template = env.get_template(schema_file)
        text = template.render(
            config_file=config_file, db_file=db_file, local_dir=local_dir
        )
        return text.strip() + os.linesep
