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


config_schema = Schema(config_schema_dict)


def validate_config(config):

    config_dict = {s: dict(config.items(s)) for s in config.sections()}
    try:
        config_schema.validate(config_dict)
        return True
    except SchemaError:
        return False
