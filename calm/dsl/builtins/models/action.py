import inspect
import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .task import create_call_rb, _get_target_ref
from .runbook import runbook, runbook_create
from calm.dsl.constants import (
    SUBSTRATE,
    ACTION,
    RESOURCE_TYPE,
    CLOUD_PROVIDER as PROVIDER,
)
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# Action - Since action, runbook and DAG task are heavily coupled together,
# the action type behaves as all three.


class ActionType(EntityType):
    __schema_name__ = "Action"
    __openapi_type__ = "app_action"

    def __call__(cls, name=None, target=None):
        """
        This function is called whenever ENTITY_TYPE.function_name() is invoked
        and it returns a task of CALL_RUNBOOK type.

        e.g. Service class having name SampleService defines a function "foo" then
        each call to SampleService.foo() invokes this function.
        """

        if cls.name in list(SUBSTRATE.VM_POWER_ACTIONS_REV.keys()) and cls.runbook:
            if not isinstance(name, str):
                LOG.error("{} if not of type string".format(name))
                sys.exit(-1)

            # global import raises ImportError
            from .substrate import SubstrateType

            entity = cls.runbook.tasks[0].target_any_local_reference.__self__

            # guard condition to only allow substrate level vm power actions
            if isinstance(entity, SubstrateType):
                substrate = entity
                vm_power_action = getattr(
                    substrate, SUBSTRATE.VM_POWER_ACTIONS_REV[cls.name], None
                )
                if not vm_power_action:
                    LOG.error(
                        "Action {} not implemented in substrate".format(
                            SUBSTRATE.VM_POWER_ACTIONS_REV[cls.name]
                        )
                    )
                    sys.exit(-1)
                target_runbook = vm_power_action.runbook
                task = create_call_rb(cls.runbook, name=name, target=target_runbook)
                task.name = name or task.name
                # setting default target to service coupled to a substrate
                if not target:
                    target = substrate.get_service_target()
                    if not target:
                        LOG.error("No service found to target")
                        sys.exit(-1)

                task.target_any_local_reference = _get_target_ref(target)
                return task

        return create_call_rb(cls.runbook, name=name) if cls.runbook else None

    def assign_targets(cls, parent_entity):
        for task in cls.runbook.tasks:
            if not task.target_any_local_reference:
                task.target_any_local_reference = parent_entity.get_task_target()


class ActionValidator(PropertyValidator, openapi_type="app_action"):
    __default__ = None
    __kind__ = ActionType


