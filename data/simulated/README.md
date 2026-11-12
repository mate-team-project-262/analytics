# Movie Match — Synthetic Product Analytics Simulation

## What is included

This package contains page-oriented CSV files based on the latest **Product Analytics & Event Tracking Specification** provided in the conversation. There is no separate `backend/` folder: the events are organized by the page sections used in the specification.

The dataset is fully synthetic. It is not a production export and does not contain real users, credentials, participant tokens, or TMDB records.

## Dataset size

- 500 completed rooms / voting rounds
- 1,700 participants
- 20 unique cards per room
- 34,000 individual votes
- 69,431 CSV event/metric rows across 13 page-specific files (including lifecycle timestamps and boolean observations)
- 500 archived rounds
- Group distribution: 100 rooms with 2 participants, 175 with 3, 150 with 4, and 75 with 5
- 275 guest-hosted rooms and 225 authenticated-hosted rooms
- Date range: 2026-09-01 through 2026-11-10
- Timestamps are written in UTC (`...Z`)

## CSV files

| File | Page / section | Row grain |
|---|---|---|
| `01_landing_page.csv` | 01 — Landing page | One row per metric observation per landing-page view |
| `02_guest_create_room.csv` | 02 — GUEST Create room | One row per documented field per room-creation form view |
| `02_authenticated_create_room.csv` | 02 — AUTHENTICATED Create Room | One row per documented field per room-creation form view |
| `03_guest_host_room_invite_friends.csv` | 03 — GUEST Host room / Invite friends | One row per metric per host-room page view |
| `03_authenticated_host_room_invite_friends.csv` | 03 — AUTHENTICATED Host Room / Invite Friends | One row per metric per host-room page view |
| `06_guest_swipe_session.csv` | 06 — GUEST Swipe Session | One row per swipe/vote, plus one start and one completion timestamp row per participant |
| `06_authenticated_swipe_session.csv` | 06 — AUTHENTICATED Swipe Session | One row per swipe/vote, plus one start and one completion timestamp row per participant |
| `08_guest_results_winners.csv` | 08 — GUEST Results / Winners | Frontend observations per results view; backend winner records per guest-hosted room and winner |
| `08_authenticated_results_winners.csv` | 08 — AUTHENTICATED Results / Winners | Frontend observations per results view; backend winner records per authenticated-hosted room and winner |
| `09_sign_in.csv` | 09 — Sign in | One row per metric observation per sign-in page view |
| `10_sign_up.csv` | 10 — Sign up | One row per metric observation per sign-up page view |
| `11_home_signed_in.csv` | 11 — Home / Signed-in | One row per metric observation per home-page view |
| `12_settings.csv` | 12 — Settings | One row per metric observation per settings-page view |

The design screenshots also showed Join Room, Waiting Room, Finished / Waiting for others, About, and Explore your taste pages. Separate metric tables for those pages were not present in the supplied specification, so this package does **not** invent event metrics or CSVs for them.

## Common event schema

All CSVs use the same core columns:

- `event_id` — unique synthetic row identifier.
- `page_view_id` — groups observations belonging to the same page view or swipe session.
- `event_timestamp` — time of the event/observation in UTC.
- `event_name` — event name from the specification, preserving its spelling/capitalization.
- `event_value` — value serialized as text; use `event_value_type` to interpret it.
- `event_value_type` — `boolean`, `string`, `integer`, `json`, or `timestamp`.
- `capture_side` — `FRONTEND` or `BACKEND`, following the specification and the agreed mappings.
- `visitor_id` — generated technical key to link a visitor across pages, including before account creation. It is not a new product metric or a field confirmed in the current backend.
- `user_id` — synthetic numeric account ID; empty for guests and anonymous visitors.
- `user_type` — `ANONYMOUS`, `GUEST`, or `AUTHENTICATED`.
- `participant_id` — synthetic backend-style participant ID when a room participant exists.
- `room_id` — synthetic numeric room ID. As agreed, this is the identifier used to connect activity during the active voting round.
- `archive_session_id` — synthetic archive ID added as a post-completion enrichment key. It is not assumed to be available to the frontend during live voting.

Some page-specific rows also populate `title_id`, `room_title_id`, `interaction_method`, `is_liked`, `content_type`, `max_duration_minutes`, `participant_count`, `started_at`, `completed_at`, `card_position`, `title`, `genres_json`, `release_year`, `runtime_minutes`, `vote_average`, and `likes_count`.

### Recommended import types

- Parse `event_value` as a Boolean when `event_value_type=boolean`.
- Parse it as an integer when `event_value_type=integer`.
- Parse it as JSON when `event_value_type=json` (for example `genres_selected` and `movie_won`).
- Treat `event_value` as text when `event_value_type=string`.
- Parse timestamps as UTC.

Boolean `false` rows are intentionally retained for click metrics. They represent that the control was not used during that page view, allowing calculation of click-through rates against observed page views.

## Agreed identifier decisions

1. **Active session:** `room_id` identifies the room / active voting round.
2. **Archived session:** `archive_session_id` identifies the archive record created after completion. The backend archive ID is distinct from the active room ID.
3. **Movie/card identifiers:** `room_title_id` identifies the card in a particular room; `title_id` identifies the shared title/catalog record. The specification's ambiguous `movie_id` is represented by these two explicit IDs.
4. **Swipe start:** `swipe_session_started` uses `rooms.started_at` as the agreed approximation. The current backend does not separately store each participant's first swipe time.
5. **Swipe completion:** `swipe_session_completed` is derived from that participant's timestamp on their 20th / final vote.
6. **Streaming services:** omitted from both Guest and Authenticated Create Room data, as agreed, because no corresponding field was found in the inspected backend model/API.

## Behavioral and backend assumptions used

- Every completed round contains exactly 20 unique cards, with positions 0–19.
- Each participant votes once on every card: exactly 20 votes per participant. The backend rejects changing a saved vote.
- A round is completed only when every current participant has voted on all 20 cards.
- Participant display names are unique within each room, matching the room-join validation.
- `is_liked=true` is a like; `false` is a dislike/skip. Both are saved votes.
- A winner is any card with the maximum **positive** like count. Ties can yield multiple winners. If every card has zero likes, there is no winner.
- The generated dataset deliberately includes one all-zero round and one two-way tied-winner round to test those cases.
- `content_type` uses backend enum values `MOVIES` / `TV_SERIES`; the UI field `content_type_selected` uses `Movies` / `TV Shows`.
- `max_duration_selected` uses the UI options 90, 120, and 150 minutes.
- Selected genres are JSON arrays. An empty array means any genre, consistent with the backend preference handling.
- The default participant limit is five, so generated completed groups use 2–5 participants.

## Synthetic title catalogue

Title names, genres, release years, runtime values, and ratings included with swipe/winner records are generated fictional metadata. They are not actual TMDB results. This keeps the dataset self-contained for analysis while preserving the structure and broad constraints of the backend title model. `title_id` values are synthetic database-style IDs.

## Excluded fields and pages

- Streaming-service selection is excluded by agreement.
- `session_id` is not used as a single live-session key: use `room_id` for the active round and `archive_session_id` for the archived record.
- The event spec's `movie_id` is represented by `room_title_id` plus `title_id`.
- No event files were invented for pages without event tables in the supplied specification.
- No separate raw database tables (`users`, `rooms`, `participants`, etc.) are exported; files remain organized by documented pages as requested.

## Reproducibility

`generate_synthetic_data.py` regenerates the same CSV files using seed `20261112`. It uses only Python's standard library.
