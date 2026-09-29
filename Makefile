# Shortcuts for the commands in DOCKER.md. Run `make` to list them.
#
# These are only shortcuts. DOCKER.md explains each command and when to use it.
# Restores are left out on purpose: they are destructive and have several steps,
# so follow them in DOCKER.md.
#
# Every prod-* target runs through $(DCP). Without `-f docker-compose.prod.yml`,
# a compose command quietly acts on the development stack.
#
# Optional variables:
#   svc=web          which service to follow in logs or open a shell in
#   cmd="..."        the manage.py command for manage / prod-manage
#   t="forums bio"   test labels, for test and deprecation-gate
#   label=...        a label for a snapshot
#   ip=...           an address for blocklist-add / blocklist-remove
#   all=1, days=N    what blocklist-clear removes
#
# Written for the GNU Make 3.81 that macOS ships.

DC  := docker compose
DCP := docker compose -f docker-compose.prod.yml

TEST_SETTINGS := --settings=sg101.settings.docker_test

svc ?=
cmd ?=
t ?=
label ?=
ip ?=
all ?=
days ?=

.DEFAULT_GOAL := help

.PHONY: help \
	prod-maint-on prod-maint-off prod-maint-status \
	prod-build prod-up prod-down prod-ps prod-logs prod-shell prod-bash \
	prod-manage prod-check prod-proxy-reload prod-smoke prod-browser \
	prod-backup prod-backup-drill \
	cloudflare-ranges-check firewall-plan firewall-apply firewall-check firewall-test \
	blocklist-show blocklist-add blocklist-remove blocklist-clear blocklist-test \
	up down ps logs shell bash manage psql test deprecation-gate css \
	snapshot snapshots

help: ## Show this list
	@awk 'BEGIN { FS = ":.*## " } \
		/^##@ / { printf "\n%s\n", substr($$0, 5) } \
		/^[a-zA-Z0-9_-]+:.*## / { printf "  %-24s %s\n", $$1, $$2 }' \
		$(MAKEFILE_LIST)
	@echo
	@echo "Restores are in DOCKER.md, not here: \"Backups, and restoring from them\""
	@echo "for production and \"PostgreSQL snapshots\" for development."

##@ Production (docker-compose.prod.yml)

prod-maint-on: ## Maintenance mode on: every request gets offline.html (503)
	touch var/maintenance/on

prod-maint-off: ## Maintenance mode off
	rm -f var/maintenance/on

prod-maint-status: ## Show whether maintenance mode is on
	@if [ -e var/maintenance/on ]; then echo "maintenance mode is ON"; \
	else echo "maintenance mode is off"; fi

# The backup service is in a profile, so a plain build skips it. With the
# profile set, `build` also builds the backup image. Don't use the profile with
# `up`: that would start a backup run.
prod-build: ## Build every image, including the backup image
	$(DCP) --profile backup build

prod-up: prod-build ## Build, then start the stack in the background
	$(DCP) up -d

prod-down: ## Stop the stack and keep its data
	$(DCP) down

prod-ps: ## Show each service's status and health
	$(DCP) ps

prod-logs: ## Follow logs: all services, or svc=web|proxy|worker|beat
	$(DCP) logs -f $(svc)

prod-shell: ## Django shell
	$(DCP) exec web python manage.py shell

prod-bash: ## bash in a container: web, or svc=...
	$(DCP) exec $(or $(svc),web) bash

prod-manage: ## Run a management command: cmd="..."
	@test -n "$(cmd)" || { echo 'usage: make prod-manage cmd="<command> [args]"'; exit 2; }
	$(DCP) exec web python manage.py $(cmd)

prod-check: ## Run manage.py check --deploy
	$(DCP) exec web python manage.py check --deploy

prod-proxy-reload: ## Test the Apache config, then reload it gracefully
	$(DCP) exec proxy sh -c '. /etc/apache2/envvars && apache2 -t'
	$(DCP) exec proxy apache2ctl -k graceful

prod-smoke: ## Smoke-test the stack on this machine (stop the dev stack first)
	tools/prod_smoke.sh

# Production settings only answer to surfguitar101.com, so the browser has to
# send that name to this machine. A fresh, throwaway profile does that without
# changing anything system-wide, and it has no remembered HSTS for the real
# site, which is what lets you click past the self-signed certificate.
prod-browser: ## Open Chrome on the local prod stack (macOS; throwaway profile)
	open -na "Google Chrome" --args --user-data-dir="$$(mktemp -d)" \
		--host-resolver-rules="MAP surfguitar101.com 127.0.0.1" \
		https://surfguitar101.com/

