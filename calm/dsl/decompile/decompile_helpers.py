from calm.dsl.builtins.models.utils import get_valid_identifier

special_tasks_types = ["DECISION", "WHILE_LOOP"]


def process_variable_name(var_name):
    """
    Args:
        var_name (str): variable name which needs processing
    Returns: processed variable name
    """

    return get_valid_identifier(var_name)


class IndentHelper:
    def generate_indents(
        self, special_tasks_data, task, base_indent, depth, if_needed, else_needed
    ):
        """
        generates indents for special task types, like decision, and while loop
        Args:
            task (obj): task object
        Returns:
            list containing indent info which can be consumed by various indent helpers
        """
        helper = None

        if task.type == "DECISION":
            helper = DecisionTaskIndentHelper()
        elif task.type == "WHILE_LOOP":
            helper = WhileTaskIndentHelper()
        if not helper:
            return []
        return helper.generate_indents(
            special_tasks_data, task.name, base_indent, depth, if_needed, else_needed
        )


class DecisionTaskIndentHelper:
    def __init__(self):
        self.output = []

    def generate_indents(
        self, special_tasks_data, curr_node, base_indent, depth, if_needed, else_needed
    ):
        """
        Args:
            decision_tasks (dict): data structure representing decision task
            curr_node (str): name of the current node
            base_indent (int): indent inherited from parent node
            depth (int): depth in the binary tree
            if_needed (bool): if block needed. first success task
            else_needed (bool): else block needed. first failure task
        Returns:
            a list containing in-order traversed nodes of the
            binary tree with indentation information
        """
        decision_tasks = special_tasks_data["decision_tasks"]
        output = self.output
        if_block_indent = None
        else_block_indent = None
        if if_needed:
            if_block_indent = base_indent - 1
        elif else_needed:
            else_block_indent = base_indent - 1
        output.append(
            {
                "task_name": curr_node,
                "with_block_indent": base_indent,
                "if_block_indent": if_block_indent,
                "else_block_indent": else_block_indent,
                "task_indent": base_indent,
                "depth": depth,
            }
        )
        ind = 0
        child_indent = base_indent + 2
        for success_task in decision_tasks[curr_node]["success_tasks"]:
            if success_task["data"].type in special_tasks_types:
                helper = IndentHelper()
                output += helper.generate_indents(
                    special_tasks_data,
                    success_task["data"],
                    child_indent,
                    depth + 1,
                    ind == 0,
                    False,
                )
            else:
                output.append(
                    {
                        "task_name": success_task["name"],
                        "with_block_indent": None,
                        "if_block_indent": base_indent + 1 if ind == 0 else None,
                        "else_block_indent": None,
                        "task_indent": child_indent,
                        "depth": depth + 1,
                    }
                )
            ind += 1

        ind = 0
        for failure_task in decision_tasks[curr_node]["failure_tasks"]:
            if failure_task["data"].type in special_tasks_types:
                helper = IndentHelper()
                output += helper.generate_indents(
                    special_tasks_data,
                    failure_task["data"],
                    child_indent,
                    depth + 1,
                    False,
                    ind == 0,
                )
            else:
                output.append(
                    {
                        "task_name": failure_task["name"],
                        "with_block_indent": None,
                        "if_block_indent": None,
                        "else_block_indent": base_indent + 1 if ind == 0 else None,
                        "task_indent": child_indent,
                        "depth": depth + 1,
                    }
                )
            ind += 1
        return output


class WhileTaskIndentHelper:
    def __init__(self):
        self.output = []

    def generate_indents(
        self, special_tasks_data, curr_task, base_indent, depth, if_needed, else_needed
    ):
        """
        generates indents for a while task
        Args:
            special_tasks_data (dict): dict containing special tasks data
            curr_task (str): current task name
            base_indent (int): base indent for the current task
        """
        while_tasks = special_tasks_data["while_tasks"]
        output = self.output
        if_block_indent = None
        else_block_indent = None
        if if_needed:
            if_block_indent = base_indent - 1
        elif else_needed:
            else_block_indent = base_indent - 1

        output.append(
            {
                "task_name": curr_task,
                "while_block_indent": base_indent,
                "task_indent": base_indent,
                "depth": depth,
                "if_block_indent": if_block_indent,
                "else_block_indent": else_block_indent,
            }
        )
        for task in while_tasks[curr_task]["child_tasks"]:
            if task.type in special_tasks_types:
                helper = IndentHelper()
                output += helper.generate_indents(
                    special_tasks_data, task, base_indent + 1, depth + 1, False, False
                )
            else:
                output.append(
                    {
                        "task_name": task.name,
                        "while_block_indent": None,
                        "task_indent": base_indent + 1,
                        "depth": depth + 1,
                        "if_block_indent": None,
                        "else_block_indent": None,
                    }
                )
        return output
