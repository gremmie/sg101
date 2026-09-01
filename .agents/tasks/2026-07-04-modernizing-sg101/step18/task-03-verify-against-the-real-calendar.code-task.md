# Task: Verify Against the Real Calendar

## Description
Answer, against the live Google Calendar API, the two questions no mock can
answer, then prove the whole pipeline end to end: a member submits an event, an
admin approves it, the sync button pushes it, and it appears on the SG101
calendar. Write down the Google-side setup as it is performed, because Step 21
has to reproduce it on the new host.

This is the task that decides whether Step 18 is done. Tasks 01 and 02 prove the
code does what we think Google wants; this proves Google agrees.

## Background

### Why mocks cannot close this step
Every test in tasks 01 and 02 asserts our own assumptions back at us. Two
questions are facts about Google's behavior toward a service account, and the
code has not successfully talked to Google since **2020-03-03**:

1. **`anyoneCanAddSelf`.** `calendar.py:120` sets `'anyoneCanAddSelf': True` on
   every event body. It is a guest-list feature, and service accounts have
   historically been limited around guests without domain-wide delegation. If
   Google rejects it, the insert fails — and it fails on *every* event, because
   the field is unconditional.
2. **Editing events the service account did not create.** All **1,478** existing
   events were created by Brian's account. `EDIT_APRV` and `DEL_APRV` both act on
   `event.google_id`, so if sharing the calendar with "Make changes to events"
   does not confer edit rights over pre-existing events, two of the three sync
   paths are broken for everything already on the calendar and working only for
   events created from here on.

Neither is knowable from the source. Both change the code if they come back
negative.

### The pending queue should be empty first
Brian is deleting all **32** stranded events by hand from the admin — `NEW` and
`NEW_APRV` alike — **in production as well as locally**, since Step 21 converts a
fresh production snapshot and rows deleted only in dev would come back with it.
**Confirm that is done before this task**, or the first press
of the sync button pushes six years of past gigs onto the live calendar — and
fires `notify_on_calendar()` for the **8** of them that carry
`create_forum_thread`, posting threads in `gigs` about shows that already
happened.

### Step 21 needs this written down
The new host will need the same service account, the same key file, and the same
calendar share. None of that is in the repo — it is console state. A short setup
record is the only thing that makes it reproducible.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R27)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 18` — the console checks already performed and the two probes
- Google: `developers.google.com/workspace/calendar/api/guides/auth` (service accounts)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Create a service account in Google Cloud project **786263548002** (confirmed
   alive, Calendar API enabled, 2026-08-31), generate a JSON key, and place it
   where `GCAL_CREDENTIALS_PATH` points. **The key MUST NOT be committed** —
   confirm it is covered by `.gitignore` before it exists on disk.
2. Share `i81lu3fkh57sgqqenogefd9v78@group.calendar.google.com` with the service
   account's address at **"Make changes to events"**. Brian owns the calendar.
3. **Probe 1 — `anyoneCanAddSelf`:** insert one test event and record whether the
   field is accepted, silently dropped, or rejected. Read the created event back
   and compare what Google stored against what was sent.
4. **Probe 2 — foreign event editing:** update and then delete **one existing
   event created by Brian's account**, chosen so that losing it costs nothing.
   Record whether both succeed.
5. Run the pipeline end to end against the real calendar: submit as a member,
   approve in the admin, press Synchronize, and confirm the event appears — then
   edit it and delete it through the same path.
6. Record the findings and the console setup in `STATUS.md` under the Step 18
   heading. **Findings are recorded as measured, including negative ones.**
7. If either probe is negative, make the code change it forces **and cover it
   with a unit test back in the suite**. A live probe is not a substitute for a
   regression test; it is what tells you which test to write.

## Dependencies
- Tasks 01 and 02 complete.
- Google Cloud console and Google Calendar access, as the owner of the calendar.
  **These steps are Brian's to perform** — they are account actions on his own
  Google identity, not repository changes.
- The 29 stranded `NEW` events deleted from the admin first (see Background).
- Take a database snapshot before the end-to-end run: `tools/pg_snapshot.sh`.
  The sync path writes to `Event` rows and can delete them.

## Implementation Approach
1. Confirm the key path is git-ignored, then create the service account, download
   the key, and share the calendar.
2. Run probe 1 on a throwaway event. Read it back rather than trusting the
   insert's return.
3. Run probe 2 on one deliberately chosen existing event.
4. If both pass, run the full submit → approve → sync → edit → delete cycle.
5. Write the findings and the setup steps into `STATUS.md`.
6. If a probe failed, implement the forced change, unit-test it, and re-run the
   probe.

## Acceptance Criteria

1. **The key is not in the repository**
   - Given the service account key exists at `GCAL_CREDENTIALS_PATH`
   - When `git status` and `git check-ignore` are run
   - Then the key is ignored and does not appear as an untracked file

2. **Probe 1 answered from what Google stored**
   - Given an event inserted with `anyoneCanAddSelf: True`
   - When the created event is read back from the API
   - Then it is recorded whether the field survived, was dropped, or was
     rejected — and the answer comes from the read-back, not from the insert
     appearing to succeed

3. **Probe 2 answered on a real pre-existing event**
   - Given an event created by Brian's account, already on the calendar
   - When the service account updates it and then deletes it
   - Then both outcomes are recorded, and a failure names the API error

4. **The pipeline works end to end**
   - Given a member-submitted event and an admin approval
   - When the Synchronize button is pressed
   - Then the event appears on the Google calendar, its row reaches `ON_CAL` with
     `google_id` and `google_url` populated, and it is visible in the public
     `/calendar/` iframe

5. **Edit and delete work end to end**
   - Given the event from criterion 4
   - When it is edited and then deleted through the site and re-synced
   - Then the Google calendar reflects both changes and the row is removed

6. **A negative probe produces a tested code change**
   - Given either probe returned negative
   - When the forced change is made
   - Then it is covered by a unit test in the suite, and the probe is re-run and
     passes

7. **The findings are recorded**
   - Given the probes and the end-to-end run are complete
   - When `STATUS.md` is read under `Step 18`
   - Then both probe results appear as measured, and the console setup is
     written down in enough detail for Step 21 to repeat it on the new host

## Metadata
- **Complexity**: Medium
- **Labels**: gcalendar, verification, Google Cloud setup, live probe, Step 21 input
- **Required Skills**: Google Cloud console, Google Calendar sharing, Django admin, API debugging
