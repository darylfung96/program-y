"""
Copyright (c) 2016-17 Keith Sterling http://www.keithsterling.com

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import logging

from programy.config.base import BaseConfigurationData
from programy.config.sections.brain.oob import BrainOOBConfiguration

class BrainOOBSConfiguration(BaseConfigurationData):
    def __init__(self):
        BaseConfigurationData.__init__(self, "oob")
        self._default = None
        self._oobs = {}

    def exists(self, name):
        if name == 'default':
            return bool(self._default is not None)
        else:
            return bool(name in self._oobs)

    def default(self):
        return self._default

    def oob(self, name):
        if name in self._oobs:
            return self._oobs[name]
        else:
            return None

    def oobs(self):
        return self._oobs.keys()

    def load_config_section(self, file_config, brain_config, bot_root):
        oobs = file_config.get_section("oob", brain_config)
        if oobs is not None:
            oob_keys = file_config.get_keys(oobs)

            for name in oob_keys:
                oob = BrainOOBConfiguration(name)
                oob.load_config_section(file_config, oobs, bot_root)
                if name == 'default':
                    self._default = oob
                else:
                    self._oobs[name] = oob

        else:
            if logging.getLogger().isEnabledFor(logging.WARNING): logging.warning("Config section [oobs] missing from Brain, no oobs loaded")
