# The nightly backup job: the database dumped to one bucket, /media copied to
# another. Run once by the host's timer and gone when it exits:
#     docker compose -f docker-compose.prod.yml run --rm backup
#
# Built on the database's own image so pg_dump is always the server's version --
# a pg_dump older than the server refuses to run, and one from a distro package
# drifts. It connects over the compose network rather than through `exec`,
# because reaching into another container needs the Docker socket, which is root
# on the host.

FROM postgres:16

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends awscli ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*

COPY backup.sh /usr/local/bin/backup
COPY provision.sh /usr/local/bin/provision
COPY lifecycle-db.json /etc/sg101-backup/

# The image's own entrypoint initialises a database server; this runs a client.
ENTRYPOINT []
USER postgres
CMD ["backup"]
