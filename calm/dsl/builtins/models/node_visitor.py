import ast
import uuid

from .task import meta
from .entity import EntityType
from .task import CalmTask, TaskType
from .variable import CalmVariable, VariableType


def handle_meta_create(node, func_globals):
    """
    helper for create parsing tasks and creating meta
    """

    node_visitor = GetCallNodes(func_globals, is_runbook=True)
    try:
        node_visitor.visit(node)
    except Exception as ex:
        raise ex
    tasks, variables, task_list = node_visitor.get_objects()

    child_tasks = []
    for child_task in task_list:
        if not isinstance(child_task, list):
            child_task = [child_task]
        child_tasks.extend(child_task)

    # First create the meta
    user_meta = meta(name=str(uuid.uuid4())[-10:] + "_meta", child_tasks=child_tasks)

    return user_meta, tasks, variables


class GetCallNodes(ast.NodeVisitor):

    # TODO: Need to add validations for unsupported nodes.
    def __init__(self, func_globals, target=None, is_runbook=False):
        self.task_list = []
        self.all_tasks = []
        self.variables = {}
        self.target = target or None
        self._globals = func_globals or {}.copy()

        # flag to check if this runbook is in context of RaaS, as decision, while, parallel tasks are supported only in RaaS
        self.is_runbook = is_runbook

    def get_objects(self):
        return self.all_tasks, self.variables, self.task_list

    def visit_Call(self, node, return_task=False):
        sub_node = node.func
        while not isinstance(sub_node, ast.Name):
            sub_node = sub_node.value
        py_object = eval(compile(ast.Expression(sub_node), "", "eval"), self._globals)
        if py_object == CalmTask or isinstance(py_object, EntityType):
            task = eval(compile(ast.Expression(node), "", "eval"), self._globals)
            if task is not None and isinstance(task, TaskType):
                if self.target is not None and not task.target_any_local_reference:
                    task.target_any_local_reference = self.target
                if return_task:
                    return task
                self.task_list.append(task)
                self.all_tasks.append(task)
                return
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if not isinstance(node.value, ast.Call):
            return self.generic_visit(node)
        sub_node = node.value.func
        while not isinstance(sub_node, ast.Name):
            sub_node = sub_node.value
        if (
            eval(compile(ast.Expression(sub_node), "", "eval"), self._globals)
            == CalmVariable
        ):
            if len(node.targets) > 1:
                raise ValueError(
                    "not enough values to unpack (expected {}, got 1)".format(
                        len(node.targets)
                    )
                )
            variable_name = node.targets[0].id
            if variable_name in self.variables.keys():
                raise NameError("duplicate variable name {}".format(variable_name))
            variable = eval(
                compile(ast.Expression(node.value), "", "eval"), self._globals
            )
            if isinstance(variable, VariableType):
                variable.name = variable_name
                self.variables[variable_name] = variable
                return
        return self.generic_visit(node)

    def visit_With(self, node):
        parallel_tasks = []
        if len(node.items) > 1:
            raise ValueError(
                "Only a single context is supported in 'with' statements inside the action."
            )
        context = eval(
            compile(ast.Expression(node.items[0].context_expr), "", "eval"),
            self._globals,
        )
        if (
            not self.is_runbook
            and hasattr(context, "__calm_type__")
            and context.__calm_type__ == "parallel"
        ):
            for statement in node.body:
                if not isinstance(statement.value, ast.Call):
                    raise ValueError(
                        "Only calls to 'CalmTask' methods supported inside parallel context."
                    )
                task = self.visit_Call(statement.value, return_task=True)
                if task:
                    parallel_tasks.append(task)
                    self.all_tasks.append(task)
            self.task_list.append(parallel_tasks)

        # for running tasks serially
        elif (
            self.is_runbook
            and hasattr(context, "__calm_type__")
            and context.__calm_type__ == "serial"
        ):
            serialBody = ast.FunctionDef(body=node.body, col_offset=node.col_offset)
            meta_task, tasks, variables = handle_meta_create(serialBody, self._globals)
            self.all_tasks.extend([meta_task] + tasks)
            self.variables.update(variables)
            self.task_list.append(meta_task)

        # for decision tasks
        elif (
            self.is_runbook
            and isinstance(context, TaskType)
            and context.type == "DECISION"
        ):
            if not node.items[0].optional_vars:
                raise ValueError(
                    "Decision task must be used in the format `with CalmTask.Decision() as val`"
                )
            var = node.items[0].optional_vars.id
            success_path = None
            failure_path = None
            for statement in node.body:
                if isinstance(statement, ast.If) and statement.test.value.id == var:

                    if statement.orelse:
                        raise ValueError(
                            "elif or else are not supported in decision context"
                        )

                    if statement.test.attr.lower() == "true":
                        if success_path:
                            raise ValueError(
                                "'True' flow is defined more than once in decision task."
                            )
                        success_path, tasks, variables = handle_meta_create(
                            statement, self._globals
                        )
                        self.all_tasks.extend([success_path] + tasks)
                        self.variables.update(variables)

                    elif statement.test.attr.lower() == "false":
                        if failure_path:
                            raise ValueError(
                                "'False' flow is defined more than once in decision task."
                            )
                        failure_path, tasks, variables = handle_meta_create(
                            statement, self._globals
                        )
                        self.all_tasks.extend([failure_path] + tasks)
                        self.variables.update(variables)
                    else:
                        raise ValueError(
                            "Only 'True' and 'False' flows are supported inside decision context."
                        )
                else:
                    raise ValueError(
                        "Only calls to 'If' methods on decision variable are supported inside decision context."
                    )

            if not success_path or not failure_path:
                raise ValueError(
                    "Both 'True' and 'False' flows are required for decision task."
                )

            context.attrs["success_child_reference"] = success_path.get_ref()
            context.attrs["failure_child_reference"] = failure_path.get_ref()
            self.all_tasks.append(context)
            self.task_list.append(context)

        # for parallel tasks
        elif (
            self.is_runbook
            and isinstance(context, TaskType)
            and context.type == "PARALLEL"
        ):
            parallelBody = ast.FunctionDef(body=node.body, col_offset=node.col_offset)
            _node_visitor = GetCallNodes(self._globals, is_runbook=True)
            try:
                _node_visitor.visit(parallelBody)
            except Exception as ex:
                raise ex
            tasks, variables, task_list = _node_visitor.get_objects()
            self.all_tasks.extend(tasks)
            self.variables.update(variables)

            for task in task_list:
                context.child_tasks_local_reference_list.append(task.get_ref())

            self.all_tasks.append(context)
            self.task_list.append(context)

        # for while tasks
        elif (
            self.is_runbook
            and isinstance(context, TaskType)
            and context.type == "WHILE_LOOP"
        ):
            whileBody = ast.FunctionDef(body=node.body, col_offset=node.col_offset)
            meta_task, tasks, variables = handle_meta_create(whileBody, self._globals)
            self.all_tasks.extend([meta_task] + tasks)
            self.variables.update(variables)
            context.child_tasks_local_reference_list.append(meta_task.get_ref())
            self.all_tasks.append(context)
            self.task_list.append(context)
        else:
            raise ValueError(
                "Unsupported context used in 'with' statement inside the action."
            )
