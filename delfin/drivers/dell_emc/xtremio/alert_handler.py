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
import time

from oslo_log import log
from oslo_utils import units

from delfin import exception
from delfin.common import constants
from delfin.drivers.dell_emc.xtremio import consts
from delfin.i18n import _

LOG = log.getLogger(__name__)


class AlertHandler(object):

    @staticmethod
    def parse_alert(alert):
        try:
            alert_model = dict()
            alert_model['alert_id'] = alert.get(consts.OID_CODE)
            alert_model['alert_name'] = alert.get(consts.OID_DESCRIPTION)
            alert_model['severity'] = consts.ALERT_LEVEL_MAP.get(
                alert.get(consts.OID_SEVERITY),
                constants.Severity.INFORMATIONAL)
            alert_model['sequence_number'] = alert.get(consts.OID_INDEX)
            alert_model['category'] = constants.Category.FAULT
            alert_model['type'] = constants.EventType.EQUIPMENT_ALARM
            occur_time = int(time.time()) * units.k
            alert_model['occur_time'] = occur_time
            alert_model['description'] = alert.get(
                consts.OID_DESCRIPTION)
            alert_model['resource_type'] = constants.DEFAULT_RESOURCE_TYPE
            return alert_model
        except Exception as e:
            LOG.error(e)
            msg = (_("Failed to build alert model as some attributes missing "
                     "in alert message."))
            raise exception.InvalidResults(msg)
