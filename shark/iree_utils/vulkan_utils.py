# Copyright 2020 The Nod Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# All the iree_vulkan related functionalities go here.

from os import linesep
from sys import platform
from iree.runtime import get_driver


def get_all_devices(driver_name):
    """
    Inputs: driver_name
    Returns a list of all the available devices for a given driver sorted by
    the iree path names of the device as in --list_devices option in iree.
    Set `full_dict` flag to True to get a dict
    with `path`, `name` and `device_id` for all devices
    """
    driver = get_driver(driver_name)
    device_list_src = driver.query_available_devices()
    device_list_src.sort(key=lambda d: d["path"])
    return device_list_src


def create_map_device_to_key(driver, key):
    # key can only be path, name, device id
    device_list = get_all_devices(driver)
    device_map = dict()
    # mapping driver name to default device (driver://0)
    device_map[f"{driver}"] = f"{device_list[0][key]}"
    for i, device in enumerate(device_list):
        # mapping with index
        device_map[f"{driver}://{i}"] = f"{device[key]}"
        # mapping with full path
        device_map[f"{driver}://{device['path']}"] = f"{device[key]}"

    return device_map


def map_device_to_path(device):
    driver = device.split("://")[0]
    device_map = create_map_device_to_key(driver, "path")
    try:
        device_path = device_map[device]
    except KeyError:
        raise Exception(f"Device {device} is not a valid device.")
    return f"{driver}://{device_path}"


def map_device_to_name(device):
    driver = device.split("://")[0]
    device_map = create_map_device_to_key(driver, "name")
    try:
        device_name = device_map[device]
    except KeyError:
        raise Exception(f"Device {device} is not a valid device.")
    return device_name


def get_os_name():
    if platform.startswith("linux"):
        return "linux"
    elif platform == "darwin":
        return "macos"
    elif platform == "win32":
        return "windows"
    else:
        print("Cannot detect OS type, defaulting to linux.")
        return "linux"


def get_vulkan_triple_flag(device_name):
    system_os = get_os_name()
    triple = None
    # Apple Targets
    if all(x in device_name for x in ("Apple", "M1")):
        triple = "m1-moltenvk-macos"
    elif all(x in device_name for x in ("Apple", "M2")):
        triple = "m1-moltenvk-macos"
    # Nvidia Targets
    elif all(x in device_name for x in ("RTX", "2080")):
        triple = f"turing-rtx2080-{system_os}"
    elif all(x in device_name for x in ("A100", "SXM4")):
        triple = f"ampere-rtx3080-{system_os}"
    elif all(x in device_name for x in ("RTX", "3090")):
        triple = f"ampere-rtx3090-{system_os}"
    elif all(x in device_name for x in ("RTX", "4090")):
        triple = f"ampere-rtx3090-{system_os}"
    elif all(x in device_name for x in ("RTX", "4000")):
        triple = f"turing-rtx4000-{system_os}"
    elif all(x in device_name for x in ("RTX", "5000")):
        triple = f"turing-rtx5000-{system_os}"
    elif all(x in device_name for x in ("RTX", "6000")):
        triple = f"turing-rtx6000-{system_os}"
    elif all(x in device_name for x in ("RTX", "8000")):
        triple = f"turing-rtx8000-{system_os}"
    # Amd Targets
    elif all(x in device_name for x in ("AMD", "7900")):
        triple = f"rdna3-7900-{system_os}"
    elif any(x in device_name for x in ("AMD", "Radeon")):
        triple = f"rdna2-unknown-{system_os}"
    else:
        print(
            """Optimized kernel for your target device is not added yet.
            Contact SHARK Admin on discord[https://discord.com/invite/RUqY2h2s9u]
            or pull up an issue."""
        )
        print(f"Target : {device_name}")
        return None

    print(f"Found {device_name}. Using {triple}")
    return f"-iree-vulkan-target-triple={triple}"


def get_iree_vulkan_args(device, extra_args=[]):
    vulkan_flag = []
    device_name = map_device_to_name(device)
    if "-iree-vulkan-target-triple=" in " ".join(extra_args):
        print(
            f"Found {device_name}. Using target triple from command line args"
        )
        return vulkan_flag

    vulkan_triple_flag = get_vulkan_triple_flag(device_name)
    if vulkan_triple_flag is not None:
        vulkan_flag.append(vulkan_triple_flag)
    return vulkan_flag


def set_iree_vulkan_runtime_flags(flags):
    import iree.runtime as ireert

    for flag in flags:
        ireert.flags.parse_flags(flag)
    return
