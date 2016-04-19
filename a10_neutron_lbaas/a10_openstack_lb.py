# Copyright 2014, Doug Wiegley (dougwig), A10 Networks
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

import logging

import a10_config
import acos_client
import plumbing_hooks as hooks
import version

import v1.handler_hm
import v1.handler_member
import v1.handler_pool
import v1.handler_vip

import v2.handler_hm
import v2.handler_lb
import v2.handler_listener
import v2.handler_member
import v2.handler_pool
import time
import signal
import sys
import atexit
import threading
import os

logging.basicConfig()
LOG = logging.getLogger(__name__)
MAX_ACOS_CACHE_TIME = 60

def signal_handler(obj):
    def handler(*args):
        LOG.info("Handling signal")
        obj.__del__()
    return handler

class A10OpenstackLBBase(object):

    def __init__(self, openstack_driver,
                 plumbing_hooks_class=hooks.PlumbingHooks,
                 neutron_hooks_module=None,
                 barbican_client=None,
                 db_operations_class=operations.Operations,
                 inventory_class=inventory.InventoryBase,
                 config_name='config',
                 barbican_client=None):
        self.openstack_driver = openstack_driver
        self.config = a10_config.A10Config(config_name)
        self.neutron = neutron_hooks_module
        self.barbican_client = barbican_client
        self.acos_client_internal = None
        self.last_acos_client_creation = int(time.time())
        LOG.info("A10-neutron-lbaas: initializing, version=%s, acos_client=%s",
                 version.VERSION, acos_client.VERSION)
        self.my_lock = threading.Lock()
        if self.config.get('verify_appliances'):
            self._verify_appliances()
        self.hooks = plumbing_hooks_class(self)
        self.signal_handler_registered = False
        self.acos_clients = {}
        LOG.info("PID creating "+str(os.getpid()))

    def _select_a10_device(self, tenant_id):
        return self.hooks.select_device(tenant_id)

    def _get_a10_client(self, device_info):
        d = device_info
        d_key = d['host']+'-'+str(d['port'])

        ### The signal is registered here because in some time the process is forked
        ### So you lost variable references
        if not self.signal_handler_registered:
            signal.signal(signal.SIGTERM, signal_handler(self))
            signal.signal(signal.SIGHUP, signal_handler(self))
            signal.signal(signal.SIGINT, signal_handler(self))
            self.signal_handler_registered = True
            LOG.info("PID registering "+str(os.getpid()))

        if d_key in self.acos_clients:
            with self.my_lock:
                cli = self.acos_clients[d_key]
                if cli['last_acos_client_creation'] + MAX_ACOS_CACHE_TIME < int(time.time()):
                    LOG.info("Creating a new  acos_client");
                    acos_client = self._create_new_acos_client(cli['device_info'])
                    if acos_client is not None:
                        old_acos = cli['acos_client']
                        cli['acos_client'] = acos_client
                        cli['last_acos_client_creation'] = int(time.time())
                        self._close_old_a10_client(old_acos)
                        LOG.info("New Acos Client created successfully")
                return cli['acos_client']
        else:
            acos_client = self._create_new_acos_client(d)
            self.acos_clients[d_key] = {'device_info':d,'acos_client':acos_client,'last_acos_client_creation':int(time.time())}
            return acos_client


    def _create_new_acos_client(self, d, sleep_time_on_error=0.5):
        client = acos_client.Client(d['host'],
                          d.get('api_version', acos_client.AXAPI_21),
                          d['username'], d['password'],
                          port=d['port'], protocol=d['protocol'])
        final_client = None
        for i in range(1,10):
            if(client.session.id is not None):
                final_client = client
                break
            else:
                time.sleep(sleep_time_on_error)

        return final_client


    def _close_old_a10_client(self, a10_client,sleep_time_on_error=0.5):
        LOG.info("DELETING session")
        for i in range(1,10):
            r = a10_client.session.close() or {}
            if r.get('response',{}).get('status','') == 'OK':
                LOG.info("A10 Driver session destroyed: "+str(r))
                break
            else:
                LOG.info("A10 Driver Error closing session: "+str(r))
                time.sleep(sleep_time_on_error)

    def __del__(self):
        LOG.info("PID deletting "+str(os.getpid()))
        LOG.info("A10Driver: Deletting remaining acos sessions")
        LOG.info(self.acos_clients)
        for cli_key in self.acos_clients:
            cli = self.acos_clients[cli_key]
            threading.Thread(target=self._close_old_a10_client, args=(cli['acos_client'],)).start()
        time.sleep(10)
        LOG.info("A10Driver: Sessions deleted")

    def _verify_appliances(self):
        LOG.info("A10Driver: verifying appliances")

        if len(self.config.get_devices()) == 0:
            LOG.error("A10Driver: no configured appliances")

        for k, v in self.config.get_devices().items():
            try:
                LOG.info("A10Driver: appliance(%s) = %s", k,
                         self._get_a10_client(v).system.information())
            except Exception:
                LOG.error("A10Driver: unable to connect to configured"
                          "appliance, name=%s", k)


class A10OpenstackLBV2(A10OpenstackLBBase):

    @property
    def lb(self):
        return v2.handler_lb.LoadbalancerHandler(
            self,
            self.openstack_driver.load_balancer,
            neutron=self.neutron)

    @property
    def loadbalancer(self):
        return self.lb

    @property
    def listener(self):
        return v2.handler_listener.ListenerHandler(
            self,
            self.openstack_driver.listener,
            neutron=self.neutron,
            barbican_client=self.barbican_client)

    @property
    def pool(self):
        return v2.handler_pool.PoolHandler(
            self, self.openstack_driver.pool,
            neutron=self.neutron)

    @property
    def member(self):
        return v2.handler_member.MemberHandler(
            self,
            self.openstack_driver.member,
            neutron=self.neutron)

    @property
    def hm(self):
        return v2.handler_hm.HealthMonitorHandler(
            self,
            self.openstack_driver.health_monitor,
            neutron=self.neutron)


class A10OpenstackLBV1(A10OpenstackLBBase):

    @property
    def pool(self):
        return v1.handler_pool.PoolHandler(self)

    @property
    def vip(self):
        return v1.handler_vip.VipHandler(self)

    @property
    def member(self):
        return v1.handler_member.MemberHandler(self)

    @property
    def hm(self):
        return v1.handler_hm.HealthMonitorHandler(self)