prod-backup: ## Run a backup now (the nightly timer runs the same thing)
	$(DCP) run --rm backup

prod-backup-drill: ## Test backup and restore against a local MinIO (stack up)
	tools/backup_drill.sh

##@ Origin firewall (run these from your own machine, never the VM)

# tools/origin_firewall.py explains the settings apply needs. The ranges live in
# apache/cloudflare-ranges.txt, which Apache reads too: after changing it, run
# prod-proxy-reload as well as firewall-apply.
cloudflare-ranges-check: ## Compare apache/cloudflare-ranges.txt with Cloudflare's lists
	tools/origin_firewall.py ranges-check

firewall-plan: ## Print the firewall rules the ranges file implies
	tools/origin_firewall.py plan

firewall-apply: ## Push the firewall rules to the hosting provider
	tools/origin_firewall.py apply

firewall-check: ## Compare the provider's live rules with the plan
	tools/origin_firewall.py check

firewall-test: ## Test the firewall script against a local stand-in for Linode's API
	tools/origin_firewall_test.py

##@ Cloudflare block list (run these on the VM)

# tools/cloudflare_block_list.py explains the settings; it reads them from
# secrets/cloudflare.env. An address blocked with blocklist-add never expires,
# because fail2ban does not know it is there. For a block that expires, use
# `sudo fail2ban-client set sg101-auth banip <ip>` instead.
blocklist-show: ## Every address on the block list, with its date and comment
	tools/cloudflare_block_list.py show

blocklist-add: ## Block ip=... by hand; never expires, as fail2ban never sees it
	@test -n "$(ip)" || { echo 'usage: make blocklist-add ip=<address>'; exit 2; }
	tools/cloudflare_block_list.py add $(ip)

blocklist-remove: ## Unblock ip=... at Cloudflare
	@test -n "$(ip)" || { echo 'usage: make blocklist-remove ip=<address>'; exit 2; }
	tools/cloudflare_block_list.py remove $(ip)

# fail2ban is told first, so its ban database does not go on believing the
# addresses are banned; that unbans every jail, sshd's included. Not with days=:
# an age-filtered clear only removes entries older than every bantime, and must
# leave fail2ban's live bans alone. While jaguar still writes to the list, all=1
# removes jaguar's current bans too.
blocklist-clear: ## Remove fail2ban's entries; all=1 everything, days=N older only
	@if [ -z "$(days)" ] && systemctl is-active --quiet fail2ban 2>/dev/null; then \
		sudo fail2ban-client unban --all; fi
	tools/cloudflare_block_list.py clear $(if $(all),--all) $(if $(days),--older-than $(days))

blocklist-test: ## Test the block-list script against a local stand-in for Cloudflare's API
	tools/cloudflare_block_list_test.py

##@ Development (docker-compose.yml)

up: ## Start the stack in the background
	$(DC) up -d

down: ## Stop the stack and keep the database
	$(DC) down

ps: ## Show each service's status
	$(DC) ps

logs: ## Follow logs: all services, or svc=...
	$(DC) logs -f $(svc)

shell: ## Django shell
	$(DC) exec web python manage.py shell

bash: ## bash in a container: web, or svc=...
	$(DC) exec $(or $(svc),web) bash

manage: ## Run a management command: cmd="..."
	@test -n "$(cmd)" || { echo 'usage: make manage cmd="<command> [args]"'; exit 2; }
	$(DC) exec web python manage.py $(cmd)

psql: ## PostgreSQL prompt
	$(DC) exec postgres psql -U sg101 sg101

test: ## Run the test suite, or only t="labels"
	$(DC) exec web python manage.py test $(TEST_SETTINGS) $(t)

# Running tools/deprecation_gate.sh by itself only prints the filter. The gate
# is this run of the suite with that filter applied.
deprecation-gate: ## Run the suite with deprecation warnings as errors
	$(DC) run --rm -e PYTHONWARNINGS="$$(tools/deprecation_gate.sh)" web \
		python manage.py test --noinput $(TEST_SETTINGS) $(t)

css: ## Rebuild the v3 stylesheet (commit the Sass and the output together)
	cd sg101 && npm run build:css

snapshot: ## Snapshot the database, optionally with label=...
	tools/pg_snapshot.sh dump $(label)

snapshots: ## List snapshots, newest first
	tools/pg_snapshot.sh list
