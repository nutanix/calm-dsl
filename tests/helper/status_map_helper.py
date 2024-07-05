def remove_status_map_from_bp(known_json):
    """
    This helper function is used to remove the status_map_list from the known_json
    for versions less than 3.9.0

    Args:
        known_json (dict): The known_json dictionary

    Returns:
        None
    """
    for service in known_json["service_definition_list"]:
        for action in service["action_list"]:
            for task in action["runbook"]["task_definition_list"]:
                if "status_map_list" in task:
                    task.pop("status_map_list")

    for app_profile in known_json["app_profile_list"]:
        for action in app_profile["action_list"]:
            for task in action["runbook"]["task_definition_list"]:
                if "status_map_list" in task:
                    task.pop("status_map_list")

    for substrate in known_json["substrate_definition_list"]:
        for action in substrate["action_list"]:
            for task in action["runbook"]["task_definition_list"]:
                if "status_map_list" in task:
                    task.pop("status_map_list")

    for package in known_json["package_definition_list"]:
        if "install_runbook" in package["options"]:
            for task in package["options"]["install_runbook"]["task_definition_list"]:
                if "status_map_list" in task:
                    task.pop("status_map_list")
        if "uninstall_runbook" in package["options"]:
            for task in package["options"]["uninstall_runbook"]["task_definition_list"]:
                if "status_map_list" in task:
                    task.pop("status_map_list")
