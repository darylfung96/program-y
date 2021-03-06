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

from programy.config.sections.brain.security import BrainSecurityConfiguration
from programy.utils.security.authenticate.authenticator import Authenticator


class ClientIdAuthenticationService(Authenticator):

    def __init__(self, configuration: BrainSecurityConfiguration):
        Authenticator.__init__(self, configuration)
        self.authorised = [
            "console"
        ]

    # Its at this point that we would call a user auth service, and if that passes
    # return true, appending the user to the known authorised list of user
    # This is a very naive approach, and does not cater for users that log out, invalidate
    # their credentials, or have a TTL on their credentials
    # #Exercise for the reader......
    def _auth_clientid(self, clientid):
        authorised = False # call user_auth_service()
        if authorised is True:
            self.authorised.append(clientid)
        return authorised

    def authenticate(self, clientid: str):
        try:
            if clientid in self.authorised:
                return True
            else:
                if self._auth_clientid(clientid) is True:
                    return True

                return False
        except Exception as excep:
            if logging.getLogger().isEnabledFor(logging.ERROR): logging.error(str(excep))
            return False
