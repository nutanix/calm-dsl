import os
import sys

from asciimatics.widgets import (
    Frame,
    Layout,
    Divider,
    Text,
    Button,
    DatePicker,
    TimePicker,
    Label,
    DropdownList,
)
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication
import time
from time import sleep
from datetime import timedelta
import itertools

from anytree import NodeMixin, RenderTree
import datetime

from .constants import RUNLOG, SINGLE_INPUT
from calm.dsl.api import get_api_client


def parse_machine_name(runlog_id, machine_name):
    if not machine_name:
        return None
    machine_info = machine_name.split("-{} - ".format(runlog_id))
    return machine_info


class InputFrame(Frame):
    def __init__(self, name, screen, inputs, data):
        super(InputFrame, self).__init__(
            screen,
            int(len(inputs) * 2 + 8),
            int(screen.width * 4 // 5),
            has_shadow=True,
            data=data,
            name=name,
        )
        layout = Layout([1, len(inputs), 1])
        self.add_layout(layout)
        layout.add_widget(
            Label("Inputs for the input task '{}'".format(name), height=2), 1
        )
        for singleinput in inputs:
            if (
                singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT)
                == SINGLE_INPUT.TYPE.TEXT
            ):
                layout.add_widget(
                    Text(
                        label=singleinput.get("name") + ":",
                        name=singleinput.get("name"),
                        on_change=self._on_change,
                    ),
                    1,
                )
            elif (
                singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT)
                == SINGLE_INPUT.TYPE.DATE
            ):
                layout.add_widget(
                    DatePicker(
                        label=singleinput.get("name") + ":",
                        name=singleinput.get("name"),
                        year_range=range(1899, 2300),
                        on_change=self._on_change,
                    ),
                    1,
                )
            elif (
                singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT)
                == SINGLE_INPUT.TYPE.TIME
            ):
                layout.add_widget(
                    TimePicker(
                        label=singleinput.get("name") + ":",
                        name=singleinput.get("name"),
                        seconds=True,
                        on_change=self._on_change,
                    ),
                    1,
                )
            elif singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT) in [
                SINGLE_INPUT.TYPE.SELECT,
                SINGLE_INPUT.TYPE.SELECTMULTIPLE,
            ]:
                layout.add_widget(
                    DropdownList(
                        [(option, option) for option in singleinput.get("options")],
                        label=singleinput.get("name") + ":",
                        name=singleinput.get("name"),
                        on_change=self._on_change,
                    ),
                    1,
                )
            elif (
                singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT)
                == SINGLE_INPUT.TYPE.PASSWORD
            ):
                layout.add_widget(
                    Text(
                        label=singleinput.get("name") + ":",
                        name=singleinput.get("name"),
                        hide_char="*",
                        on_change=self._on_change,
                    ),
                    1,
                )

        layout.add_widget(Divider(height=3), 1)
        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Submit", self._submit), 1)
        self.fix()

    def _set_default(self):
        self.set_theme("bright")

    def _on_change(self):
        self.save()

    def _submit(self):
        for key, value in self.data.items():
            input_payload[key]["value"] = str(value)
        raise StopApplication("User requested exit")


