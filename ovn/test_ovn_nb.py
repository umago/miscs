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

with api.transaction(check_error=True) as txn:
    txn.add(api.pg_del('testpg'))
