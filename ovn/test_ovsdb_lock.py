import time

from ovsdbapp.backend.ovs_idl import connection
from ovsdbapp.backend.ovs_idl import idlutils
from ovsdbapp.schema.open_vswitch import impl_idl
import ovs.db.idl

remote = 'unix:/usr/local/var/run/openvswitch/db.sock'
schema = idlutils.get_schema_helper(remote, 'Open_vSwitch')
schema.register_all()
idl = ovs.db.idl.Idl(remote, schema)
conn = connection.Connection(idl, timeout=60)
api = impl_idl.OvsdbIdl(conn)

idl.set_lock('test_lock')

while True:
    print('Lock name: %s' % idl.lock_name)
    print('Has lock: %s' % idl.has_lock)
    print('Is lock contended: %s\n' % idl.is_lock_contended)
    time.sleep(3)

