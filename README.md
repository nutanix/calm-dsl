[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

![Build](https://github.com/nutanix/calm-dsl/workflows/Setup%20&%20build%20calm-dsl/badge.svg)

`Latest release version: 4.1.1, Latest-release-tag: v4.1.1`

`Latest Release Notes:` [read here](release-notes/4.1.1)


# Nutanix Cloud Manager (NCM) Self Service (formerly Calm) DSL

## About NCM Self Service DSL

NCM Self-Service DSL refers to the Domain-Specific Language (DSL) used in [NCM Self-Service (formerly Calm)](https://www.nutanix.com/products/cloud-manager/self-service), an application management platform. DSL is a specialized Python based programming language that allows users to define and automate tasks and application workflows within their infrastructure as code (IaC). It also has support for executing CLI commands empowering users to interact with and utilize Self-Service features and functionality in a convenient, efficient, and automated manner. 

### Why Python3 as NCM Self Service DSL?

Language design is black art, and building upon a well-established language is design-wise a big win. The language has also solved many issues like scoping, modules, if-else, inheritance, etc. Well established languages have great tooling support: IDEs, syntax checkers, third-party modules, coding practices, better readability, editing, syntax highlighting, code completion, versioning, collaboration, etc. They see much more community improvements as well. Python specifically comes with a very good REPL (read–eval–print-loop). Having an interactive prompt to play around and slowly build objects is an order-of-magnitude improvement in developer productivity. Python is very easy language to learn and use; and most of the ITOps/DevOps community already use Python for scripting.

## Getting Started and Documentation

**Complete documentation is available on Nutanix Dev Community [Website](https://www.nutanix.dev/self-service-dsl/)**

 - [DSL Technical Documentation](https://www.nutanix.dev/docs/self-service-dsl/)
 - [DSL Setup](https://www.nutanix.dev/docs/self-service-dsl/setup/)
 - [DSL Initialization](https://www.nutanix.dev/docs/self-service-dsl/initialization/)
 - [DSL CLI commands](https://www.nutanix.dev/docs/self-service-dsl/getting-started/commands/)
 - [DSL Release Notes](https://github.com/nutanix/calm-dsl/tree/master/release-notes)
 - [NCM Self Service Terminology](docs/01-Calm-Terminology/)
 - [DSL Blueprint Architecture](https://www.nutanix.dev/docs/self-service-dsl/models/Blueprint/)

 ### Tutorials
 - [Create your First Blueprint](https://www.nutanix.dev/docs/self-service-dsl/tutorial/first_blueprint/)
 - [Create your First Runbook](https://www.nutanix.dev/docs/self-service-dsl/tutorial/first_runbook/)

### Video Links
 - [Workstation Setup](https://youtu.be/uIZmHQhioZg)
 - [Blueprint & App management](https://youtu.be/jb-ZllhaROs)
 - [NCM Self Service DSL Blueprint Architecture](https://youtu.be/Y-6eq91rtSw)

### [Blogs](https://www.nutanix.dev/calm-dsl/)
 - [Introducing the NCM Self Service DSL](https://www.nutanix.dev/2020/03/17/introducing-the-nutanix-calm-dsl/)
 - [Creating Custom Blueprint](https://www.nutanix.dev/2020/03/30/nutanix-calm-dsl-creating-custom-blueprint/)
 - [Generating VM Specs](https://www.nutanix.dev/2020/04/06/nutanix-calm-dsl-generating-vm-specs/)
 - [Run Custom Actions](https://www.nutanix.dev/2020/04/17/nutanix-calm-dsl-run-custom-actions/)
 - [Remote Container Development (Part 1)](https://www.nutanix.dev/2020/04/24/nutanix-calm-dsl-remote-container-development-part-1/)
 - [From UI to Code – NCM Self Service DSL and Blueprint Decompile](https://www.nutanix.dev/2020/07/20/from-ui-to-code-calm-dsl-and-blueprint-decompile/)

### Demos
 - [Zero-touch CI/CD - VDI Template Creation with NCM Self Service DSL](https://youtu.be/5k_K7idGxsI)
 - [Integrating with Azure DevOps CI/CD pipeline](https://youtu.be/496bvlIi4pk)

## Contributing to Self-Service DSL

This repository only contains Self-Service DSL command line interface and the python model for different Self-Service enitities. To know more about compiling DSL and contributing suggested changes, refer to the [contribution guide](https://www.nutanix.dev/docs/self-service-dsl/contributions/).

## Reporting Issues

To raise and track any improvement or a bug, create an open issue in DSL github repository, [issue section.](https://github.com/nutanix/calm-dsl/issues)

## License

**[Apache-2.0 license](https://github.com/nutanix/calm-dsl/blob/master/LICENSE)**