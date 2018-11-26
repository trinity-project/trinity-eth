# --*-- coding : utf-8 --*--
"""
Package :

Author  : Trinity Core Team

MIT License

Copyright (c) 2018 Trinity

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import platform
import os


# Trinity version for whole packages
# version x.y.z
#   This version will have same meaning as Linux
#       x -- Production version with big different feature
#       y -- Odd number means formal version, Even number means beta/development version
#       z -- Count of fixing bugs
__version__ = '0.3.0'


# Trinity running OS type
__os_platform__ = platform.system().upper() if platform.system() else 'LINUX'


# Trinity running network settings
__running_over_main_net__ = ('MainNet'.upper() == os.getenv('TRINITY_NET', '').upper().strip())


# Database basic configuration. Default the mongodb is chosen.
DATABASE_CONFIGURATION = {
    'authentication': {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    },
    'type': os.getenv('DB_TYPE', 'mongodb'),
    'name': os.getenv('DB_TRINITY', 'trinity')
    if __running_over_main_net__ else os.getenv('DB_TRINITY', 'beta-trinity'),
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 27017))
}


# Supported Asset List Settings
