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

from shark.iree_utils._common import run_cmd


def get_vulkan_triple_flag(extra_args=[]):
    if "-iree-vulkan-target-triple=" in " ".join(extra_args):
        print(f"Using target triple from command line args")
        return None
    return "-iree-vulkan-target-triple=rdna2-unknown-linux"


def get_iree_vulkan_args(extra_args=[]):
    # vulkan_flag = ["--iree-flow-demote-i64-to-i32"]
    vulkan_flag = []
    vulkan_triple_flag = get_vulkan_triple_flag(extra_args)
    if vulkan_triple_flag is not None:
        vulkan_flag.append(vulkan_triple_flag)
    return vulkan_flag
