pg_basebackup -h postgres-main-prime -U replicator -Ft -x -D - > /tmp/backup.tar


pg_basebackup -h postgres-main-prime.staging.local --username=replicator --format=t --wal-method=fetch -D - > /tmp/backup.tar
