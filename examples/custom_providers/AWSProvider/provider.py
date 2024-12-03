# flake8: noqa
# pylint: skip-file
import os  # no_qa

from calm.dsl.builtins import (
    read_local_file,
    CalmVariable,
    ResourceType,
    action,
    CloudProvider,
    ProviderEndpointSchema,
    ProviderTestAccount,
)
from calm.dsl.builtins.models.task import ProviderTask as CalmTask

# Secret Variables

CloudProvider_AWSProvider_auth_schema_secret_access_key = read_local_file(
    "CloudProvider_AWSProvider_auth_schema_secret_access_key"
)
CloudProvider_AWSProvider_test_account_variable_secret_access_key = read_local_file(
    "CloudProvider_AWSProvider_test_account_variable_secret_access_key"
)

# Credentials

# ResourceTypes


class S3Bucket(ResourceType):
    """
    S3 Bucket resource type.
    Attributes:
        name (str): The name of the S3 Bucket.
        resource_kind (str): The kind of resource, which is "Storage" for S3 Bucket.
        schemas (list): List of schemas associated with the S3 Bucket.
        variables (list): List of variables associated with the S3 Bucket.
    """

    name = "S3 Bucket"

    resource_kind = "Storage"

    schemas = []

    variables = [
        CalmVariable.Simple(
            "",
            label="",
            is_mandatory=False,
            is_hidden=False,
            runtime=False,
            description="",
            name="rt_var",
        ),
    ]

    @action
    def Create(type="resource_type_create"):
        """
        Creates a new bucket with the specified parameters.

        Args:
            type (str, optional): The type of resource to create. Defaults to "resource_type_create".

        Returns:
            None
        """

        # Input Variables
        bucket_name = CalmVariable.Simple(
            "bucket-463783",
            label="",
            is_mandatory=False,
            is_hidden=False,
            runtime=True,
            description="",
        )
        location = CalmVariable.WithOptions(
            ["us-east-1", "us-west-2"],
            label="",
            default="us-west-2",
            is_mandatory=False,
            is_hidden=False,
            runtime=True,
            description="",
        )
        ACL = CalmVariable.Simple(
            "public-read",
            label="",
            is_mandatory=False,
            is_hidden=False,
            runtime=True,
            description="",
        )

        # Output Variables
        outputs = [
            CalmVariable.Simple(
                "",
                label="",
                is_mandatory=False,
                is_hidden=False,
                runtime=False,
                description="",
                name="ARN",
            ),
        ]

        CalmTask.SetVariable.escript.py3(
            name="Create new Bucket",
            filename=os.path.join(
                "scripts", "ResourceType_S3Bucket_Action_Create_Task_CreatenewBucket.py"
            ),
            variables=["ARN"],
        )

    @action
    def Delete(type="resource_type_delete"):
        """
        Deletes a bucket.

        Args:
            type (str, optional): The type of deletion. Defaults to "resource_type_delete".

        Returns:
            None
        """

        # Input Variables
        bucket_name = CalmVariable.Simple(
            "",
            label="",
            is_mandatory=False,
            is_hidden=False,
            runtime=True,
            description="",
        )

        CalmTask.SetVariable.escript.py3(
            name="Delete Bucket",
            filename=os.path.join(
                "scripts", "ResourceType_S3Bucket_Action_Delete_Task_DeleteBucket.py"
            ),
            variables=[],
        )


class DSL_AWSProvider(CloudProvider):
    """
    AWS Provider.
    Attributes:
        name (str): The name of the S3 Bucket.
        resource_kind (str): The kind of resource, which is "Storage" for S3 Bucket.
        auth_schema_variables (list): List of schemas associated with the S3 Bucket.
        variables (list): List of variables associated with the S3 Bucket.
        endpoint_schema (ProviderEndpointSchema): Schema for the AWS Provider.
        test_account (ProviderTestAccount): Test account for the AWS Provider.
        resource_types (list): List of resource types associated with the AWS Provider.
    """

    infra_type = "cloud"

    auth_schema_variables = [
        CalmVariable.Simple(
            "",
            label="Access Key ID",
            is_mandatory=True,
            is_hidden=False,
            runtime=True,
            description="",
            name="access_key_id",
        ),
        CalmVariable.Simple.Secret(
            CloudProvider_AWSProvider_auth_schema_secret_access_key,
            label="Secret Access Key",
            is_mandatory=True,
            is_hidden=False,
            runtime=True,
            description="",
            name="secret_access_key",
        ),
    ]

    variables = []

    endpoint_schema = ProviderEndpointSchema(type="AWS", variables=[])

    test_account = ProviderTestAccount(
        name="dsl_aws_test_account",
        variables=[
            CalmVariable.Simple(
                "AKIA2LDLYW6I7KAY7QWB",
                label="Access Key ID",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="",
                name="access_key_id",
            ),
            CalmVariable.Simple.Secret(
                CloudProvider_AWSProvider_test_account_variable_secret_access_key,
                label="Secret Access Key",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="",
                name="secret_access_key",
            ),
        ],
    )

    resource_types = [S3Bucket]

    @action
    def Verify(type="provider"):
        """
        Verify the credentials for the AWS provider.
        Args:
            type (str, optional): The type of verification. Defaults to "provider".
        """

        # Input Variables
        CalmTask.Exec.escript.py3(
            name="VerifyCredentials",
            filename=os.path.join(
                "scripts",
                "CloudProvider_AWSProvider_Action_Verify_Task_VerifyCredentials.py",
            ),
        )