class RerunFrame(Frame):
    def __init__(self, status, screen):
        super(RerunFrame, self).__init__(
            screen,
            int(8),
            int(screen.width * 3 // 4),
            has_shadow=True,
            name="Rerun popup box",
        )
        layout = Layout([1, 4, 1])
        self.add_layout(layout)
        layout.add_widget(
            Label("Runbook run is in FAILURE STATE '{}'".format(status), height=2), 1
        )
        layout2 = Layout([1, 2, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Re-run", self._rerun), 1)
        layout2.add_widget(Button("Exit", self._exit), 2)
        self.fix()

    def _rerun(self):
        rerun.update({"rerun": True})
        self._exit()

    def _exit(self):
        raise StopApplication("User requested exit")


class ConfirmFrame(Frame):
    def __init__(self, name, screen):
        super(ConfirmFrame, self).__init__(
            screen, int(8), int(screen.width * 3 // 4), has_shadow=True, name=name
        )
        layout = Layout([1, 4, 1])
        self.add_layout(layout)
        layout.add_widget(Label("Confirmation for '{}' task".format(name), height=2), 1)
        layout2 = Layout([1, 2, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Pass", self._pass), 1)
        layout2.add_widget(Button("Fail", self._fail), 2)
        self.fix()

    def _pass(self):
        confirm_payload["confirm_answer"] = "SUCCESS"
        raise StopApplication("User requested exit")

    def _fail(self):
        confirm_payload["confirm_answer"] = "FAILURE"
        raise StopApplication("User requested exit")


def displayRunLogTree(screen, root, completed_tasks, total_tasks, msg=None):
    screen.clear()
    if total_tasks:
        progress = "{0:.2f}".format(completed_tasks / total_tasks * 100)
        screen.print_at("Progress: {}%".format(progress), 0, 0)

    runlog_state = root.children[0].runlog["status"]["state"]
    colour = 3  # yellow for pending state
    if runlog_state == RUNLOG.STATUS.SUCCESS:
        colour = 2  # green for success
    elif runlog_state in RUNLOG.FAILURE_STATES:
        colour = 1  # red for failure
    elif runlog_state == RUNLOG.STATUS.RUNNING:
        colour = 4  # blue for running state
    elif runlog_state == RUNLOG.STATUS.INPUT:
        colour = 6  # cyan for input state

    screen.print_at(
        runlog_state,
        screen.width - len(runlog_state) - 5 if hasattr(screen, "width") else 0,
        0,
        colour=colour,
        attr=Screen.A_UNDERLINE,
    )
    line = 1
    for pre, fill, node in RenderTree(root):
        line = displayRunLog(screen, node, pre, fill, line)
    if msg:
        screen.print_at(msg, 0, line, colour=6)
    line = line + 1
    screen.refresh()
    return line


class RunlogNode(NodeMixin):
    def __init__(
        self,
        runlog,
        machine=None,
        parent=None,
        children=None,
        outputs=None,
        reasons=None,
    ):
        self.runlog = runlog
        self.parent = parent
        self.outputs = outputs or []
        self.reasons = reasons or []
        self.machine = machine
        if children:
            self.children = children


def displayRunLog(screen, obj, pre, fill, line):

    if not isinstance(obj, RunlogNode):
        return super().default(obj)

    metadata = obj.runlog["metadata"]
    status = obj.runlog["status"]
    state = status["state"]
    output = ""
    reason_list = ""

    idx = itertools.count(start=line, step=1).__next__

    if status["type"] == "task_runlog":
        name = status["task_reference"]["name"]
        for out in obj.outputs:
            output += "'{}'\n".format(out[:-1])
        for reason in obj.reasons:
            reason_list += "'{}'\n".format(reason)
    elif status["type"] == "runbook_runlog":
        if "call_runbook_reference" in status:
            name = status["call_runbook_reference"]["name"]
        else:
            name = status["runbook_reference"]["name"]
    elif status["type"] == "action_runlog" and "action_reference" in status:
        name = status["action_reference"]["name"]
    elif status["type"] == "app":
        screen.print_at("{}{}".format(pre, status["name"]), 0, idx())
        return idx()
    else:
        screen.print_at("{}root".format(pre), 0, idx())
        return idx()

    # TODO - Fix KeyError for action_runlog

    if obj.machine:
        name = "{} ['{}']".format(name, obj.machine)

    creation_time = int(metadata["creation_time"]) // 1000000
    username = (
        status["userdata_reference"]["name"] if "userdata_reference" in status else None
    )
    last_update_time = int(metadata["last_update_time"]) // 1000000

    if state in RUNLOG.TERMINAL_STATES:
        time_stats = "[Time Taken: {:0>8}]".format(
            str(timedelta(seconds=last_update_time - creation_time))
        )
    else:
        time_stats = "[Started: {}]".format(time.ctime(creation_time))

    prefix = "{}{} (Status:".format(pre, name)
    screen.print_at("{} {}) {}".format(prefix, state, time_stats), 0, line)
    colour = 3  # yellow for pending state
    if state == RUNLOG.STATUS.SUCCESS:
        colour = 2  # green for success
    elif state in RUNLOG.FAILURE_STATES:
        colour = 1  # red for failure
    elif state == RUNLOG.STATUS.RUNNING:
        colour = 4  # blue for running state
    elif state == RUNLOG.STATUS.INPUT:
        colour = 6  # cyan for input state
    if os.isatty(sys.stdout.fileno()):
        screen.print_at("{}".format(state), len(prefix) + 1, idx(), colour=colour)

    if obj.children:
        fill = fill + "\u2502"

    if status["type"] == "action_runlog":
        screen.print_at("{}\t Runlog UUID: {}".format(fill, metadata["uuid"]), 0, idx())

    if username:
        screen.print_at("{}\t Run by: {}".format(fill, username), 0, idx())

    if output:
        screen.print_at("{}\t Output :".format(fill), 0, idx())
        output_lines = output.splitlines()
        for line in output_lines:
            y_coord = idx()
            screen.print_at("{}\t  {}".format(fill, line), 0, y_coord, colour=5, attr=1)
            screen.print_at(fill, 0, y_coord)

    if reason_list:
        screen.print_at("{}\t Reasons :".format(fill), 0, idx())
        reason_lines = reason_list.splitlines()
        for line in reason_lines:
            y_coord = idx()
            screen.print_at("{}\t  {}".format(fill, line), 0, y_coord, colour=1, attr=1)
            screen.print_at(fill, 0, y_coord)

    if status["type"] == "task_runlog" and state == RUNLOG.STATUS.INPUT:
        attrs = status.get("attrs", None)
        if not isinstance(attrs, dict):
            return idx()

        input_tasks.append(
            {"name": name, "uuid": metadata["uuid"], "inputs": attrs.get("inputs", [])}
        )

    if status["type"] == "task_runlog" and state == RUNLOG.STATUS.CONFIRM:
        confirm_tasks.append({"name": name, "uuid": metadata["uuid"]})
    return idx()


def get_completion_func(screen):
    def is_action_complete(
        response,
        task_type_map=[],
        top_level_tasks=[],
        input_data={},
        runlog_uuid=None,
        **kwargs,
    ):

        client = get_api_client()
        global input_tasks
        global input_payload
        global confirm_tasks
        global confirm_payload
        global rerun
        input_tasks = []
        confirm_tasks = []
        entities = response["entities"]
        if len(entities):

            # catching interrupt for pause and play
            interrupt = None
            if hasattr(screen, "get_event"):
                interrupt = screen.get_event()

            # Sort entities based on creation time
            sorted_entities = sorted(
                entities, key=lambda x: int(x["metadata"]["creation_time"])
            )

            # Create nodes of runlog tree and a map based on uuid
            root = None
            nodes = {}
            runlog_map = {}
            for runlog in sorted_entities:
                # Create root node
                # TODO - Get details of root node
                if not root:
                    root_uuid = runlog["status"]["root_reference"]["uuid"]
                    root_runlog = {
                        "metadata": {"uuid": root_uuid},
                        "status": {"type": "action_runlog", "state": ""},
                    }
                    runlog_map[str(root_uuid)] = root_runlog
                    root = RunlogNode(root_runlog)
                    nodes[str(root_uuid)] = root

                uuid = runlog["metadata"]["uuid"]
                runlog_map[str(uuid)] = runlog
                reasons = runlog["status"].get("reason_list", [])
                outputs = []
                machine_name = runlog["status"].get("machine_name", None)
                machine = parse_machine_name(runlog_uuid, machine_name)
                if machine and len(machine) == 1:
                    runlog["status"]["machine_name"] = "-"
                    continue  # this runlog corresponds to endpoint loop
                elif machine:
                    machine = "{} ({})".format(machine[1], machine[0])

                if runlog["status"]["type"] == "task_runlog":

                    task_id = runlog["status"]["task_reference"]["uuid"]
                    if task_type_map[task_id] == "META":
                        continue  # don't add metatask's trl in runlogTree

                    # Output is not valid for input, confirm and while_loop tasks
                    if task_type_map[task_id] not in ["INPUT", "CONFIRM", "WHILE_LOOP"]:
                        res, err = client.runbook.runlog_output(runlog_uuid, uuid)
                        if err:
                            raise Exception(
                                "\n[{}] - {}".format(err["code"], err["error"])
                            )
                        runlog_output = res.json()
                        output_list = runlog_output["status"]["output_list"]
                        if len(output_list) > 0:
                            outputs.append(output_list[0]["output"])

                nodes[str(uuid)] = RunlogNode(
                    runlog,
                    parent=root,
                    outputs=outputs,
                    machine=machine,
                    reasons=reasons,
                )

            # Attach parent to nodes
            for runlog in sorted_entities:
                uuid = runlog["metadata"]["uuid"]
                if nodes.get(str(uuid), None) is None:
                    continue
                parent_uuid = runlog["status"]["parent_reference"]["uuid"]
                parent_runlog = runlog_map[str(parent_uuid)]
                parent_type = parent_runlog["status"]["type"]
                while (
                    parent_type == "task_runlog"
                    and task_type_map[parent_runlog["status"]["task_reference"]["uuid"]]
                    == "META"
                ) or parent_runlog["status"].get("machine_name", None) == "-":
                    parent_uuid = parent_runlog["status"]["parent_reference"]["uuid"]
                    parent_runlog = runlog_map[str(parent_uuid)]
                    parent_type = parent_runlog["status"]["type"]

                node = nodes[str(uuid)]
                node.parent = nodes[str(parent_uuid)]

            # Show Progress
            # TODO - Draw progress bar
            total_tasks = len(top_level_tasks)
            task_status_map = {}
            completed_tasks = 0
            for runlog in sorted_entities:
                runlog_type = runlog["status"]["type"]
                if runlog_type == "task_runlog":
                    task_id = runlog["status"]["task_reference"]["uuid"]
                    state = runlog["status"]["state"]
                    if (
                        state in RUNLOG.TERMINAL_STATES
                        and task_id in top_level_tasks
                        and not task_status_map.get(task_id, None)
                    ):
                        task_status_map[task_id] = "COMPLETED"
                    elif (
                        state not in RUNLOG.TERMINAL_STATES
                        and task_id in top_level_tasks
                    ):
                        task_status_map[task_id] = "RUNNING"
            for key, val in task_status_map.items():
                if val == "COMPLETED":
                    completed_tasks += 1

            line = displayRunLogTree(screen, root, completed_tasks, total_tasks)

            # Check if any tasks is in INPUT state
            if len(input_tasks) > 0:
                sleep(2)
                for input_task in input_tasks:
                    name = input_task.get("name", "")
                    inputs = input_task.get("inputs", [])
                    task_uuid = input_task.get("uuid", "")
                    input_payload = {}
                    data = {}
                    inputs_required = []
                    input_value = input_data.get(name, {})
                    for singleinput in inputs:
                        input_type = singleinput.get(
                            "input_type", SINGLE_INPUT.TYPE.TEXT
                        )
                        input_name = singleinput.get("name", "")
                        value = input_value.get(input_name, "")
                        if not value:
                            inputs_required.append(singleinput)
                            data.update({input_name: ""})
                        input_payload.update(
                            {input_name: {"secret": False, "value": value}}
                        )
                        if input_type == SINGLE_INPUT.TYPE.PASSWORD:
                            input_payload.update(
                                {input_name: {"secret": True, "value": value}}
                            )
                        elif input_type == SINGLE_INPUT.TYPE.DATE:
                            data.update({input_name: datetime.datetime.now().date()})
                        elif input_type == SINGLE_INPUT.TYPE.TIME:
                            data.update({input_name: datetime.datetime.now().time()})
                    if len(inputs_required) > 0:
                        screen.play(
                            [
                                Scene(
                                    [InputFrame(name, screen, inputs_required, data)],
                                    -1,
                                )
                            ]
                        )
                    if client is not None:
                        client.runbook.resume(
                            runlog_uuid, task_uuid, {"properties": input_payload}
                        )
                input_tasks = []
                msg = "Sending resume for input tasks with input values"
                line = displayRunLogTree(
                    screen, root, completed_tasks, total_tasks, msg=msg
                )

            # Check if any tasks is in CONFIRM state
            if len(confirm_tasks) > 0:
                sleep(2)
                for confirm_task in confirm_tasks:
                    name = confirm_task.get("name", "")
                    task_uuid = confirm_task.get("uuid", "")
                    confirm_payload = {}
                    screen.play([Scene([ConfirmFrame(name, screen)], -1)])
                    if client is not None:
                        client.runbook.resume(runlog_uuid, task_uuid, confirm_payload)
                confirm_tasks = []
                msg = "Sending resume for confirm tasks with confirmation"
                line = displayRunLogTree(
                    screen, root, completed_tasks, total_tasks, msg=msg
                )

            if (
                interrupt
                and hasattr(interrupt, "key_code")
                and interrupt.key_code in (3, 4)
            ):
                # exit interrupt
                screen.close()
                sys.exit(-1)
            elif (
                interrupt
                and hasattr(interrupt, "key_code")
                and interrupt.key_code == 32
            ):
                # on space pause/play runbook based on current state
                runlog_state = root.children[0].runlog["status"]["state"]

                if runlog_state in [
                    RUNLOG.STATUS.RUNNING,
                    RUNLOG.STATUS.INPUT,
                    RUNLOG.STATUS.CONFIRM,
                ]:
                    client.runbook.pause(runlog_uuid)
                    msg = "Triggered pause on the runnning Runbook Execution"
                elif runlog_state in [RUNLOG.STATUS.PAUSED]:
                    client.runbook.play(runlog_uuid)
                    msg = "Triggered play on the paused Runbook Execution"
                line = displayRunLogTree(
                    screen, root, completed_tasks, total_tasks, msg=msg
                )

            rerun = {}
            for runlog in sorted_entities:
                state = runlog["status"]["state"]
                if state in RUNLOG.FAILURE_STATES:
                    sleep(2)
                    msg = "Action failed."
                    if os.isatty(sys.stdout.fileno()):
                        msg += " Exit screen?"
                        screen.play([Scene([RerunFrame(state, screen)], -1)])
                        if rerun.get("rerun", False):
                            client.runbook.rerun(runlog_uuid)
                            msg = "Triggered rerun for the Runbook Runlog"
                            displayRunLogTree(
                                screen, root, completed_tasks, total_tasks, msg=msg
                            )
                            return (False, "")
                        displayRunLogTree(
                            screen, root, completed_tasks, total_tasks, msg=msg
                        )
                        return (True, msg)
                    else:
                        return (True, msg)
                if state not in RUNLOG.TERMINAL_STATES:
                    return (False, "")

            msg = "Action ran successfully."
            if os.isatty(sys.stdout.fileno()):
                msg += " Exit screen?"
            screen.print_at(msg, 0, line, colour=6)
            screen.refresh()

            return (True, msg)
        return (False, "")

    return is_action_complete


def get_runlog_status(screen):
    def check_runlog_status(response, client=None, **kwargs):

        # catching interrupt for exit
        interrupt = None
        if hasattr(screen, "get_event"):
            interrupt = screen.get_event()

        if (
            interrupt
            and hasattr(interrupt, "key_code")
            and interrupt.key_code in (3, 4)
        ):
            # exit interrupt
            screen.close()
            sys.exit(-1)

        if response["status"]["state"] == "PENDING":
            msg = "Runlog run is in PENDING state"
            screen.clear()
            screen.print_at(msg, 0, 0)
            screen.refresh()
        elif response["status"]["state"] in RUNLOG.FAILURE_STATES:
            msg = "Runlog run is in {} state.".format(response["status"]["state"])
            msg += " {}".format("\n".join(response["status"]["reason_list"]))
            screen.clear()
            screen.print_at(msg, 0, 0)
            screen.refresh()
            if response["status"]["reason_list"] == []:
                return (True, "")
            return (True, msg)
        else:
            return (True, "")
        return (False, msg)

    return check_runlog_status
