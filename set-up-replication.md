--- prime
select * from pg_create_physical_replication_slot('replica01_slot');
select slot_name, slot_type, active, wal_status from pg_replication_slots;


pg_basebackup -h postgres-main-prime -U replicator -Ft -x -D - > /tmp/backup.tar


pg_basebackup -h postgres-main-prime.staging.local --username=replicator --format=t --wal-method=fetch -D - > /tmp/backup.tar


pg_basebackup --host postgres-main-prime.staging.local --username=replicator --format=t --wal-method=fetch --pgdata=/tmp

pg_basebackup --host postgres-main-prime.staging.local --username=replicator --format=p --wal-method=fetch --pgdata=/tmp/pg_backup


pg_resetwal --force --pgdata /postgres/data

sudo systemctl stop postgresql
sudo mv /tmp/pg_backup /postgres/data
sudo chown -R postgres:postgres /postgres/data
sudo systemctl start postgresql


# Standby
primary_conninfo = 'user=replicator port=5432 host=postgres-main-prime.staging.local application_name=db02.replicator'
primary_slot_name = 'replica01_slot'
