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
from delfin.common import constants

REST_CLUSTER_LIST_URL = '/api/json/v3/types/clusters'
REST_SSD_URL = '/api/json/v3/types/ssds'
REST_VOLUMES_URL = '/api/json/v3/types/volumes'
REST_ALERTS_URL = '/api/json/v3/types/alerts'
REST_DEL_ALERT_URL = '/api/json/v3/commands/alerts/acknowledge/'
VALID_REQUEST_CODE = 200
ERROR_BAD_REQUEST_CODE = 400
ERROR_SESSION_INVALID_CODE = 401
VOLUMES_HEALTH_MAP = {'critical': constants.StorageStatus.ABNORMAL,
                      'major': constants.StorageStatus.NORMAL,
                      'minor': constants.StorageStatus.NORMAL,
                      'information': constants.StorageStatus.NORMAL,
                      'clear': constants.StorageStatus.NORMAL
                      }
STORAGE_HEALTH_MAP = {'healthy': constants.StorageStatus.NORMAL,
                      'failed': constants.StorageStatus.ABNORMAL,
                      'disconnected': constants.StorageStatus.ABNORMAL,
                      'uninitialized': constants.StorageStatus.ABNORMAL,
                      'initializing': constants.StorageStatus.ABNORMAL
                      }
OID_INDEX = '1.3.6.1.4.1.1139.103.1.18.1.1'
OID_SEVERITY = '1.3.6.1.4.1.1139.30.1.1.1.5'
OID_DESCRIPTION = '1.3.6.1.4.1.1139.30.1.1.1.8'
OID_CODE = '1.3.6.1.4.1.1139.30.1.1.1.11'
OID_CATEGORY = '1.3.6.1.4.1.1139.30.1.1.1.15'
OID_TIMESTAMP = '1.3.6.1.4.1.1139.30.1.1.1.9'
OID_OBJECT = '1.3.6.1.4.1.1139.30.1.1.1.4'
ALERT_LEVEL_MAP = {'critical': constants.Severity.CRITICAL,
                   'major': constants.Severity.MAJOR,
                   'minor': constants.Severity.MINOR,
                   'information': constants.Severity.INFORMATIONAL,
                   'clear': constants.Severity.NOT_SPECIFIED
                   }
