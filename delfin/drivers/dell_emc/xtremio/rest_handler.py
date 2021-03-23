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
from oslo_log import log as logging
from requests.auth import HTTPBasicAuth

from delfin import cryptor
from delfin import exception
from delfin.drivers.dell_emc.xtremio import consts
from delfin.drivers.utils.request_client import RequestClient

LOG = logging.getLogger(__name__)


class RestHandler(RequestClient):

    def __init__(self, **kwargs):
        super(RestHandler, self).__init__(**kwargs)

    def call(self, url, data=None, method=None):
        res = self.do_call(url, data, method, self.set_auth())
        if res.status_code == consts.ERROR_SESSION_INVALID_CODE:
            raise exception.InvalidUsernameOrPassword(res.text)
        elif res.status_code == consts.ERROR_BAD_REQUEST_CODE:
            raise exception.BadRequest(res.text)
        elif res.status_code == consts.VALID_REQUEST_CODE:
            if method in ('GET', 'POST'):
                return res.json()
            else:
                return ''
        return res

    def get_resources_info(self, url, data=None, method='GET',
                           drill_down_key=None, cluster_index=None):
        result_list = []
        if cluster_index:
            if data:
                data['cluster-index'] = cluster_index
            else:
                data = {'cluster-index': cluster_index}
        rest_result = self.call(url, data, method)
        if rest_result:
            if drill_down_key:
                drill_url_list = rest_result.get(drill_down_key)
                for drill_url_node in drill_url_list:
                    detail_url = drill_url_node.get('href')
                    resources_detail_result = self.call(detail_url, data,
                                                        method)
                    if resources_detail_result:
                        result_list.append(resources_detail_result)
            else:
                result_list.append(rest_result)
        return result_list

    def set_auth(self):
        return HTTPBasicAuth(self.rest_username,
                             cryptor.decode(self.rest_password))

    def login(self):
        self.call(consts.REST_CLUSTER_LIST_URL, method='GET')

    def get_clusters(self):
        cluster_list = self.get_resources_info(consts.REST_CLUSTER_LIST_URL,
                                               drill_down_key='clusters')
        return cluster_list

    def get_ssds(self, cluster_index):
        ssd_list = self.get_resources_info(consts.REST_SSD_URL,
                                           drill_down_key='ssds',
                                           cluster_index=cluster_index)
        return ssd_list

    def get_volumes(self, cluster_index):
        volume_list = self.get_resources_info(consts.REST_VOLUMES_URL,
                                              drill_down_key='volumes',
                                              cluster_index=cluster_index)
        return volume_list

    def get_alerts(self, cluster_index):
        data = {'filter': 'alert-state:ne:acknowledged'}
        alert_list = self.get_resources_info(consts.REST_ALERTS_URL, data=data,
                                             drill_down_key='alerts',
                                             cluster_index=cluster_index)
        return alert_list

    def remove_alert(self, sequence_number, cluster_index):
        url = '%s%s' % (consts.REST_DEL_ALERT_URL, sequence_number)
        self.get_resources_info(url, method='PUT', cluster_index=cluster_index)
