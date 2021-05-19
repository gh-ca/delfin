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
import six
from oslo_log import log

from delfin import exception
from delfin.common import constants
from delfin.drivers import driver
from delfin.drivers.dell_emc.unity import rest_handler, alert_handler
from delfin.drivers.dell_emc.unity.alert_handler import AlertHandler

LOG = log.getLogger(__name__)


class UnityStorDriver(driver.StorageDriver):
    """UnityStorDriver implement the DELL EMC Storage driver"""
    HEALTH_OK = (5, 7)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rest_handler = rest_handler.RestHandler(**kwargs)
        self.rest_handler.login()

    def reset_connection(self, context, **kwargs):
        self.rest_handler.logout()
        self.rest_handler.verify = kwargs.get('verify', False)
        self.rest_handler.login()

    def close_connection(self):
        self.rest_handler.logout()

    def get_storage(self, context):
        system_info = self.rest_handler.get_storage()
        capacity = self.rest_handler.get_capacity()
        version_info = self.rest_handler.get_soft_version()
        status = constants.StorageStatus.OFFLINE
        if system_info is not None and capacity is not None:
            system_entries = system_info.get('entries')
            for system in system_entries:
                content = system.get('content', {})
                name = content.get('name')
                model = content.get('model')
                serial_number = content.get('serialNumber')
                health_value = content.get('health').get('value')
                if health_value in UnityStorDriver.HEALTH_OK:
                    status = constants.StorageStatus.NORMAL
                else:
                    status = constants.StorageStatus.ABNORMAL
                break
            capacity_info = capacity.get('entries')
            for per_capacity in capacity_info:
                content = per_capacity.get('content', {})
                free = content.get('sizeFree')
                total = content.get('sizeTotal')
                used = content.get('sizeUsed')
                subs = content.get('sizeSubscribed')
                break
            soft_version = version_info.get('entries')
            for soft_info in soft_version:
                content = soft_info.get('content', {})
                version = content.get('id')
                break
            system_result = {
                'name': name,
                'vendor': 'DELL EMC',
                'model': model,
                'status': status,
                'serial_number': serial_number,
                'firmware_version': version,
                'location': '',
                'subscribed_capacity': int(subs),
                'total_capacity': int(total),
                'raw_capacity': int(total),
                'used_capacity': int(used),
                'free_capacity': int(free)
            }
        return system_result

    def list_storage_pools(self, context):
        pool_info = self.rest_handler.get_all_pools()
        pool_list = []
        pool_type = constants.StorageType.UNIFIED
        if pool_info is not None:
            pool_entries = pool_info.get('entries')
            for pool in pool_entries:
                content = pool.get('content', {})
                health_value = content.get('health').get('value')
                if health_value in UnityStorDriver.HEALTH_OK:
                    status = constants.StorageStatus.NORMAL
                else:
                    status = constants.StorageStatus.ABNORMAL
                pool_result = {
                    'name': content.get('name'),
                    'storage_id': self.storage_id,
                    'native_storage_pool_id': str(content.get('id')),
                    'description': content.get('description'),
                    'status': status,
                    'storage_type': pool_type,
                    'total_capacity': int(content.get('sizeTotal')),
                    'subscribed_capacity': int(content.get('sizeSubscribed')),
                    'used_capacity': int(content.get('sizeUsed')),
                    'free_capacity': int(content.get('sizeFree'))
                }
                pool_list.append(pool_result)
        return pool_list

    def volume_handler(self, volumes, volume_list):
        if volumes is not None:
            vol_entries = volumes.get('entries')
            for volume in vol_entries:
                content = volume.get('content', {})
                total = content.get('sizeTotal')
                used = content.get('sizeAllocated')
                vol_type = constants.VolumeType.THICK
                if content.get('isThinEnabled') is True:
                    vol_type = constants.VolumeType.THIN
                health_value = content.get('health').get('value')
                if health_value in UnityStorDriver.HEALTH_OK:
                    status = constants.StorageStatus.NORMAL
                else:
                    status = constants.StorageStatus.ABNORMAL
                volume_result = {
                    'name': content.get('name'),
                    'storage_id': self.storage_id,
                    'description': content.get('description'),
                    'status': status,
                    'native_volume_id': str(content.get('id')),
                    'native_storage_pool_id': content.get('pool').get('id'),
                    'wwn': content.get('wwn'),
                    'type': vol_type,
                    'total_capacity': int(total),
                    'used_capacity': int(used),
                    'free_capacity': int(total - used)
                }
                volume_list.append(volume_result)

    def list_volumes(self, context):
        page_number = 1
        volume_list = []
        while True:
            luns = self.rest_handler.get_all_luns(page_number)
            if 'entries' not in luns:
                break
            if len(luns['entries']) < 1:
                break
            self.volume_handler(luns, volume_list)
            page_number = page_number + 1

        return volume_list

    def list_alerts(self, context, query_para=None):
        page_number = 1
        alert_model_list = []
        while True:
            alert_list = self.rest_handler.get_all_alerts(page_number)
            if 'entries' not in alert_list:
                break
            if len(alert_list['entries']) < 1:
                break
            alert_handler.AlertHandler() \
                .parse_queried_alerts(alert_model_list, alert_list, query_para)
            page_number = page_number + 1

        return alert_model_list

    def list_controllers(self, context):
        try:
            controller_list = []
            controller_info = self.rest_handler.get_all_controllers()
            if controller_info is not None:
                pool_entries = controller_info.get('entries')
                for pool in pool_entries:
                    content = pool.get('content', {})
                    health_value = content.get('health').get('value')
                    if health_value in UnityStorDriver.HEALTH_OK:
                        status = constants.StorageStatus.NORMAL
                    else:
                        status = constants.StorageStatus.ABNORMAL
                    controller_result = {
                        'name': content.get('name'),
                        'storage_id': self.storage_id,
                        'native_controller_id': content.get('id'),
                        'status': status,
                        'location': content.get('slotNumber'),
                        'memory_size': content.get('memorySize'),
                    }
                    controller_list.append(controller_result)
            return controller_list
        except Exception as err:
            err_msg = "Failed to get controller metrics from UnityStor: %s" %\
                      (six.text_type(err))
            LOG.error(err_msg)
            raise exception.InvalidResults(err_msg)

    @staticmethod
    def handle_port_ip(ip, result):
        if ip is None:
            ip = result
        else:
            ip = '%s;%s' % (ip, result)

    def get_eth_ports(self, port_list):
        ports = self.rest_handler.get_all_ethports()
        ip_interfaces = self.rest_handler.get_port_interface()
        if ports is not None:
            port_entries = ports.get('entries')
            for port in port_entries:
                content = port.get('content', {})
                health_value = content.get('health').get('value')
                if health_value in UnityStorDriver.HEALTH_OK:
                    status = constants.StorageStatus.NORMAL
                else:
                    status = constants.StorageStatus.ABNORMAL
                conn_status = constants.PortConnectionStatus.CONNECTED if \
                    content.get('isLinkUp') is True \
                    else constants.PortConnectionStatus.DISCONNECTED
                ipv4 = None
                ipv4_mask = None
                ipv6 = None
                ipv6_mask = None
                for ip_info in ip_interfaces.get('entries'):
                    ip_content = ip_info.get('content', {})
                    if content.get('id') == ip_content.get(
                            'ipPort').get('id'):
                        if ip_content.get('ipProtocolVersion') == 4:
                            UnityStorDriver.handle_port_ip(
                                ipv4, ip_content.get('ipAddress'))
                            UnityStorDriver.handle_port_ip(
                                ipv4_mask, ip_content.get('netmask'))
                        else:
                            UnityStorDriver.handle_port_ip(
                                ipv6, ip_content.get('ipAddress'))
                            UnityStorDriver.handle_port_ip(
                                ipv6_mask, ip_content.get('netmask'))
                port_result = {
                    'name': content.get('name'),
                    'storage_id': self.storage_id,
                    'native_port_id': content.get('id'),
                    'location': content.get('name'),
                    'connection_status': conn_status,
                    'health_status': status,
                    'type': constants.PortType.ETH,
                    'logical_type': '',
                    'speed': content.get('speed'),
                    'max_speed': content.get('supportedSpeeds'),
                    'native_parent_id':
                        content.get('storageProcessor').get('id'),
                    'wwn': '',
                    'mac_address': content.get('macAddress'),
                    'ipv4': ipv4,
                    'ipv4_mask': ipv4_mask,
                    'ipv6': ipv6,
                    'ipv6_mask': ipv6_mask
                }
                port_list.append(port_result)

    def get_fc_port(self, port_list):
        ports = self.rest_handler.get_all_ethports()
        if ports is not None:
            port_entries = ports.get('entries')
            for port in port_entries:
                content = port.get('content', {})
                health_value = content.get('health').get('value')
                if health_value in UnityStorDriver.HEALTH_OK:
                    status = constants.StorageStatus.NORMAL
                else:
                    status = constants.StorageStatus.ABNORMAL
                conn_status = status
                port_result = {
                    'name': content.get('name'),
                    'storage_id': self.storage_id,
                    'native_port_id': content.get('id'),
                    'location': content.get('slotNumber'),
                    'connection_status': conn_status,
                    'health_status': status,
                    'type': constants.PortType.FC,
                    'logical_type': '',
                    'speed': content.get('currentSpeed'),
                    'max_speed': content.get('availableSpeeds'),
                    'native_parent_id':
                        content.get('storageProcessor').get('id'),
                    'wwn': content.get('wwn'),
                    'mac_address': '',
                    'ipv4': '',
                    'ipv4_mask': '',
                    'ipv6': '',
                    'ipv6_mask': ''
                }
                port_list.append(port_result)

    def list_ports(self, context):
        try:
            port_list = []
            self.get_eth_ports(port_list)
            self.get_fc_port(port_list)
            return port_list
        except Exception as err:
            err_msg = "Failed to get ports metrics from UnityStor: %s" % \
                      (six.text_type(err))
            raise exception.InvalidResults(err_msg)

    def list_disks(self, context):
        try:
            disks = self.rest_handler.get_all_disks()
            disk_list = []
            if disks is not None:
                disk_entries = disks.get('entries')
                for disk in disk_entries:
                    content = disk.get('content', {})
                    health_value = content.get('health').get('value')
                    if health_value in UnityStorDriver.HEALTH_OK:
                        status = constants.StorageStatus.NORMAL
                    else:
                        status = constants.StorageStatus.ABNORMAL
                    disk_result = {
                        'name': content.get('name'),
                        'storage_id': self.storage_id,
                        'native_disk_id': content.get('id'),
                        'serial_number': content.get('emcSerialNumber'),
                        'manufacturer': content.get('manufacturer'),
                        'model': content.get('model'),
                        'firmware': content.get('version'),
                        'speed': content.get('rpm'),
                        'capacity': content.get('size'),
                        'status': status,
                        'physical_type': constants.DiskPhysicalType.SAS,
                        'logical_type': '',
                        'native_disk_group_id': content.
                            get('diskGroup').get('id'),
                        'location': content.get('slotNumber')
                    }
                    disk_list.append(disk_result)
            return disk_list

        except Exception as err:
            err_msg = "Failed to get disk metrics from UnityStor: %s" % \
                      (six.text_type(err))
            raise exception.InvalidResults(err_msg)

    def list_filesystems(self, context):
        try:
            files = self.rest_handler.get_all_filesystems()
            fs_list = []
            if files is not None:
                fs_entries = files.get('entries')
                for disk in fs_entries:
                    content = disk.get('content', {})
                    health_value = content.get('health').get('value')
                    if health_value in UnityStorDriver.HEALTH_OK:
                        status = constants.StorageStatus.NORMAL
                    else:
                        status = constants.StorageStatus.ABNORMAL
                    fs_type = constants.VolumeType.THICK
                    if content.get('isThinEnabled') is True:
                        fs_type = constants.VolumeType.THIN
                    fs = {
                        'name': content.get('name'),
                        'storage_id': self.storage_id,
                        'native_filesystem_id': content.get('id'),
                        'native_pool_id': content.get('pool').get('id'),
                        'status': status,
                        'type': fs_type,
                        'total_capacity': int(content.get('sizeTotal')),
                        'used_capacity': int(content.get('sizeAllocated')),
                        'free_capacity': int(content.get('sizeTotal')) - int(
                            content.get('sizeAllocated'))
                    }
                    fs_list.append(fs)
        except Exception as err:
            err_msg = "Failed to get filesystem metrics from UnityStor: %s"\
                      % (six.text_type(err))
            raise exception.InvalidResults(err_msg)

    def list_qtrees(self, context):
        try:
            qts = self.rest_handler.get_all_qtrees()
            qt_list = []
            if qts is not None:
                qts_entries = qts.get('entries')
                for qtree in qts_entries:
                    content = qtree.get('content', {})
                    qt = {
                        'name': content.get('description'),
                        'storage_id': self.storage_id,
                        'native_qtree_id': content.get('id'),
                        'native_filesystem_id':
                            content.get('filesystem').get('id'),
                        'path': content.get('path')
                    }
                    qt_list.append(qt)
            return qt_list
        except Exception as err:
            err_msg = "Failed to get qtree metrics from UnityStor: %s"\
                      % (six.text_type(err))
            raise exception.InvalidResults(err_msg)

    def get_share(self, share_list, protocol):
        try:
            if protocol == 'cifs':
                shares = self.rest_handler.get_all_cifsshares()
                protocol = constants.ShareProtocol.CIFS
            else:
                shares = self.rest_handler.get_all_nfsshares()
                protocol = constants.ShareProtocol.NFS
            if shares is not None:
                share_entries = shares.get('entries')
                for share in share_entries:
                    content = share.get('content', {})
                    fs = {
                        'name': content.get('name'),
                        'storage_id': self.storage_id,
                        'native_share_id': content.get('id'),
                        'native_filesystem_id':
                            content.get('filesystem').get('id'),
                        'path': content.get('path'),
                        'protocol': protocol
                    }
                    share_list.append(fs)
        except Exception as err:
            err_msg = "Failed to get share metrics from UnityStor: %s"\
                      % (six.text_type(err))
            raise exception.InvalidResults(err_msg)

    def list_shares(self, context):
        try:
            share_list = []
            self.get_cifs_share(share_list, 'cifs')
            self.get_nfs_share(share_list, 'nfs')
            return share_list
        except Exception as err:
            err_msg = "Failed to get shares metrics from UnityStor: %s"\
                      % (six.text_type(err))
            raise exception.InvalidResults(err_msg)

    def add_trap_config(self, context, trap_config):
        pass

    def remove_trap_config(self, context, trap_config):
        pass

    @staticmethod
    def parse_alert(context, alert):
        return AlertHandler.parse_alert(context, alert)

    def clear_alert(self, context, alert):
        return self.rest_handler.remove_alert(alert)

    @staticmethod
    def get_access_url():
        return 'https://{ip}'
