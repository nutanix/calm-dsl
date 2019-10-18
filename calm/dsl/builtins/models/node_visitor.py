import ast

from .task import dag, meta
from .entity import EntityType
from .task import CalmTask, TaskType
from .variable import CalmVariable, VariableType


def handle_dag_create(node, func_globals, dag_name):
    """
    helper for create parsing tasks and creating dag
    """

    node_visitor = GetCallNodes(func_globals)
    try:
        node_visitor.visit(node)
    except Exception as ex:
        raise ex
    tasks, variables, task_list = node_visitor.get_objects()
    edges = []
    for from_tasks, to_tasks in zip(task_list, task_list[1:]):
        if not isinstance(from_tasks, list):
            from_tasks = [from_tasks]
        if not isinstance(to_tasks, list):
            to_tasks = [to_tasks]
        for from_task in from_tasks:
            for to_task in to_tasks:
                edges.append((from_task.get_ref(), to_task.get_ref()))

    child_tasks = []
    for child_task in task_list:
        if not isinstance(child_task, list):
            child_task = [child_task]
        child_tasks.extend(child_task)

    # First create the dag
    user_dag = dag(
        name=dag_name,
        child_tasks=child_tasks,
        edges=edges
    )

    return user_dag, tasks, variables


def handle_meta_create(node, func_globals, meta_name):
    """
    helper for create parsing tasks and creating meta
    """

    node_visitor = GetCallNodes(func_globals)
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
    user_meta = meta(
        name=meta_name,
        child_tasks=child_tasks
    )

    return user_meta, tasks, variables


class GetCallNodes(ast.NodeVisitor):

    # TODO: Need to add validations for unsupported nodes.
    def __init__(self, func_globals, target=None):
        self.task_list = []
        self.all_tasks = []
        self.variables = {}
        self.target = target or None
        self._globals = func_globals or {}.copy()

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
        if hasattr(context, '__calm_type__') and context.__calm_type__ == "parallel":
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

        # for decision tasks
        elif isinstance(context, TaskType) and context.type == "DECISION":
            for statement in node.body:
                if isinstance(statement, ast.FunctionDef):
                    if statement.name == "success":
                        success_path, tasks, variables = handle_meta_create(statement, self._globals, context.name + "-success")
                        self.all_tasks.extend([success_path] + tasks)
                        self.variables.update(variables)

                    elif statement.name == "failure":
                        failure_path, tasks, variables = handle_meta_create(statement, self._globals, context.name + "-failure")
                        self.all_tasks.extend([failure_path] + tasks)
                        self.variables.update(variables)
                    else:
                        raise ValueError(
                            "Only \"success\" and \"failure\" flows are supported inside decision context"
                        )
                else:
                    raise ValueError(
                        "Only calls to 'FunctionDef' methods supported inside decision context."
                    )

            context.attrs['success_child_reference'] = success_path.get_ref()
            context.attrs['failure_child_reference'] = failure_path.get_ref()
            self.all_tasks.append(context)
            self.task_list.append(context)

        # for parallel tasks
        elif isinstance(context, TaskType) and context.type == "PARALLEL":
            for statement in node.body:
                if isinstance(statement, ast.FunctionDef):
                    meta_task, tasks, variables = handle_meta_create(statement, self._globals, context.name + "-" + statement.name)
                    self.all_tasks.extend([meta_task] + tasks)
                    self.variables.update(variables)
                    context.child_tasks_local_reference_list.append(meta_task.get_ref())
                elif isinstance(statement.value, ast.Call):
                    task = self.visit_Call(statement.value, return_task=True)
                    if task:
                        self.all_tasks.append(task)
                        context.child_tasks_local_reference_list.append(task.get_ref())
                else:
                    raise ValueError(
                        "Only calls to 'CalmTask' or 'FunctionDef' methods supported inside parallel context."
                    )

            self.all_tasks.append(context)
            self.task_list.append(context)
        else:
            raise ValueError(
                "Unsupported context used in 'with' statement inside the action."
            )
