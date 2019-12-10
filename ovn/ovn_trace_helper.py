# Copyright (C) 2019 Lucas Alvares Gomes <lucasagomes@gmail.com>
# All Rights Reserved.
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

import os

from ovsdbapp.backend.ovs_idl import connection
from ovsdbapp.backend.ovs_idl import idlutils
from ovsdbapp.schema.ovn_northbound import impl_idl
import ovs.db.idl

remote = 'unix:/usr/local/var/run/openvswitch/ovnnb_db.sock'
schema = idlutils.get_schema_helper(remote, 'OVN_Northbound')
schema.register_all()
idl = ovs.db.idl.Idl(remote, schema)
conn = connection.Connection(idl, timeout=60)
api = impl_idl.OvnNbApiIdlImpl(conn)


def _get_mac_ip_from_port(port, ip_version=4):
    addresses = port.addresses[0].split()
    return addresses[0], addresses[1 if ip_version == 4 else 2]


def _get_lsp_ls_id(lsp):
    # OpenStack saves the network name in the external_ids of the port
    net = lsp.external_ids.get('neutron:network_name')
    if not net:
        # If it's not there, let's loop thru the netowks and find it
        for net in api.ls_list().execute(check_error=True):
            if lsp in net.ports:
                net = net.name
                break
        else:
            raise Exception("Couldn't find aaaa")
    return net


def _get_lrp_from_ls(ls_id):
    ls = api.ls_get(ls_id).execute(check_error=True)
    lsp = None
    for lsp in ls.ports:
        if lsp.type == "router":
            lsp = lsp
            break
    else:
        raise Exception("Couldn't find the router port")

    lrp_id = lsp.options['router-port']
    for lrp in api._tables['Logical_Router_Port'].rows.values():
        if lrp.name == lrp_id:
            return lrp
    else:
        raise Exception("Couldn't find the router port")



def ping(src_port, dst_port, verbosity='--detailed', ip_version=4):
    src_lsp = api.lsp_get(src_port).execute(check_error=True)
    dst_lsp = api.lsp_get(dst_port).execute(check_error=True)
    ls_id = _get_lsp_ls_id(src_lsp)
    dst_ls_id = _get_lsp_ls_id(dst_lsp)

    src_mac, src_ip = _get_mac_ip_from_port(src_lsp, ip_version)
    dst_mac, dst_ip = _get_mac_ip_from_port(dst_lsp, ip_version)
    if ls_id != dst_ls_id:
        # If the ports are on different networks we need to find the
        # router port in the dst network and set the dst_mac to that router
        # interface mac
        dst_mac = _get_lrp_from_ls(ls_id).mac

    cmd = ("ovn-trace %(verbosity)s %(datapath)s 'inport == \"%(src_port)s\" "
           "&& eth.src == %(src_mac)s && ip4.src == %(src_ip)s && "
           "eth.dst == %(dst_mac)s && ip4.dst == %(dst_ip)s && ip.ttl == 32'")
    cmd = cmd % {'verbosity': verbosity, 'datapath': ls_id,
                 'src_port': src_port, 'src_mac': src_mac, 'src_ip': src_ip,
                 'dst_mac': dst_mac, 'dst_ip': dst_ip}

    print('DEBUG running: %s' % cmd)
    os.system(cmd)


ping('f94a1b72-3a42-400b-843f-83e539e217e1', '05273b59-1a8c-4548-9531-c469b1c6f97c')
