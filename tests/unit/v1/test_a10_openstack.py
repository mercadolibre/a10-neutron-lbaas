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

import test_base


class TestA10Openstack(test_base.UnitTestBaseV1):

    def test_sanity(self):
        pass

    def test_select(self):
        a = self.a._select_a10_device("first-token")
        self.a._select_a10_device("second-token")
        self.assertEqual(a, self.a._select_a10_device("first-token"))

    def test_verify(self):
        self.a._verify_appliances()
