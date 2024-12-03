# flake8: noqa
# pylint: skip-file
# type: ignore

import os
from calm.dsl.runbooks import *
from calm.dsl.runbooks import (
    CalmEndpoint as Endpoint,
    RunbookTask as CalmTask,
    RunbookVariable as CalmVariable,
)
from calm.dsl.builtins import CalmTask as CalmVarTask, Metadata

# Runbook


@runbook
def dsl_vm_create_workflow():

    rb_vm_name = CalmVariable.Simple(
        "MyNewVM",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
        description="",
    )  # noqa
    rb_vlan_id = CalmVariable.Simple(
        "1234",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
        description="",
    )  # noqa
    rb_subnet_name = CalmVariable.Simple(
        "MyNewSubnet",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
        description="",
    )  # noqa

    CalmTask.ResourceTypeAction(
        "Create Subnet",
        Ref.Resource_Type(name="Subnet", provider_name="MyNutanixProvider"),
        Ref.ResourceTypeAction(
            name="Create Nutanix IPAM Subnet",
            resource_type_name="Subnet",
            provider_name="MyNutanixProvider",
        ),
        account_ref=Ref.Account(name="my_nutanix_account"),
        inarg_list=[
            CalmVariable.Simple(
                "",
                label="Description (Optional)",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
                name="description",
            ),
            CalmVariable.Simple(
                "",
                label="Boot File Name (Optional)",
                is_mandatory=False,
                is_hidden=False,
                runtime=False,
                description="",
                name="boot_file_name",
            ),
            CalmVariable.Simple(
                "",
                label="TFTP Server Name (Optional)",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
                name="tftp_server_name",
            ),
            CalmVariable.Simple(
                "",
                label="Domain Search List CSV",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Enter domain search list - <domain1>,<domain2>",
                name="domain_search_list",
            ),
            CalmVariable.Simple(
                "",
                label="Domain Name (Optional)",
                regex="^.*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
                name="domain_name",
            ),
            CalmVariable.Simple(
                "10.40.64.15,10.40.64.16",
                label="DNS List (Optional)",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Enter comma separated dns servers eg <IP>, <IP>",
                name="domain_name_server_list",
            ),
            CalmVariable.Simple(
                "10.44.19.126",
                label="DHCP Server Address (Optional)",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
                name="dhcp_server_address",
            ),
            CalmVariable.Simple(
                '"10.44.19.66 10.44.19.125"',
                label="IP Pool List (Optional)",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description='Enter pool list in this format eg."<start_ip> <end_ip>", "<start_ip> <end_ip>" ',
                name="pool_list",
            ),
            CalmVariable.Simple(
                "10.44.19.65",
                label="Default Gateway IP",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="",
                name="default_gateway_ip",
            ),
            CalmVariable.Simple(
                "10.44.19.64/26",
                label="Subnet IP Prefix",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Enter subnet IP with prefix eg 10.10.10.10/24",
                name="subnet_ip",
            ),
            CalmVariable.WithOptions.FromTask(
                CalmVarTask.Exec.escript.py3(
                    name="",
                    filename=os.path.join(
                        "scripts",
                        "Task_Create Subnet_variable_virtual_switch_uuid_Task_SampleTask.py",
                    ),
                ),
                label="Virtual Switch UUID",
                is_mandatory=True,
                is_hidden=False,
                description="",
                value="vs0:a16ead9e-7e38-4384-96f1-463ad44440b6",
                name="virtual_switch_uuid",
            ),
            CalmVariable.Simple(
                "@@{rb_vlan_id}@@",
                label="VLAN ID",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Enter vlan_id",
                name="vlan_id",
            ),
            CalmVariable.Simple(
                "@@{rb_subnet_name}@@",
                label="Subet Name",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Enter name of subnet",
                name="subnet_name",
            ),
            CalmVariable.WithOptions.FromTask(
                CalmVarTask.Exec.escript.py3(
                    name="",
                    filename=os.path.join(
                        "scripts",
                        "Task_Create Subnet_variable_pe_cluster_uuid_Task_SampleTask.py",
                    ),
                ),
                label="PE Cluster UUID",
                is_mandatory=True,
                is_hidden=False,
                description="Please select cluster",
                value="auto_cluster_prod_3603422bb3bb:00061d74-f560-a7e1-0c0a-ac1f6b35f919",
                name="pe_cluster_uuid",
            ),
        ],
        output_variables={"create_subnet_status": "task_status"},
    )

    CalmTask.Exec.escript.py3(
        name="Create subnet status",
        filename=os.path.join(
            "scripts", "_Runbook_vm_create_workflow_Task_Createsubnetstatus.py"
        ),
    )

    CalmTask.ResourceTypeAction(
        "Create VM",
        Ref.Resource_Type(name="VM", provider_name="MyNutanixProvider"),
        Ref.ResourceTypeAction(
            name="Create",
            resource_type_name="VM",
            provider_name="MyNutanixProvider",
        ),
        account_ref=Ref.Account(name="my_nutanix_account"),
        inarg_list=[
            CalmVariable.WithOptions(
                ["Yes", "No"],
                label="Wait",
                default="Yes",
                regex="^.*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Whether to wait for the operation to complete",
                name="wait",
            ),
            CalmVariable.Simple.multiline(
                "",
                label="Categories",
                regex="^(.|\\n)*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Comma separated names of categories ",
                name="categories",
            ),
            CalmVariable.Simple.multiline(
                "",
                label="Cloud init",
                regex="^(.|\\n)*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Cloud init scripts used when creating the VM",
                name="cloud_init",
            ),
            CalmVariable.Simple.multiline(
                "",
                label="Sys Prep",
                regex="^(.|\\n)*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Sys prep scripts used when creating the VM",
                name="sys_prep",
            ),
            CalmVariable.Simple(
                "",
                label="Subnet",
                regex="^.*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Name of the subnet to create the VM",
                name="subnet",
            ),
            CalmVariable.Simple(
                "",
                label="ISO Image",
                regex="^.*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Name of the iso image needed to create the CD-ROM",
                name="iso_image",
            ),
            CalmVariable.Simple(
                "",
                label="Disk Image",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Name of the disk image needed to create the disk",
                name="disk_image",
            ),
            CalmVariable.Simple(
                "",
                label="Storage Container",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="This reference is for disk level storage container preference. This preference specifies the storage container to which this disk belongs",
                name="storage_container",
            ),
            CalmVariable.Simple.int(
                "",
                label="Size of the disk in Bytes",
                regex="^[\\d]*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Size of the disk in Bytes\n\n",
                name="disk_size_in_bytes",
            ),
            CalmVariable.Simple.int(
                "1",
                label="Number of vCPU sockets",
                regex="^[\\d]*$",
                validate_regex=False,
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Number of vCPU sockets\n\n",
                name="num_of_sockets",
            ),
            CalmVariable.Simple.int(
                "2",
                label="Number of cores per socket",
                regex="^[\\d]*$",
                validate_regex=False,
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Number of cores per socket",
                name="num_cores_per_socket",
            ),
            CalmVariable.Simple.int(
                "1",
                label="Number of threads per core",
                regex="^[\\d]*$",
                validate_regex=False,
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Number of threads per core",
                name="num_threads_per_core",
            ),
            CalmVariable.Simple.int(
                "2000000000",
                label="Memory size in bytes",
                regex="^[\\d]*$",
                validate_regex=False,
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Memory size in bytes",
                name="memory_size_bytes",
            ),
            CalmVariable.Simple(
                "auto_cluster_prod_3603422bb3bb",
                label="Cluster",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Reference to a cluster\n\n",
                name="cluster",
            ),
            CalmVariable.Simple(
                "",
                label="VM description",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="VM description\n\n",
                name="description",
            ),
            CalmVariable.Simple(
                "@@{rb_vm_name}@@",
                label="VM Name",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Name of the VM to be created",
                name="vm_name",
            ),
        ],
        output_variables={"create_vm_status": "task_status"},
    )

    CalmTask.Exec.escript.py3(
        name="Create VM status",
        filename=os.path.join(
            "scripts", "_Runbook_vm_create_workflow_Task_CreateVMstatus.py"
        ),
    )

    CalmTask.ResourceTypeAction(
        "List VMs",
        Ref.Resource_Type(name="VM", provider_name="MyNutanixProvider"),
        Ref.ResourceTypeAction(
            name="List",
            resource_type_name="VM",
            provider_name="MyNutanixProvider",
        ),
        account_ref=Ref.Account(name="my_nutanix_account"),
        inarg_list=[
            CalmVariable.Simple.int(
                "0",
                label="Page",
                regex="^[\\d]*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="A URL query parameter that specifies the page number of the result set. It must be a positive integer between 0 and the maximum number of pages that are available for that resource. Any number out of this range might lead to no results",
                name="page",
            ),
            CalmVariable.Simple.int(
                "50",
                label="Limit",
                regex="^[\\d]*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="A URL query parameter that specifies the total number of records returned in the result set. Must be a positive integer between 1 and 100. Any number out of this range will lead to a validation error. If the limit is not provided, a default value of 50 records will be returned in the result set.",
                name="limit",
            ),
            CalmVariable.Simple(
                "name eq '@@{rb_vm_name}@@'",
                label="Filter",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="A URL query parameter that allows clients to filter a collection of resources. The expression specified with $filter is evaluated for each resource in the collection, and only items where the expression evaluates to true are included in the response. Expression specified with the $filter must conform to the OData V4.01 URL conventions. For example, filter '$filter=name eq 'karbon-ntnx-1.0' would filter the result on cluster name 'karbon-ntnx1.0', filter '$filter=startswith(name, 'C')' would filter on cluster name starting with 'C'.",
                name="filter",
            ),
            CalmVariable.Simple(
                "name",
                label="Order By",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="A URL query parameter that allows clients to specify the sort criteria for the returned list of objects. Resources can be sorted in ascending order using asc or descending order using desc. If asc or desc are not specified, the resources will be sorted in ascending order by default. For example, '$orderby=templateName desc' would get all templates sorted by templateName in descending order",
                name="orderby",
            ),
            CalmVariable.Simple(
                "",
                label="Select",
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="A URL query parameter that allows clients to request a specific set of properties for each entity or complex type. Expression specified with the $select must conform to the OData V4.01 URL conventions. If a $select expression consists of a single select item that is an asterisk (i.e., *), then all properties on the matching resource will be returned",
                name="select",
            ),
        ],
        output_variables={"output_vms": "vms"},
    )

    CalmTask.SetVariable.escript.py3(
        name="Extract ID of new VM",
        filename=os.path.join(
            "scripts", "_Runbook_vm_create_workflow_Task_ExtractIDofnewVM.py"
        ),
        variables=["vm_ext_id"],
    )

    CalmTask.ResourceTypeAction(
        "Power on VM",
        Ref.Resource_Type(name="VM", provider_name="MyNutanixProvider"),
        Ref.ResourceTypeAction(
            name="Perform Operation",
            resource_type_name="VM",
            provider_name="MyNutanixProvider",
        ),
        account_ref=Ref.Account(name="my_nutanix_account"),
        inarg_list=[
            CalmVariable.WithOptions(
                ["Yes", "No"],
                label="Wait",
                default="Yes",
                regex="^.*$",
                validate_regex=False,
                is_mandatory=False,
                is_hidden=False,
                runtime=True,
                description="Whether to wait for the operation to complete",
                name="wait",
            ),
            CalmVariable.WithOptions(
                [
                    "reboot",
                    "shutdown",
                    "guest-reboot",
                    "guest-shutdown",
                    "power-on",
                    "power-off",
                    "power-cycle",
                    "reset",
                ],
                label="Action",
                default="power-on",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="Name of the action that needs to be performed",
                name="action",
            ),
            CalmVariable.Simple(
                "@@{vm_ext_id}@@",
                label="VM ExtID",
                regex="^.*$",
                validate_regex=False,
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="The globally unique identifier of a VM",
                name="vm_extId",
            ),
        ],
        output_variables={"power_status": "task_status"},
    )

    CalmTask.Exec.escript.py3(
        name="Power on VM status",
        filename=os.path.join(
            "scripts", "_Runbook_vm_create_workflow_Task_PoweronVMstatus.py"
        ),
    )


class RunbookMetadata(Metadata):
    project = Ref.Project("default")
