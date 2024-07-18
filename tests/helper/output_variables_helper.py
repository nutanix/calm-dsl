def remove_output_variables_from_bp(bp_json):
    """
    This helper function is used to remove the output_variables/output_variable_list from the bp_json

    Args:
        bp_json (dict): The bp_json dictionary

    Returns:
        None
    """

    if "service_definition_list" in bp_json:
        for service_definition in bp_json["service_definition_list"]:
            for action in service_definition["action_list"]:
                action["runbook"].pop("output_variables", None)
                action["runbook"].pop("output_variable_list", None)

    if "package_definition_list" in bp_json:
        for package_definition in bp_json["package_definition_list"]:
            if "install_runbook" in package_definition["options"]:
                package_definition["options"]["install_runbook"].pop(
                    "output_variables", None
                )
                package_definition["options"]["install_runbook"].pop(
                    "output_variable_list", None
                )
            if "uninstall_runbook" in package_definition["options"]:
                package_definition["options"]["uninstall_runbook"].pop(
                    "output_variables", None
                )
                package_definition["options"]["uninstall_runbook"].pop(
                    "output_variable_list", None
                )

    if "app_profile_list" in bp_json:
        for app_profile in bp_json["app_profile_list"]:
            for action in app_profile["action_list"]:
                action["runbook"].pop("output_variables", None)
                action["runbook"].pop("output_variable_list", None)

    if "substrate_definition_list" in bp_json:
        for substrate in bp_json["substrate_definition_list"]:
            for action in substrate["action_list"]:
                action["runbook"].pop("output_variables", None)
                action["runbook"].pop("output_variable_list", None)

    if "action_list" in bp_json:
        for action in bp_json["action_list"]:
            action["runbook"].pop("output_variables", None)
            action["runbook"].pop("output_variable_list", None)
