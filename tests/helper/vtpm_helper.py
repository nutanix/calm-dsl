def remove_vtpm_config_from_bp_resources(known_json):
    """
    This helper function is used to remove the vtpm_config from the known_json
    for versions less than 4.2.0

    Args:
        known_json (dict): The known_json dictionary
    Returns:
        None
    """

    for substrate in known_json["resources"].get("substrate_definition_list", []):
        substrate["create_spec"]["resources"].pop("vtpm_config", None)


def remove_vtpm_config_from_bp(known_json):
    """
    This helper function is used to remove the vtpm_config from the known_json
    for versions less than 4.2.0 (Use this if the known_json does not have resources key)

    Args:
        known_json (dict): The known_json dictionary
    Returns:
        None
    """
    for substrate in known_json.get("substrate_definition_list", []):
        substrate["create_spec"]["resources"].pop("vtpm_config", None)
