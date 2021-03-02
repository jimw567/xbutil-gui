# -*- coding: utf-8 -*-
#
# xbutil GUI
#
# Developers: Jim Wu, Annie Ren
#
# MIT License
#
# Copyright (c) 2020-2021 xbutil GUI contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
    author_email="jimw567@gmail.com",
    description="Xilinx xbutil GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jimw567/xbutil-gui",
    packages=['xbutil_gui'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
