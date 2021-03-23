# Copyright 2021 The SODA Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import requests
import six
from oslo_log import log as logging

from delfin import exception, ssl_utils

LOG = logging.getLogger(__name__)


class RequestClient(object):
    SOCKET_TIMEOUT = 10

    def __init__(self, **kwargs):
        rest_access = kwargs.get('rest')
        if rest_access is None:
            raise exception.InvalidInput('Input rest_access is missing')
        self.rest_host = rest_access.get('host')
        self.rest_port = rest_access.get('port')
        self.rest_username = rest_access.get('username')
        self.rest_password = rest_access.get('password')
        self.san_address = 'https://%s:%s' % \
                           (self.rest_host, str(self.rest_port))
        self.verify = kwargs.get('verify', False)
        self.headers = {
            'Accept': 'application/json',
            "Content-Type": "application/json"}

    def do_call(self, url, data, method, auth, timeout=SOCKET_TIMEOUT):
        if 'http' not in url:
            if self.san_address:
                url = '%s%s' % (self.san_address, url)
        try:
            with requests.sessions.Session() as session:
                session.trust_env = False
                session.mount("https://",
                              ssl_utils.get_host_name_ignore_adapter())
                return session.request(method=method, url=url, params=data,
                                       data=data, headers=self.headers,
                                       timeout=timeout, verify=self.verify,
                                       auth=auth)
        except requests.exceptions.ConnectTimeout as ct:
            LOG.error('Connect Timeout err: {}'.format(ct))
            raise exception.InvalidIpOrPort()
        except requests.exceptions.SSLError as e:
            LOG.error('SSLError for %s %s' % (method, url))
            err_str = six.text_type(e)
            if 'certificate verify failed' in err_str:
                raise exception.SSLCertificateFailed()
            else:
                raise exception.SSLHandshakeFailed()
        except Exception as err:
            LOG.exception('Bad response from server: %(url)s.'
                          ' Error: %(err)s', {'url': url, 'err': err})
            if 'WSAETIMEDOUT' in str(err):
                raise exception.ConnectTimeout()
            elif 'Failed to establish a new connection' in str(err):
                LOG.error('Failed to establish: {}'.format(err))
                raise exception.InvalidIpOrPort()
            else:
                raise exception.BadResponse()
