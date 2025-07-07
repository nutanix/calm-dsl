> **Python < 3.8 support will be deprecated from DSL v4.2.0 onwards:** To continue using DSL and it's features use Python 3.8 or above while setting up DSL environment

# Improvements

- <b>Added support to configure VMs with a vTPM (virtual Trusted Platform Module) in AHV bluperints. </b> To enable vTPM in your AHV VM blueprints, set the `boot_type` attribute to UEFI and the `vtpm_enabled` attribute to True in the AHV VM resources class. For more information, [read](https://www.nutanix.dev/docs/self-service-dsl/getting-started/blueprints/#virual-trusted-platform-module-vtpm-support-for-ahv-blueprints)

- <b>Support for downloadable images in Single VM Blueprint:</b> You can now configure a downloadable image in Single VM blueprint to allow Self-Service to automatically download an image and import the image into the Nutanix image service.

# Bug Fixes

- Fixed an issue preventing brownfield import for AWS provider through DSL.
- Fixed an issue where role-based access control (RBAC) users were unable to view overlay subnets under the infrastructure details for a project.