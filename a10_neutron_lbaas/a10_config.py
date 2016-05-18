# Copyright 2014,  Doug Wiegley,  A10 Networks.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ConfigParser as ini
import logging
import os
import sys
import imp

from debtcollector import removals

from a10_neutron_lbaas import a10_exceptions as a10_ex
from a10_neutron_lbaas.etc import config as blank_config
from a10_neutron_lbaas.etc import defaults

LOG = logging.getLogger(__name__)


class A10Config(object):

    DEVICE_DEFAULTS = {
        "status": True,
        "autosnat": True,
        "api_version": "2.1",
        "v_method": "LSI",
        "max_instance": 5000,
        "use_float": False,
        "method": "hash"
    }

    def __init__(self, config_name='config'):
        # Look for config in the virtual environment
        # virtualenv puts the original prefix in sys.real_prefix
        # pyenv puts it in sys.base_prefix
        venv_d = os.path.join(sys.prefix, 'etc/a10')
        has_prefix = (hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix'))
        env_override = os.environ.get('A10_CONFIG_DIR', None)
        if config_name is None:
            config_name = 'config'
        if config_name is not None:
            d = config_name
        elif env_override is not None:
            d = env_override
        elif has_prefix and os.path.exists(venv_d):
            d = venv_d
        elif os.path.exists('/etc/neutron/services/loadbalancer/a10networks'):
            d = '/etc/neutron/services/loadbalancer/a10networks'
        else:
            d = '/etc/a10'
        self._config_dir = os.environ.get('A10_CONFIG_DIR', d)

        real_sys_path = sys.path
        sys.path = [self._config_dir]
        try:
            try:
                f,path,description = imp.find_module(config_name)
                self._config = imp.load_module(config_name,f,path,description)
            except ImportError as e:
                LOG.error("A10Config could not find %s/%s", self._config_dir, config_name)
                self._config = blank_config

            # Global defaults
            for dk, dv in defaults.GLOBAL_DEFAULTS.items():
                if not hasattr(self._config, dk):
                    LOG.debug("setting global default %s=%s", dk, dv)
                    setattr(self._config, dk, dv)
                else:
                    LOG.debug("global setting %s=%s", dk, getattr(self._config, dk))

            self._devices = {}
            for k, v in self._config.devices.items():
                if 'status' in v and not v['status']:
                    LOG.debug("status is False, skipping dev: %s", v)
                else:
                    for x in defaults.DEVICE_REQUIRED_FIELDS:
                        if x not in v:
                            msg = "device %s missing required value %s, skipping" % (k, x)
                            LOG.error(msg)
                            raise a10_ex.InvalidDeviceConfig(msg)

                    v['key'] = k
                    self._devices[k] = v

                    # Old configs had a name field
                    if 'name' not in v:
                        self._devices[k]['name'] = k

                    # Figure out port and protocol
                    protocol = self._devices[k].get('protocol', 'https')
                    port = self._devices[k].get(
                        'port', {'http': 80, 'https': 443}[protocol])
                    self._devices[k]['protocol'] = protocol
                    self._devices[k]['port'] = port

                    # Device defaults
                    for dk, dv in defaults.DEVICE_OPTIONAL_DEFAULTS.items():
                        if dk not in self._devices[k]:
                            self._devices[k][dk] = dv

                    LOG.debug("A10Config, device %s=%s", k, self._devices[k])

            # Setup db foo
            if self._config.use_database and self._config.database_connection is None:
                self._config.database_connection = self._get_neutron_db_string()

            # Setup some backwards compat stuff
            self.config = OldConfig(self)

        finally:
            sys.path = real_sys_path

    # We don't use oslo.config here, in a weak attempt to avoid pulling in all
    # the many openstack dependencies. If this proves problematic, we should
    # shoot this manual parser in the head and just use the global config
    # object.
    def _get_neutron_db_string(self):
        neutron_conf_dir = os.environ.get('NEUTRON_CONF_DIR', self._config.neutron_conf_dir)
        neutron_conf = '%s/neutron.conf' % neutron_conf_dir

        z = None
        if os.path.exists(neutron_conf):
            LOG.debug("found neutron.conf file in /etc")
            n = ini.ConfigParser()
            n.read(neutron_conf)
            try:
                z = n.get('database', 'connection')
            except (ini.NoSectionError, ini.NoOptionError):
                pass

        if z is None:
            raise a10_ex.NoDatabaseURL('must set db connection url or neutron dir in config.py')

        LOG.debug("using %s as db connect string", z)
        return z

    def get(self, key):
        return getattr(self._config, key)

    def get_device(self, device_name):
        return self._devices[device_name]

    def get_devices(self):
        return self._devices

    # backwards compat
    @removals.remove
    @property
    def devices(self):
        return self.config.devices

    @removals.remove
    @property
    def use_database(self):
        return self.config.use_database

    @removals.remove
    @property
    def database_connection(self):
        return self.config.database_connection

    @removals.remove
    @property
    def verify_appliances(self):
        return self.config.verify_appliances


# backwards compat
class OldConfig(object):

    def __init__(self, main_config):
        self._config = main_config

    @removals.remove
    @property
    def devices(self):
        return self._config.get_devices()

    @removals.remove
    @property
    def use_database(self):
        return self._config.get('use_database')

    @removals.remove
    @property
    def database_connection(self):
        return self._config.get('database_connection')

    @removals.remove
    @property
    def verify_appliances(self):
        return self._config.get('verify_appliances')
