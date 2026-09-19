# The reverse proxy in front of gunicorn: Debian's apache2 package, so the
# configuration keeps the Debian layout (conf-enabled/, sites-enabled/) that the
# old host used and its files port as files.
#
# Only the program and its modules are in the image. The site's configuration is
# this directory, bind-mounted at /etc/apache2/sg101 by docker-compose.prod.yml,
# so a change to it is an edit and a graceful reload rather than a rebuild:
#     docker compose -f docker-compose.prod.yml exec proxy apache2ctl -k graceful

FROM debian:trixie-slim

# curl is for the health check, which requests the home page through Apache.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends apache2 ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*

# The distro's default site is dropped, and so is the catch-all access log for
# vhosts without their own: this site's vhost names its log, and a second copy
# of every line would be one more file for fail2ban to not read.
RUN set -eux; \
    a2enmod proxy proxy_http headers rewrite ssl; \
    a2dissite 000-default; \
    a2disconf other-vhosts-access-log; \
    printf '%s\n' \
        'IncludeOptional sg101/conf-enabled/*.conf' \
        'IncludeOptional sg101/sites-enabled/*.conf' \
        >> /etc/apache2/apache2.conf

EXPOSE 80 443

# apache2 itself as PID 1, not apache2ctl: the wrapper would sit between Docker
# and the server, and a stop signal would reach the wrapper instead. envvars is
# what apache2ctl would have read for us, and the run and lock directories it
# names do not exist in a fresh container.
CMD ["/bin/sh", "-c", ". /etc/apache2/envvars && mkdir -p \"$APACHE_RUN_DIR\" \"$APACHE_LOCK_DIR\" && exec apache2 -D FOREGROUND"]
