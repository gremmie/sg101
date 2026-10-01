-- Prefix-matching indexes that Django creates and pgloader does not.
--
-- On PostgreSQL, Django adds a second index with varchar_pattern_ops for every
-- indexed CharField, because under a non-C collation (this database is
-- en_US.utf8) a plain btree cannot serve LIKE 'prefix%'. The conversion copies
-- MySQL's indexes, which have no equivalent, and the initial migrations are
-- applied with --fake-initial, so Django never creates them either. Without
-- these, prefix queries -- the username autocomplete over 15,227 users, for
-- one -- fall back to sequential scans.
--
-- The names are Django's own, so a later migration that expects to drop or
-- rename them still matches.
--
-- Applied by tools/pgloader/post_convert.py. Generated from a database built
-- by migrations alone; regenerate with:
--
--   docker compose exec -T postgres psql -U sg101 -d <migrations-built-db> -tA \
--     -c "SELECT indexdef || ';' FROM pg_indexes
--         WHERE schemaname='public' AND indexdef LIKE '%pattern_ops%'
--         ORDER BY tablename, indexname;"

CREATE INDEX IF NOT EXISTS accounts_illegalemail_email_a610b9e2_like ON public.accounts_illegalemail USING btree (email varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS accounts_illegalusername_username_f23e2f93_like ON public.accounts_illegalusername USING btree (username varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS accounts_pendinguser_username_4c67e046_like ON public.accounts_pendinguser USING btree (username varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS banners_campaign_slug_cda2ac58_like ON public.banners_campaign USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS contests_contest_slug_e1e3158c_like ON public.contests_contest USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS django_flatpage_url_41612362_like ON public.django_flatpage USING btree (url varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS django_site_domain_a2e37b91_like ON public.django_site USING btree (domain varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS downloads_category_slug_e97cfc11_like ON public.downloads_category USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS elsewhere_instantmessenger_slug_5a49bb85_like ON public.elsewhere_instantmessenger USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS elsewhere_instantmessengerprofile_network_id_6fb2b14d_like ON public.elsewhere_instantmessengerprofile USING btree (network_id varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS elsewhere_socialnetwork_slug_82e2a009_like ON public.elsewhere_socialnetwork USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS elsewhere_socialnetworkprofile_network_id_68310d53_like ON public.elsewhere_socialnetworkprofile USING btree (network_id varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS forums_category_slug_897e4ae3_like ON public.forums_category USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS forums_forum_slug_1262ff97_like ON public.forums_forum USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS news_category_slug_8bf24efd_like ON public.news_category USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS oembed_oembed_url_1941b473_like ON public.oembed_oembed USING btree (url varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS user_photos_photo_signature_e2c8ab5d_like ON public.user_photos_photo USING btree (signature varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS weblinks_category_slug_63daaff9_like ON public.weblinks_category USING btree (slug varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS weblinks_link_url_2d78c345_like ON public.weblinks_link USING btree (url varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS weblinks_pendinglink_url_5875d90d_like ON public.weblinks_pendinglink USING btree (url varchar_pattern_ops);
