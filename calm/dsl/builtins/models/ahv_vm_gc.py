from .entity import EntityType, Entity
from .validator import PropertyValidator
from .utils import read_file, yaml

import os
import sys
import inspect
import re


# AHV Guest Customization


class AhvGCType(EntityType):
    __schema_name__ = "AhvGuestCustomization"
    __openapi_type__ = "vm_ahv_gc"


class AhvGCValidator(PropertyValidator, openapi_type="vm_ahv_gc"):
    __default__ = None
    __kind__ = AhvGCType


def ahv_vm_guest_customization(**kwargs):
    name = getattr(AhvGCType, "__schema_name__")
    bases = (Entity,)
    return AhvGCType(name, bases, kwargs)


def create_ahv_guest_customization(
    customization_type="cloud_init",
    user_data="",
    unattend_xml="",
    install_type="FRESH",
    is_domain=False,
    domain="",
    dns_ip="",
    dns_search_path="",
    credential=None,
):

    if customization_type == "cloud_init":
        kwargs = {"cloud_init": {"user_data": user_data}}

    elif customization_type == "sysprep":
        kwargs = {
            "sysprep": {
                "unattend_xml": unattend_xml,
                "install_type": install_type,
                "is_domain": is_domain,
                "domain": domain,
                "dns_ip": dns_ip,
                "dns_search_path": dns_search_path,
                "credential": credential,
            }
        }

    return ahv_vm_guest_customization(**kwargs)


def cloud_init(filename=None, user_data={}):

    if not user_data:
        file_path = os.path.join(
            os.path.dirname(inspect.getfile(sys._getframe(2))), filename
        )

        # Reading the file
        with open(file_path, "r", encoding="utf-8") as f:
            user_data = f.read()

        # Checking whether macros exists in file
        if re.search("@@{.*}@@", user_data):
            return create_ahv_guest_customization(
                customization_type="cloud_init", user_data=user_data
            )

        # If macros doesn't exists, then safe load the yaml file
        else:
            user_data = yaml.safe_load(user_data)

    user_data = "#cloud-config\n" + yaml.dump(user_data, default_flow_style=False)

    return create_ahv_guest_customization(
        customization_type="cloud_init", user_data=user_data
    )


def fresh_sys_prep_with_domain(
    domain="",
    dns_ip="",
    dns_search_path="",
    credential=None,
    filename=None,
    unattend_xml="",
):
    if not unattend_xml:
        if filename:
            unattend_xml = read_file(filename, depth=3)

    return create_ahv_guest_customization(
        customization_type="sysprep",
        install_type="FRESH",
        unattend_xml=unattend_xml,
        is_domain=True,
        domain=domain,
        dns_ip=dns_ip,
        dns_search_path=dns_search_path,
        credential=credential,
    )


def fresh_sys_prep_without_domain(filename=None, unattend_xml=""):
    if not unattend_xml:
        if filename:
            unattend_xml = read_file(filename, depth=3)

    return create_ahv_guest_customization(
        customization_type="sysprep",
        install_type="FRESH",
        unattend_xml=unattend_xml,
        is_domain=False,
        domain="",
        dns_ip="",
        dns_search_path="",
        credential=None,
    )


def prepared_sys_prep_with_domain(
    domain="",
    dns_ip="",
    dns_search_path="",
    credential=None,
    filename=None,
    unattend_xml="",
):
    if not unattend_xml:
        if filename:
            unattend_xml = read_file(filename, depth=3)

    return create_ahv_guest_customization(
        customization_type="sysprep",
        install_type="PREPARED",
        unattend_xml=unattend_xml,
        is_domain=True,
        domain=domain,
        dns_ip=dns_ip,
        dns_search_path=dns_search_path,
        credential=credential,
    )


def prepared_sys_prep_without_domain(filename=None, unattend_xml=""):
    if not unattend_xml:
        if filename:
            unattend_xml = read_file(filename, depth=3)

    return create_ahv_guest_customization(
        customization_type="sysprep",
        install_type="PREPARED",
        unattend_xml=unattend_xml,
        is_domain=False,
        domain="",
        dns_ip="",
        dns_search_path="",
        credential=None,
    )


class AhvVmGC:
    class CloudInit:
        def __new__(cls, filename=None, user_data={}):
            return cloud_init(filename=filename, user_data=user_data)

    class Sysprep:
        def __new__(cls, filename=None, unattend_xml=""):
            return fresh_sys_prep_without_domain(
                filename=filename, unattend_xml=unattend_xml
            )

        class FreshScript:
            def __new__(cls, filename=None, unattend_xml=""):
                return fresh_sys_prep_without_domain(
                    filename=filename, unattend_xml=unattend_xml
                )

            withDomain = fresh_sys_prep_with_domain
            withoutDomain = fresh_sys_prep_without_domain

        class PreparedScript:
            def __new__(cls, filename=None, unattend_xml=""):
                return prepared_sys_prep_without_domain(
                    filename=filename, unattend_xml=unattend_xml
                )

            withDomain = prepared_sys_prep_with_domain
            withoutDomain = prepared_sys_prep_without_domain
