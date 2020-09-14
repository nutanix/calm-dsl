from .main import (
    get,
    describe,
    launch,
    publish,
    approve,
    update,
    delete,
    reject,
    unpublish,
    decompile,
)
from .utils import FeatureFlagGroup


# Marketplace Commands


@get.group("marketplace", cls=FeatureFlagGroup)
def marketplace_get():
    """Get marketplace entities"""
    pass


@describe.group("marketplace", cls=FeatureFlagGroup)
def marketplace_describe():
    """Describe marketplace entities"""
    pass


@launch.group("marketplace", cls=FeatureFlagGroup)
def marketplace_launch():
    """Launch marketplace entities"""
    pass


@decompile.group("marketplace", cls=FeatureFlagGroup)
def marketplace_decompile():
    """Decompile marketplace entities"""
    pass


@approve.group("marketplace", cls=FeatureFlagGroup)
def marketplace_approve():
    """Approve marketplace entities"""
    pass


@publish.group("marketplace", cls=FeatureFlagGroup)
def marketplace_publish():
    """Publish marketplace entities"""
    pass


@update.group("marketplace", cls=FeatureFlagGroup)
def marketplace_update():
    """Update marketplace entities"""
    pass


@delete.group("marketplace", cls=FeatureFlagGroup)
def marketplace_delete():
    """Delete marketplace entities"""
    pass


@reject.group("marketplace", cls=FeatureFlagGroup)
def marketplace_reject():
    """Reject marketplace entities"""
    pass


@unpublish.group("marketplace", cls=FeatureFlagGroup)
def marketplace_unpublish():
    """Unpublish marketplace entities"""
    pass
