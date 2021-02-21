# -*- coding: utf-8 -*-
#
# Version control large files
# Developers: Jim Wu
#
# Copyright 2021 Xilinx, Inc.
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
#
import setuptools
from xbutil_gui import VERSION

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='xbutil_gui', # Replace with your own username
    version=VERSION,
    entry_points={
        'console_scripts' : [
            'xbutil_gui = xbutil_gui.xbutil_gui:main'
        ]
    },
    author="Jim Wu",
    author_email="ywu@xilinx.com",
    description="Xilinx xbutil GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jimw567/xbutil-gui",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    python_requiress='>=3.6.3'
)
