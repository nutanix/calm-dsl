# Improvements

- With this version of DSL (v4.2.1 onwards) we are providing seamless and platform agnostic DSL installation using `pip install ntnx-ncm-dsl` for Linux, MacOS and Windows. [[Refer]](https://www.nutanix.dev/docs/self-service-dsl/setup/#local-installation)
- Decommissioned use of setup.py based package building. 
- Added pyproject.toml based package building following latest PEP standards.
- There is no change in the way DSL was previously installed via `make dev` and other make commands. Additional way of installation using pip is added.
- Upgraded scrypt library to 0.9.4

**Command Migration Table:**

| Deprecated Commands | Alternative Commands |
|---|---|
| `venv/bin/python3 setup.py sdist bdist_wheel`<br>*(used to build DSL wheels before)* | `venv/bin/python3 -m build`<br>*(used to build DSL wheels now)* |
| `venv/bin/python3 setup.py develop`<br>*(used to setup DSL for development before)* | `venv/bin/pip3 install -e . -vvv`<br>*(used to setup DSL for development now)* |

> Make sure to migrate above commands with alternatives provided (if used in any custom built script).