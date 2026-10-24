#!/bin/sh
# Creates the role the 4CE server connects as: no superuser, no bypassing row-level
# security. PostgreSQL's image runs this once, when the data volume is first created.
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v app_password="$FOURCE_POSTGRES_APP_PASSWORD" <<'SQL'
CREATE ROLE fource_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD :'app_password';
GRANT CONNECT ON DATABASE fource TO fource_app;
SQL
