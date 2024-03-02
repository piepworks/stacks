#!/bin/bash

docker exec -it stacks_django sqlite3 /db/db.sqlite3 '.backup backup.sqlite3'
docker cp stacks_django:/db/backup.sqlite3 backup.sqlite3
gzip backup.sqlite3
s3cmd put backup.sqlite3.gz s3://tp-homeserver-backups/stacks/`date +%F`.sqlite3.gz
rm backup.sqlite3.gz
