# Major Feats

- <b>Global Variables (Variables with Centralized Management): </b>  Now you can define a variable once, import it, and use it across different blueprints, runbooks, and automation tasks to avoid any duplication and to simplify management. These variables serve as a centralized hub for predefined values. You do not have to redefine the same value across various automation entities. For more information [read](https://www.nutanix.dev/docs/self-service-dsl/getting-started/global_variable/) 

    - Read about Global Variable DSL model: [here](https://www.nutanix.dev/docs/self-service-dsl/models/Variable/globalvariable/)
    - Step by step guide on using Global Variable through DSL: [here](https://www.nutanix.dev/docs/self-service-dsl/tutorial/first_global_variable/)

- <b>Account Tunnels in Self-Service: </b> Now you can set up a tunnel to connect and manage automation activities when the Prism Central hosting Self-Service cannot directly communicate with a remote Prism Central due to connectivity restrictions. For more information [read](https://www.nutanix.dev/docs/self-service-dsl/getting-started/tunnels/)

    - Step by step guide on using tunnels through DSL: [here](https://www.nutanix.dev/docs/self-service-dsl/tutorial/first_account_tunnel/)

# Improvements

- <b>Service Account Integration with Self-Service: </b> Now you can use a service account api key for authentication when adding a remote Prism Central as an account in Self-Service. For more information [read](https://www.nutanix.dev/docs/self-service-dsl/models/Account/#service-account-api-key-authentication) 

- <b>Execution name for a runbook: </b> Now you can add an execution name to your runbook to give each runbook execution instance a meaningful identifier. Adding the execution name helps provide business context to the runbook and helps you trace and analyze logs easily. For more information [read](https://www.nutanix.dev/docs/self-service-dsl/getting-started/runbooks/#execution-name-for-runbook-executions-calm-430)