def _action(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ActionType(name, bases, kwargs)


Action = _action()


def _action_create(**kwargs):
    name = kwargs.get("name", kwargs.get("__name__", None))
    bases = (Action,)
    return ActionType(name, bases, kwargs)


class action(runbook):
    """
    action descriptor
    """

    def __init__(self, user_func, task_target_mapping={}, imported_action=False):
        """
        A decorator for generating runbooks from a function definition.
        Args:
            user_func (function): User defined function
            task_target_mapping (dict): Mapping for task's target. Used for imported runboosk in blueprint
            imported_action (boolean): True if runbook imported as action in blueprint
        Returns:
            (Runbook): Runbook class
        """

        super(action, self).__init__(user_func)

        # Will be used in runbooks imported to blueprint actions
        self.task_target_mapping = task_target_mapping
        self.imported_action = imported_action

    def __call__(self, name=None):
        if self.user_runbook:
            return create_call_rb(self.user_runbook, name=name)

    def __get__(self, instance, cls):
        """
        Translate the user defined function to an action.
        This method is called during compilation, when getattr() is called on the owner entity.
        Args:
            instance (object): Instance of cls
            cls (Entity): Entity that this action is defined on
        Returns:
            (ActionType): Generated Action class
        """
        if cls is None:
            return self

        if self.imported_action:
            # Only endpoints of type existing are supported
            sig = inspect.signature(self.user_func)
            for name, _ in sig.parameters.items():
                if name in ["endpoints", "credentials", "default"]:
                    if name in ["endpoints", "credentials"]:
                        LOG.error(
                            "{} are not supported for imported runbooks. Please use existing {} in the tasks.".format(
                                name, name
                            )
                        )
                    else:
                        LOG.error(
                            "{} are not supported for imported runbooks".format(name)
                        )
                    sys.exit(
                        "Unknown parameter '{}' for imported runbooks".format(name)
                    )

        super(action, self).__get__(instance, cls)

        # System action names
        action_name = self.action_name

        ACTION_TYPE = ACTION.TYPE.USER
        subclasses = EntityType.get_entity_types()
        if isinstance(cls, subclasses[PROVIDER.ENTITY_NAME]):
            ACTION_TYPE = ACTION.TYPE.PROVIDER  # Default for provider actions
        elif isinstance(cls, subclasses[RESOURCE_TYPE.ENTITY_NAME]):
            ACTION_TYPE = (
                RESOURCE_TYPE.ACTION_TYPE.GENERIC
            )  # Default for resource_type actions

        sig = inspect.signature(self.user_func)
        if sig.parameters.get("type", None):
            ACTION_TYPE = sig.parameters["type"].default
        func_name = self.user_func.__name__.lower()
        if func_name.startswith("__") and func_name.endswith("__"):
            SYSTEM = getattr(cls, "ALLOWED_SYSTEM_ACTIONS", {})
            FRAGMENT = getattr(cls, "ALLOWED_FRAGMENT_ACTIONS", {})
            if func_name in SYSTEM:
                ACTION_TYPE = "system"
                action_name = SYSTEM[func_name]
            elif func_name in FRAGMENT:
                ACTION_TYPE = "fragment"
                action_name = FRAGMENT[func_name]
                # Prevent accidental modification of target.
                # Fragment actions have target ref to it's caller class.
                for task in self.user_runbook.tasks:
                    task.target_any_local_reference = cls.get_task_target()

        else:
            # `name` argument is only supported in non-system actions
            gui_display_name = sig.parameters.get("name", None)
            if gui_display_name and gui_display_name.default != action_name:
                action_name = gui_display_name.default

        # Case for imported runbooks in blueprints
        if self.imported_action:

            # Mapping is compulsory for profile actions
            if self.task_target_mapping:
                # For now it is used to map runbook task's target to bp entities for PROFILE
                # In runbook, the target will be endpoint. So it will be changed to target_endpoint
                for _task in self.user_runbook.tasks[1:]:
                    if _task.target_any_local_reference:
                        _task.exec_target_reference = _task.target_any_local_reference
                        _task.target_any_local_reference = None

                    if _task.name in self.task_target_mapping:
                        _task.target_any_local_reference = self.task_target_mapping[
                            _task.name
                        ]

            # Non-Profile actions
            else:
                for _task in self.user_runbook.tasks[1:]:
                    if (
                        _task.target_any_local_reference
                        and _task.target_any_local_reference.kind == "app_endpoint"
                    ):
                        _task.exec_target_reference = _task.target_any_local_reference
                        _task.target_any_local_reference = self.task_target

        # Import error if imported globally
        from .substrate import SubstrateType

        # Case for creating vm power action runbooks for a substrate
        if isinstance(cls, SubstrateType) and action_name in list(
            SUBSTRATE.VM_POWER_ACTIONS_REV.keys()
        ):
            if len(self.user_runbook.tasks) > 1:
                LOG.error(
                    "{} can't be overriden in {}".format(
                        SUBSTRATE.VM_POWER_ACTIONS_REV[action_name], cls.__name__
                    )
                )
                sys.exit(-1)
            self.user_runbook = cls.create_power_action_runbook(action_name)

        # Finally create the action
        self.user_action = _action_create(
            **{
                "name": action_name,
                "description": self.action_description,
                "critical": ACTION_TYPE == "system",
                "type": ACTION_TYPE,
                "runbook": self.user_runbook,
            }
        )

        return self.user_action


class parallel:
    __calm_type__ = "parallel"


def get_runbook_action(runbook_obj, targets={}):
    """
    Get action from the runbook object
    """

    user_func = runbook_obj.user_func
    action_obj = action(user_func, task_target_mapping=targets, imported_action=True)
    return action_obj
