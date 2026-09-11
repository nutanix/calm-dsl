# Bug Fixes

- <b>Block addition of PE accounts in projects: </b> Added guardrails to prevent adding Prism Element (PE) accounts directly to a project through DSL. PE accounts should only be added via a parent PC account. Previously, adding a PE account directly caused an "Internal Server Error".

- <b>Block modification of LOCAL_AZ account in Calm VM: </b> DSL now blocks create, update, and sync operations on the `NTNX_LOCAL_AZ` account when running on a Calm VM setup, matching the existing UI behavior.

- <b>Fix account platform sync failure: </b> Fixed an issue where account platform sync (`calm sync account`) was failing.

- Fixed `calm init dsl` blockage in new machines when config.ini is missing.

- Added `make clean-all` Makefile target that performs a full cleanup
