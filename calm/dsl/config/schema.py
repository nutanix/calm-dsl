from schema import Schema, And, Use, SchemaError, Optional


config_schema_dict = {
    Optional("SERVER"): {
        Optional("pc_ip"): And(Use(str)),
        Optional("pc_port"): And(Use(str)),
        Optional("pc_username"): And(Use(str)),
        Optional("pc_password"): And(Use(str)),
    },
    Optional("PROJECT"): {Optional("name"): And(Use(str))},
    Optional("LOG"): {Optional("level"): And(Use(str))},
    Optional("CATEGORIES"): {},
}


init_schema_dict = {
    Optional("DB"): {Optional("location"): And(Use(str))},  # NoQA
    Optional("LOCAL_DIR"): {Optional("location"): And(Use(str))},  # NoQA
    Optional("CONFIG"): {Optional("location"): And(Use(str))},  # NoQA
}


def validate_config(config):
    """validates the config schema"""

    return validate_schema(config, config_schema_dict)


def validate_init_config(config):
    """valdiates the init schema"""

    return validate_schema(config, init_schema_dict)


def validate_schema(config, schema_dict):
    """validates the config with the schema dict"""

    config_schema = Schema(schema_dict)
    config_dict = {s: dict(config.items(s)) for s in config.sections()}
    try:
        config_schema.validate(config_dict)
        return True
    except SchemaError:
        return False
