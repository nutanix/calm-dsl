def remove_global_variables_from_spec(known_json):
    """
    This helper function is used to remove the global variables from the known_json
    for versions less than 4.3.0

    Args:
        known_json (dict): The known_json dictionary
    Returns:
        None
    """
    known_json.pop("global_variable_reference_list", None)
