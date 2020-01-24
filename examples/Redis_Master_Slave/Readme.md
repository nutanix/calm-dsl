Redis is an open source (BSD licensed), in-memory data structure store, used as a database, cache and message broker. It supports data structures such as strings, hashes, lists, sets, sorted sets with range queries, bitmaps, hyperloglogs and geospatial indexes with radius queries.
This blueprint creates a Master-Slave cluster with one Master node and two slave nodes.
#### License:
* BSD License
#### Hardware Requirement:
* Three VMs each with 2 vCPU and 2GB RAM
* Redis 3.2.10
#### Operating System:
* CentOS Linux release 7.6.1810
* Select the [AMI](https://goo.gl/td2eJJ) according to the region on AWS.
* Select the [Image](https://goo.gl/51oD7D) according to the zone on GCP.
* Select the [Image](https://goo.gl/KZAjE6) according to the location on Azure.
#### Platform:
* AHV
* AWS
* Azure
* VMware
#### Lifecycle:
* ScaleOut
* ScaleIn
#### Limitations:
* For evaluation purpose only. Not recommended for production use.
#### Other Instructions:
* Open port `6379`.
* Latest stable version of Redis will be installed.
