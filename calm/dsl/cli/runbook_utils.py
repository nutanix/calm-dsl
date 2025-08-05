from distutils.version import LooseVersion as LV
from calm.dsl.store.version import Version
import click


def validate_execution_name(value):
    """Validate execution_name based on Calm version"""
    calm_version = Version.get_version("Calm")
    if value and LV(calm_version) < LV("4.3.0"):
        raise click.BadParameter(
            f"The --execution-name option is not supported in Calm versions below 4.3.0. Current version: {calm_version}"
        )
    return value
