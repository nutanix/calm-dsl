"""Macro detection + AHV allowlist enforcement for calm-dsl.

Mirrors the server regex ``^@@{[^}]+}@@$`` so compile/decompile/save
paths share one definition of what counts as a Calm macro expression.
"""

import re
import sys

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Full-string Calm macro regex; anything else (prefix/suffix text,
# non-strings, UUIDs) is treated as a literal by the DSL.
MACRO_PATTERN = re.compile(r"^@@\{[^}]+\}@@$")


def is_macro(val):
    """True iff *val* is a string that is ENTIRELY a @@{...}@@ macro.

    Type-safe: returns False for any non-string input.
    """
    if not isinstance(val, str):
        return False
    return bool(MACRO_PATTERN.match(val))


def has_macro(val):
    """True if *val* is, or recursively contains, a Calm macro expression.

    Recurses into lists/dicts because AHV substrate fields are
    collection-typed (``nic_list``, ``data_source_reference``, etc.).
    """
    if isinstance(val, str):
        return bool(MACRO_PATTERN.match(val))

    if isinstance(val, list):
        return any(has_macro(item) for item in val)

    if isinstance(val, dict):
        return any(has_macro(v) for v in val.values())

    return False


def validate_ahv_macro_fields(cdict, entity, flow="compile"):
    """Reject macros on AHV fields not in ``AHV_MACRO_FIELDS.BY_ENTITY``.

    Raises ``sys.exit`` with a clear message instead of letting a
    misplaced macro crash downstream arithmetic or schema validation.
    """
    from calm.dsl.constants import AHV_MACRO_FIELDS, MACRO_SUPPORT_AHV_SPEC_MIN_VERSION

    if not isinstance(cdict, dict) or not cdict:
        return
    if entity not in AHV_MACRO_FIELDS.BY_ENTITY:
        return

    allow_map = AHV_MACRO_FIELDS.BY_ENTITY[entity]
    for k, v in cdict.items():
        if k in allow_map or not has_macro(v):
            continue
        allowed = ", ".join(
            "{} [{}]".format(name, dtype) for name, dtype in sorted(allow_map.items())
        )
        LOG.error(
            "AHV %s %s: macro on unsupported field %r. " "Allowed (Calm %s): %s",
            entity,
            flow,
            k,
            MACRO_SUPPORT_AHV_SPEC_MIN_VERSION,
            allowed,
        )
        sys.exit(
            "Macro not supported on field '{}' for {} ({}). "
            "Allowed: {}".format(k, entity, flow, sorted(allow_map) or "<none>")
        )
