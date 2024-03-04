#!/bin/bash -x

# Ensure script stops when commands fail
set -e

mkdir -p /tmp

# Backup & compress our database to the tmp directory
sqlite3 /db/db.sqlite3 '.backup /tmp/backup.sqlite3'
gzip /tmp/backup.sqlite3

/usr/local/bin/aws s3 cp /tmp/backup.sqlite3.gz s3://tp-stacks/daily-backups/`date +%F`.sqlite.gz --endpoint=https://nyc3.digitaloceanspaces.com

# Delete the backup so it doesn't get in the way next time
rm /tmp/backup.sqlite3.gz
