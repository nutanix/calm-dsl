from schema import Schema, And, Use, SchemaError


config_schema_dict = {
    "SERVER": {
        "pc_ip": And(Use(str)),
        "pc_port": And(Use(str)),
        "pc_username": And(Use(str)),
        "pc_password": And(Use(str)),
    },
    "PROJECT": {"name": And(Use(str))},
    "LOG": {"level": And(Use(str))},
    "CATEGORIES": {},
}


init_schema_dict = {
    "DB": {"location": And(Use(str)), },
    "LOCAL_DIR": {"location": And(Use(str)), },
    "CONFIG": {"location": And(Use(str)), },
}


config_schema = Schema(config_schema_dict)


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
