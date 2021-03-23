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
from oslo_log import log
from oslo_utils import units

from delfin.common import constants
from delfin.drivers import driver
from delfin.drivers.dell_emc.xtremio import consts
from delfin.drivers.dell_emc.xtremio.alert_handler import AlertHandler
from delfin.drivers.dell_emc.xtremio.rest_handler import RestHandler

LOG = log.getLogger(__name__)


class XtremioStorDriver(driver.StorageDriver):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rest_handler = RestHandler(**kwargs)
        self.rest_handler.login()

    def reset_connection(self, context, **kwargs):
        self.rest_handler.verify = kwargs.get('verify', False)
        self.rest_handler.login()

    def close_connection(self):
        pass

    def get_storage(self, context):
        """
        At present, xtremeio supports multi cluster management.
        Because the driver layer only supports the return of one storage,
        when multiple clusters are obtained, only the first cluster
        information will be returned temporarily, and the multi storage
        will be returned after the driver is adjusted later
        """
        storage = {}
        clusters = self.rest_handler.get_clusters()
        if clusters:
            raw_capacity = 0
            cluster = clusters[0]
            total_capacity = int(
                cluster.get('content').get('ud-ssd-space')) * units.Ki
            used_capacity = int(cluster.get('content').get(
                'ud-ssd-space-in-use')) * units.Ki
            ssds = self.rest_handler.get_ssds(
                cluster.get('content').get('index'))
            for ssd in ssds:
                raw_capacity += ssd.get('content').get(
                    'ssd-size-in-kb') * units.Ki
            storage = {
                'name': cluster.get('content').get('name'),
                'vendor': 'DELL EMC',
                'model': cluster.get('content').get('size-and-capacity'),
                'status': consts.STORAGE_HEALTH_MAP.get(
                    cluster.get('content').get('sys-health-state'),
                    constants.StorageStatus.NORMAL),
                'serial_number': cluster.get('content').get(
                    'sys-psnt-serial-number'),
                'firmware_version': cluster.get('content').get(
                    'sys-sw-version'),
                'total_capacity': total_capacity,
                'raw_capacity': raw_capacity,
                'used_capacity': used_capacity,
                'free_capacity': (total_capacity - used_capacity)
            }
        return storage

    def list_storage_pools(self, context):
        pass

    def list_volumes(self, context):
        volume_infos = []
        clusters = self.rest_handler.get_clusters()
        if clusters:
            for cluster in clusters:
                volumes_under_cluster = self.rest_handler.get_volumes(
                    cluster.get('content').get('index'))
                if volumes_under_cluster:
                    volume_infos.extend(volumes_under_cluster)
        volume_list = []
        for volume_info in volume_infos:
            total_capacity = int(
                volume_info.get('content').get('vol-size'))
            used_capacity = int(
                volume_info.get('content').get('logical-space-in-use'))
            volume = {
                'name': volume_info.get('content').get('name'),
                'storage_id': self.storage_id,
                'status': consts.VOLUMES_HEALTH_MAP.get(
                    volume_info.get('content').get('obj-severity'),
                    constants.StorageStatus.ABNORMAL),
                'native_volume_id': str(
                    volume_info.get('content').get('index')),
                'wwn': volume_info.get('content').get('naa-name'),
                'type': constants.VolumeType.THIN,
                'total_capacity': total_capacity,
                'used_capacity': used_capacity,
                'free_capacity': int(total_capacity - used_capacity)
            }
            volume_list.append(volume)
        return volume_list

    def list_controllers(self, context):
        """List all storage controllers from storage system."""
        pass

    def list_ports(self, context):
        """List all ports from storage system."""
        pass

    def list_disks(self, context):
        """List all disks from storage system."""
        pass

    def list_alerts(self, context, query_para=None):
        alert_infos = []
        clusters = self.rest_handler.get_clusters()
        if clusters:
            for cluster in clusters:
                alerts_under_cluster = self.rest_handler.get_alerts(
                    cluster.get('content').get('index'))
                if alerts_under_cluster:
                    alert_infos.extend(alerts_under_cluster)
        alert_list = []
        for alert_info in alert_infos:
            name = alert_info.get('content').get('name')
            if not name:
                name = alert_info.get('content').get('alert-type')
            location = '%s--%s' % (
                alert_info.get('content').get('class-name'),
                alert_info.get('content').get('assoc-obj-name'))
            alert = {
                'location': location,
                'alert_id': alert_info.get('content').get('alert-code'),
                'sequence_number': alert_info.get('content').get('guid'),
                'description': alert_info.get('content').get('description'),
                'alert_name': name,
                'resource_type': constants.DEFAULT_RESOURCE_TYPE,
                'occur_time': int(
                    alert_info.get('content').get('raise-time')) * units.k,
                'category': constants.Category.FAULT,
                'type': constants.EventType.EQUIPMENT_ALARM,
                'severity': consts.ALERT_LEVEL_MAP.get(
                    alert_info.get('content').get('severity'))
            }
            alert_list.append(alert)
        return alert_list

    def add_trap_config(self, context, trap_config):
        pass

    def remove_trap_config(self, context, trap_config):
        pass

    @staticmethod
    def parse_alert(context, alert):
        return AlertHandler.parse_alert(alert)

    def clear_alert(self, context, sequence_number):
        clusters = self.rest_handler.get_clusters()
        if clusters:
            for cluster in clusters:
                self.rest_handler.remove_alert(sequence_number,
                                               cluster.get('content').get(
                                                   'index'))
