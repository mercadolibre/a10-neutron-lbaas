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


#
# Global settings
#

# Should the driver check that A10 appliances are alive before
# successfullAy initializing?

# verify_appliances = False,

# Should the driver store some meta-info in a database?
# Needed for tenant<->appliance persistence if the number of appliances
# is changed for any reason. Setting this to true means that you will
# also need to run "a10-manage upgrade" after installing or upgrading
# the a10-neutron-lbaas package.
# Recommended for all new installs.

# use_database = False,

# The SQLAlchemy connection string to use to connect to the database.
# If None, and use_database is True, the driver will attempt to use
# the configured neutron database.

# database_connection = None,

# Sometimes we need things from neutron. We will look in the usual places,
# but this is here if you need to override the location.

# neutron_conf_dir = '/etc/neutron'

# If True, use the OpenStack lbaas member object UUID as the server name
# in ACOS. Recommended for all new installs using ACOS 4.0.0 or greater.

# member_name_use_uuid = False


#
# Main devices dictionary, containing a list of available ACOS devices.
#

devices = {
    # A sample ACOS 2.7.2 box
    # "ax2": {
    #     "host": "10.10.100.20",
    #     "port": 8443,
    #     "username": "admin",
    #     "password": "a10",
    #     "api_version": "2.1",
    # },
    # A sample ACOS 4.0.1 box
    # "ax4": {
    #     "host": "10.10.100.20",
    #     "port": 443,
    #     "username": "admin",
    #     "password": "a10",
    #     "api_version": "3.0",
    # },
    # The complete list of available options for a device entry, with
    # their default values.
    # "axN": {
    #
    # Hostname of ACOS device
    #     "host": <required>,
    #
    # Protocol and port number for AxAPI on ACOS device
    #     "protocol": "https",
    #     "port": 443,
    #
    # Admin username for ACOS device
    #     "username": <required>,
    #
    # Admin password for ACOS device
    #     "password": <required>,
    #
    # Which version of AxAPI to use; "2.1" for ACOS<3.0, and "3.0" for >=3.0
    #     "api_version": "2.1",
    #
    # status of device; True if online and ready for use
    #     "status": True,
    #
    # Set to true if you want automatic source nat on vports
    #     "autosnat": False,
    #
    # Partition method; "LSI" to put all slb's in a single shared partition,
    # or "ADP" to use a partition per tenant. Partitions are RBA style in
    # ACOS 2.x, and L3V in ACOS 4.x.
    #     "v_method": "LSI",
    #
    # If using a shared partition (v_method=LSI), then this field configures
    # which partition to use. By default, it is the main shared partition.
    #     "shared_partition": "shared",
    #
    # For nova based pool/service-group members, setting this to True will
    # cause the driver to lookup the nova server's floating ip and use that
    # for communication instead of its neutron port IP address.
    #     "use_float": False,
    #
    # Virtual servers will be created on this VRID. The VRID must already
    # be configured on the device. Example values: None, 1, 2, ...
    #     "default_virtual_server_vrid": None,
    #
    # Enable IP in IP on vports.
    #     "ipinip": False,
    #
    # Contains a list of hostnames or IP addresses that the driver will run
    # the 'ha sync' command against whenever a write operation occurs.
    #     "ha_sync_list": [],
    #
    # Enable or disable calling write memory directly after any operation that
    # changes ACOS's running state. Turning this off also disables all ha sync
    # operations, regardless of the settings in ha_sync_list.
    #     "write_memory": True,
    # },
}
