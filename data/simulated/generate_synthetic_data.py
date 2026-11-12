#!/usr/bin/env python3
"""Generate deterministic synthetic Movie Match page-level analytics CSVs.

The dataset is synthetic and is not exported from the production database.
Seed: 20261112
"""
from __future__ import annotations
import csv, json, random, zipfile, shutil
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 20261112
RNG = random.Random(SEED)
OUT = Path(__file__).resolve().parent

# Canonical genre names based on the genres represented in the backend migrations.
GENRES = [
    (28, "Action"), (12, "Adventure"), (16, "Animation"), (35, "Comedy"),
    (80, "Crime"), (99, "Documentary"), (18, "Drama"), (10751, "Family"),
    (14, "Fantasy"), (36, "History"), (27, "Horror"), (10402, "Music"),
    (9648, "Mystery"), (10749, "Romance"), (878, "Science Fiction"),
    (53, "Thriller"), (10752, "War"), (37, "Western"),
]
GENRE_NAMES = [g[1] for g in GENRES]
GENRE_ID = dict(GENRES)

COMMON_COLUMNS = [
    "event_id", "page_view_id", "event_timestamp", "event_name", "event_value",
    "event_value_type", "capture_side", "visitor_id", "user_id", "user_type",
    "participant_id", "room_id", "archive_session_id", "title_id", "room_title_id",
    "interaction_method", "is_liked", "content_type", "max_duration_minutes",
    "participant_count", "started_at", "completed_at", "card_position", "title", "genres_json",
    "release_year", "runtime_minutes", "vote_average", "likes_count",
]

FILES = {
    "01_landing_page.csv": "01-Landing-page",
    "02_guest_create_room.csv": "02 - GUEST Create room",
    "03_guest_host_room_invite_friends.csv": "03 - GUEST Host room / Invite friends",
    "06_guest_swipe_session.csv": "06 — GUEST Swipe Session",
    "08_guest_results_winners.csv": "08 — GUEST Results / Winners",
    "09_sign_in.csv": "09 — Sign in",
    "10_sign_up.csv": "10 — Sign up",
    "11_home_signed_in.csv": "11 — Home / Signed-in",
    "12_settings.csv": "12 — Settings",
    "02_authenticated_create_room.csv": "02 — AUTHENTICATED Create Room",
    "03_authenticated_host_room_invite_friends.csv": "03 — AUTHENTICATED Host Room / Invite Friends",
    "06_authenticated_swipe_session.csv": "06 — AUTHENTICATED Swipe Session",
    "08_authenticated_results_winners.csv": "08 — AUTHENTICATED Results / Winners",
}

class Writer:
    def __init__(self):
        self.handles = {}
        self.writers = {}
        self.counts = Counter()
        self.seq = 0
        for filename in FILES:
            f = open(OUT / filename, "w", newline="", encoding="utf-8-sig")
            w = csv.DictWriter(f, fieldnames=COMMON_COLUMNS, extrasaction="ignore")
            w.writeheader()
            self.handles[filename] = f
            self.writers[filename] = w
    def add(self, filename, page_view_id, ts, event_name, value, value_type, side, meta=None, **extra):
        self.seq += 1
        row = {c: "" for c in COMMON_COLUMNS}
        row.update({
            "event_id": f"EV{self.seq:08d}",
            "page_view_id": page_view_id,
            "event_timestamp": iso(ts),
            "event_name": event_name,
            "event_value": encode_value(value, value_type),
            "event_value_type": value_type,
            "capture_side": side,
        })
        if meta:
            row.update({k: ("" if v is None else v) for k, v in meta.items() if k in row})
        row.update({k: ("" if v is None else v) for k, v in extra.items() if k in row})
        self.writers[filename].writerow(row)
        self.counts[filename] += 1
    def close(self):
        for f in self.handles.values(): f.close()

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def encode_value(value, value_type):
    if value is None: return ""
    if value_type == "json": return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if value_type == "boolean": return "true" if bool(value) else "false"
    if value_type == "timestamp": return iso(value) if isinstance(value, datetime) else str(value)
    return str(value)

def dt_between(start, end):
    delta = int((end-start).total_seconds())
    return start + timedelta(seconds=RNG.randint(0, max(delta, 0)))

def make_catalog(content_type, count=3000):
    adjectives = ["Silent", "Hidden", "Golden", "Forgotten", "Distant", "Broken", "Midnight", "Crimson", "Endless", "Last", "Bright", "Fading", "Secret", "Northern", "Electric", "Velvet", "Lonely", "Wild", "Parallel", "Lost", "Shattered", "Winter", "Summer", "Blue", "Paper", "Glass", "Silver", "Strange", "Quiet", "Infinite"]
    nouns = ["Harbour", "Orbit", "Garden", "Signal", "Horizon", "Promise", "Station", "Mountain", "Memory", "Kingdom", "Frequency", "Mirage", "Letter", "Voyage", "Library", "Ocean", "City", "Forest", "Lantern", "Expedition", "Echo", "Workshop", "Passage", "Symphony", "Compass", "Island", "Portrait", "Secret", "Bridge", "Sky"]
    catalog = []
    for i in range(count):
        gcount = RNG.choice([1, 2, 2, 3])
        chosen = RNG.sample(GENRES, gcount)
        if content_type == "MOVIES":
            runtime = RNG.randint(75, 175)
            title_suffix = ""
        else:
            runtime = RNG.randint(22, 65)  # average episode runtime
            title_suffix = " — The Series"
        title = f"The {RNG.choice(adjectives)} {RNG.choice(nouns)} {i+1:04d}{title_suffix}"
        catalog.append({
            "title_id": (800000 if content_type == "MOVIES" else 900000) + i + 1,
            "content_type": content_type,
            "title": title,
            "release_year": RNG.randint(1980, 2026),
            "genres": [g[1] for g in chosen],
            "genre_ids": [g[0] for g in chosen],
            "runtime_minutes": runtime,
            "vote_average": round(RNG.uniform(4.8, 9.1), 2),
            "popularity": round(RNG.uniform(3, 120), 3),
        })
    return catalog

# Build a broad synthetic catalogue so every selected filter can fill a 20-card deck.
CATALOGS = {"MOVIES": make_catalog("MOVIES"), "TV_SERIES": make_catalog("TV_SERIES")}

NAMES = ["Sofia", "Anna", "Peter", "Alex", "Maria", "Daniel", "Mia", "Oliver", "Emma", "Lucas", "Nina", "Ethan", "Lena", "Noah", "Maya", "Leo", "Ella", "Adam", "Iris", "Max", "Olivia", "Ryan", "Zoe", "Mark", "Eva", "David", "Liam", "Alice", "Sam", "Nora"]
ROOM_CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

# Session distribution requested and agreed in the conversation.
GROUP_SIZES = [2]*100 + [3]*175 + [4]*150 + [5]*75
RNG.shuffle(GROUP_SIZES)
ROOM_COUNT = 500
GUEST_HOST_COUNT = 275

# Synthetic account pool; users may return across multiple rooms.
ACCOUNT_IDS = list(range(10001, 10451))
account_visitor = {uid: f"visitor_{i+1:06d}" for i, uid in enumerate(ACCOUNT_IDS)}
next_visitor = 1
next_participant = 700001
next_room = 500001
next_room_title = 3000001
next_archive = 900001


def new_visitor():
    global next_visitor
    v = f"visitor_{next_visitor:06d}"
    next_visitor += 1
    return v

def get_account():
    # Re-use existing accounts to model returning users and group participation.
    return RNG.choice(ACCOUNT_IDS)

def sample_room_genres():
    n = RNG.choices([0, 1, 2, 3], weights=[22, 40, 30, 8])[0]
    return sorted(RNG.sample(GENRE_NAMES, n)) if n else []

def create_deck(content_type, selected_genres, max_duration):
    candidates = [t for t in CATALOGS[content_type]
        if (not selected_genres or any(g in selected_genres for g in t["genres"]))
        and t["runtime_minutes"] <= max_duration]
    if len(candidates) < 20:
        raise RuntimeError(f"Insufficient catalog candidates for {content_type} {selected_genres} {max_duration}: {len(candidates)}")
    return RNG.sample(candidates, 20)

def make_meta(visitor_id=None, user_id=None, user_type=None, participant_id=None, room_id=None, archive_session_id=None):
    return {
        "visitor_id": visitor_id,
        "user_id": user_id,
        "user_type": user_type,
        "participant_id": participant_id,
        "room_id": room_id,
        "archive_session_id": archive_session_id,
    }

def add_metric(writer, filename, page_view_id, ts, name, value, vtype, side, meta=None, **extra):
    writer.add(filename, page_view_id, ts, name, value, vtype, side, meta, **extra)

writer = Writer()
rooms = []
participants = []
participant_by_id = {}
room_records = []
created_account_conversions = []

# Determine exactly 275 guest-hosted and 225 authenticated-hosted rooms.
host_types = ["GUEST"]*GUEST_HOST_COUNT + ["AUTHENTICATED"]*(ROOM_COUNT-GUEST_HOST_COUNT)
RNG.shuffle(host_types)

# Generate sessions, participants, room settings, decks, votes and result state.
base_date = datetime(2026, 9, 1, tzinfo=timezone.utc)
for room_idx, (group_size, host_type) in enumerate(zip(GROUP_SIZES, host_types)):
    room_id = next_room + room_idx
    archive_id = next_archive + room_idx
    created_at = base_date + timedelta(days=RNG.randint(0, 70), seconds=RNG.randint(8*3600, 21*3600))
    content_type = RNG.choices(["MOVIES", "TV_SERIES"], weights=[78, 22])[0]
    genres_selected = sample_room_genres()
    max_duration = RNG.choice([90, 120, 150])
    deck = create_deck(content_type, genres_selected, max_duration)
    started_at = created_at + timedelta(minutes=RNG.randint(5, 28), seconds=RNG.randint(0, 59))
    room_code = "".join(RNG.choice(ROOM_CODE_CHARS) for _ in range(6))

    room_title_records = []
    for pos, title in enumerate(deck):
        room_title_records.append({"room_title_id": next_room_title, "position": pos, **title})
        next_room_title += 1

    room_participants = []
    room_names = RNG.sample(NAMES, group_size)
    for j in range(group_size):
        pid = next_participant
        next_participant += 1
        if j == 0:
            ptype = host_type
        else:
            ptype = "AUTHENTICATED" if RNG.random() < 0.43 else "GUEST"
        if ptype == "AUTHENTICATED":
            uid = get_account()
            vid = account_visitor[uid]
        else:
            uid = None
            vid = new_visitor()
        participant = {
            "participant_id": pid,
            "room_id": room_id,
            "archive_session_id": archive_id,
            "visitor_id": vid,
            "user_id": uid,
            "user_type": ptype,
            "display_name": room_names[j],
            "is_host": (j == 0),
        }
        room_participants.append(participant)
        participants.append(participant)
        participant_by_id[pid] = participant

    room = {
        "room_id": room_id,
        "archive_session_id": archive_id,
        "room_code": room_code,
        "host_type": host_type,
        "group_size": group_size,
        "content_type": content_type,
        "content_type_ui": "Movies" if content_type == "MOVIES" else "TV Shows",
        "genres_selected": genres_selected,
        "max_duration": max_duration,
        "created_at": created_at,
        "started_at": started_at,
        "participants": room_participants,
        "deck": room_title_records,
        "votes": [],
        "likes_by_card": {},
    }
    rooms.append(room)

# Deliberate edge cases to validate backend result logic:
# - first two-person session: everyone dislikes every card -> no winner (all cards have 0 likes)
# - second two-person session: exactly two cards tie for first -> multiple winners
rooms_2p = [r for r in rooms if r["group_size"] == 2]
zero_winner_room_id = rooms_2p[0]["room_id"]
tie_winner_room_id = rooms_2p[1]["room_id"]

for room in rooms:
    vote_times_by_participant = {}
    likes_by_card = Counter()
    for p in room["participants"]:
        participant_start = room["started_at"]  # agreed proxy: room.started_at for swipe_session_started
        first_vote_at = participant_start + timedelta(seconds=RNG.randint(10, 12*60))
        vote_times = []
        if room["room_id"] == zero_winner_room_id:
            likes = [False]*20
        elif room["room_id"] == tie_winner_room_id:
            likes = [i in (0, 1) for i in range(20)]
        else:
            personal_favs = set(RNG.sample(GENRE_NAMES, RNG.randint(2, 4)))
            likes = []
            for card in room["deck"]:
                match = bool(personal_favs.intersection(card["genres"]))
                probability = 0.55 + (0.13 if match else -0.08)
                probability = max(0.25, min(0.78, probability))
                likes.append(RNG.random() < probability)

        for i, (card, liked) in enumerate(zip(room["deck"], likes)):
            vote_ts = first_vote_at + timedelta(seconds=i*RNG.randint(22, 75) + RNG.randint(0, 18))
            if liked:
                method = "swipe_right" if RNG.random() < 0.72 else "like_button"
            else:
                method = "swipe_left" if RNG.random() < 0.72 else "dislike_button"
            vote = {
                "participant": p,
                "room": room,
                "card": card,
                "timestamp": vote_ts,
                "liked": liked,
                "method": method,
            }
            room["votes"].append(vote)
            vote_times.append(vote_ts)
            if liked:
                likes_by_card[card["room_title_id"]] += 1
        vote_times_by_participant[p["participant_id"]] = (participant_start, max(vote_times))

    room["likes_by_card"] = likes_by_card
    room["participant_times"] = vote_times_by_participant
    room["finished_at"] = max(v[1] for v in vote_times_by_participant.values()) + timedelta(seconds=RNG.randint(5, 45))
    max_likes = max(likes_by_card.values()) if likes_by_card else 0
    room["winners"] = [card for card in room["deck"] if max_likes > 0 and likes_by_card.get(card["room_title_id"], 0) == max_likes]
    room["result_participant_count"] = len(room["participants"])

# Create Landing Page visits: one record per page view, with bool metric rows.
landing_visitors = []
for room in rooms:
    host = room["participants"][0]
    landing_visitors.append((host, "guest_start_clicked" if host["user_type"] == "GUEST" else "create_room_submitted"))
    # Some invitees initially enter through the landing page; others open the invite directly.
    for p in room["participants"][1:]:
        if RNG.random() < 0.68:
            landing_visitors.append((p, "join_room_clicked"))
while len(landing_visitors) < 2500:
    landing_visitors.append((None, None))
RNG.shuffle(landing_visitors)
landing_visitors = landing_visitors[:2500]
landing_event_names = [
    "create_room_submitted", "guest_start_clicked", "join_room_clicked",
    "header_sign_in_clicked", "sign_up_clicked", "account_section_sign_in_clicked",
]
for i, (p, intended) in enumerate(landing_visitors, 1):
    pv = f"PV_LP_{i:06d}"
    ts = base_date + timedelta(days=RNG.randint(0, 71), seconds=RNG.randint(7*3600, 22*3600))
    if p:
        meta = make_meta(p["visitor_id"], p["user_id"], p["user_type"], p["participant_id"], p["room_id"], p["archive_session_id"])
        action = intended if RNG.random() < (0.88 if intended else 0.0) else None
    else:
        # Funnel/drop-off visitors not necessarily associated with a room.
        meta = make_meta(new_visitor(), None, "ANONYMOUS")
        action = RNG.choices([None]+landing_event_names, weights=[22, 13, 18, 20, 9, 10, 8])[0]
    for event_name in landing_event_names:
        add_metric(writer, "01_landing_page.csv", pv, ts, event_name, event_name == action, "boolean", "FRONTEND", meta)

# Room creation forms: one value row per documented field; streaming services intentionally removed.
room_host_page_view = {}
for idx, room in enumerate(rooms, 1):
    host = room["participants"][0]
    pv = f"PV_CREATE_{room['room_id']}"
    meta = make_meta(host["visitor_id"], host["user_id"], host["user_type"], host["participant_id"], room["room_id"], room["archive_session_id"])
    ts = room["created_at"]
    filename = "02_guest_create_room.csv" if room["host_type"] == "GUEST" else "02_authenticated_create_room.csv"
    if room["host_type"] == "GUEST":
        metrics = [
            ("guest_name_entered", host["display_name"], "string"),
            ("content_type_selected", room["content_type_ui"], "string"),
            ("genres_selected", room["genres_selected"], "json"),
            ("max_duration_selected", room["max_duration"], "integer"),
            ("create_room_submitted", True, "boolean"),
        ]
    else:
        metrics = [
            ("content_type_selected", room["content_type_ui"], "string"),
            ("genres_selected", room["genres_selected"], "json"),
            ("max_duration_selected", room["max_duration"], "integer"),
            ("create_room_clicked", True, "boolean"),
        ]
    for event_name, value, vtype in metrics:
        add_metric(writer, filename, pv, ts, event_name, value, vtype, "FRONTEND", meta,
                   content_type=room["content_type"], max_duration_minutes=room["max_duration"])

# Host room / Invite friends: one value row per documented metric.
for room in rooms:
    host = room["participants"][0]
    filename = "03_guest_host_room_invite_friends.csv" if room["host_type"] == "GUEST" else "03_authenticated_host_room_invite_friends.csv"
    pv = f"PV_HOST_{room['room_id']}"
    ts = room["created_at"] + timedelta(minutes=RNG.randint(1, 4))
    meta = make_meta(host["visitor_id"], host["user_id"], host["user_type"], host["participant_id"], room["room_id"], room["archive_session_id"])
    metrics = [
        ("room_invite_link_copied", RNG.random() < 0.73, "boolean"),
        ("room_invite_telegram_clicked", RNG.random() < 0.19, "boolean"),
        ("start_session_clicked", True, "boolean"),
        ("participant_count", room["group_size"], "integer"),
    ]
    for event_name, value, vtype in metrics:
        add_metric(writer, filename, pv, ts, event_name, value, vtype, "FRONTEND", meta,
                   participant_count=room["group_size"])

# Swipe sessions: lifecycle timestamps per participant plus 20 individual vote records.
for room in rooms:
    for p in room["participants"]:
        filename = "06_guest_swipe_session.csv" if p["user_type"] == "GUEST" else "06_authenticated_swipe_session.csv"
        pv = f"PV_SWIPE_{p['participant_id']}"
        started, completed = room["participant_times"][p["participant_id"]]
        meta = make_meta(p["visitor_id"], p["user_id"], p["user_type"], p["participant_id"], room["room_id"], room["archive_session_id"])
        add_metric(writer, filename, pv, started, "swipe_session_started", started, "timestamp", "BACKEND", meta,
                   started_at=iso(started), completed_at=iso(completed), content_type=room["content_type"])
        # room_id is the active round/session identifier; archive_session_id is post-completion enrichment.
        for vote in [v for v in room["votes"] if v["participant"]["participant_id"] == p["participant_id"]]:
            card = vote["card"]
            method = vote["method"]
            liked = vote["liked"]
            if p["user_type"] == "GUEST":
                event_name = {"swipe_right": "swipe_right", "like_button": "Like_button",
                              "swipe_left": "swipe_left", "dislike_button": "dislike_button"}[method]
                event_value = method
            else:
                event_name = "movie_liked" if liked else "movie_disliked"
                event_value = method
            add_metric(writer, filename, pv, vote["timestamp"], event_name, event_value, "string", "FRONTEND", meta,
                       title_id=card["title_id"], room_title_id=card["room_title_id"], card_position=card["position"],
                       interaction_method=method, is_liked=str(liked).lower(), content_type=room["content_type"],
                       title=card["title"], genres_json=json.dumps(card["genres"], ensure_ascii=False),
                       release_year=card["release_year"], runtime_minutes=card["runtime_minutes"], vote_average=card["vote_average"])
        add_metric(writer, filename, pv, completed, "swipe_session_completed", completed, "timestamp", "BACKEND", meta,
                   started_at=iso(started), completed_at=iso(completed), content_type=room["content_type"])

# Results / winners: frontend interactions per results page view, plus one backend winner record per winning card per room.
# The room-level movie_won record is placed in the file matching the room creator's (host's) mode.
for room in rooms:
    host = room["participants"][0]
    winner_file = "08_guest_results_winners.csv" if room["host_type"] == "GUEST" else "08_authenticated_results_winners.csv"
    host_pv = f"PV_RESULTS_{host['participant_id']}"
    for winner in room["winners"]:
        likes_count = room["likes_by_card"].get(winner["room_title_id"], 0)
        payload = {
            "movie": f"title_{winner['title_id']}",
            "title_id": winner["title_id"],
            "room_title_id": winner["room_title_id"],
            "title": winner["title"],
            "genres": winner["genres"],
            "release_year": winner["release_year"],
            "likes_count": likes_count,
        }
        meta = make_meta(host["visitor_id"], host["user_id"], host["user_type"], host["participant_id"], room["room_id"], room["archive_session_id"])
        add_metric(writer, winner_file, host_pv, room["finished_at"], "movie_won", payload, "json", "BACKEND", meta,
                   title_id=winner["title_id"], room_title_id=winner["room_title_id"], title=winner["title"],
                   genres_json=json.dumps(winner["genres"], ensure_ascii=False), release_year=winner["release_year"],
                   likes_count=likes_count)

    # Each current participant gets their own guest/authenticated results page.
    for p in room["participants"]:
        filename = "08_guest_results_winners.csv" if p["user_type"] == "GUEST" else "08_authenticated_results_winners.csv"
        pv = f"PV_RESULTS_{p['participant_id']}"
        view_ts = room["finished_at"] + timedelta(seconds=RNG.randint(10, 240))
        meta = make_meta(p["visitor_id"], p["user_id"], p["user_type"], p["participant_id"], room["room_id"], room["archive_session_id"])
        if p["user_type"] == "GUEST":
            metrics = [
                ("winner_details_clicked", RNG.random() < 0.22),
                ("sign_up_clicked", RNG.random() < 0.075),
                ("another_round_clicked", RNG.random() < 0.095),
            ]
        else:
            metrics = [
                ("winner_details_clicked", RNG.random() < 0.24),
                ("view_sessions_clicked", RNG.random() < 0.20),
                ("explore_taste_clicked", RNG.random() < 0.25),
                ("another_round_clicked", RNG.random() < 0.11),
            ]
        for event_name, value in metrics:
            add_metric(writer, filename, pv, view_ts, event_name, value, "boolean", "FRONTEND", meta)

# Sign in page: independent sign-in journeys (not every sign-in page view leads to successful authentication).
for i in range(1, 321):
    uid = RNG.choice(ACCOUNT_IDS)
    vid = account_visitor[uid]
    pv = f"PV_SIGNIN_{i:05d}"
    ts = base_date + timedelta(days=RNG.randint(0, 71), seconds=RNG.randint(7*3600, 23*3600))
    meta = make_meta(vid, None, "ANONYMOUS")
    flags = [
        ("sign_in_clicked", RNG.random() < 0.91),
        ("forgot_password_clicked", RNG.random() < 0.085),
        ("sign_up_clicked", RNG.random() < 0.105),
    ]
    for name, value in flags:
        add_metric(writer, "09_sign_in.csv", pv, ts, name, value, "boolean", "FRONTEND", meta)

# Sign-up page: include conversions from Guest Results and independent signup visits.
signup_visits = []
for room in rooms:
    for p in room["participants"]:
        if p["user_type"] == "GUEST" and RNG.random() < 0.075:
            signup_visits.append({"visitor_id": p["visitor_id"], "participant_id": p["participant_id"], "room_id": room["room_id"], "archive_session_id": room["archive_session_id"], "source": "RESULTS"})
for i in range(1, 151):
    signup_visits.append({"visitor_id": new_visitor(), "participant_id": None, "room_id": None, "archive_session_id": None, "source": "INDEPENDENT"})
RNG.shuffle(signup_visits)
converted_accounts = []
for i, visit in enumerate(signup_visits, 1):
    pv = f"PV_SIGNUP_{i:05d}"
    ts = base_date + timedelta(days=RNG.randint(0, 71), seconds=RNG.randint(8*3600, 22*3600))
    clicked_submit = RNG.random() < 0.84
    clicked_signin = (not clicked_submit) and RNG.random() < 0.55
    succeeded = clicked_submit and RNG.random() < 0.91
    new_uid = None
    if succeeded:
        new_uid = max(ACCOUNT_IDS) + i
        ACCOUNT_IDS.append(new_uid)
        account_visitor[new_uid] = visit["visitor_id"]
        converted_accounts.append(new_uid)
        if visit["participant_id"]:
            created_account_conversions.append((visit["participant_id"], new_uid, visit["visitor_id"]))
    meta = make_meta(visit["visitor_id"], new_uid, "AUTHENTICATED" if succeeded else "ANONYMOUS",
                     visit["participant_id"], visit["room_id"], visit["archive_session_id"])
    for name, value in [
        ("sign_up_clicked", clicked_submit),
        ("sign_in_from_signup_clicked", clicked_signin),
        ("sign_up_succeeded", succeeded),
    ]:
        add_metric(writer, "10_sign_up.csv", pv, ts, name, value, "boolean", "FRONTEND", meta)

# Home / Signed-in: one home visit per active account, with actions consistent with known room activity.
user_participation = defaultdict(list)
for p in participants:
    if p["user_id"] is not None:
        user_participation[p["user_id"]].append(p)
# Add converted guest participants as linked accounts only after their guest round completed.
for pid, uid, vid in created_account_conversions:
    # The guest vote rows remain guest; the account is available for later Home / Settings events.
    user_participation[uid].append({"participant_id": pid, "room_id": participant_by_id[pid]["room_id"], "visitor_id": vid, "user_id": uid, "user_type": "AUTHENTICATED", "is_host": False})

home_rows = []
for uid, plist in user_participation.items():
    # Use one or two visits per active account.
    visit_count = 1 + (1 if RNG.random() < 0.20 else 0)
    for vi in range(visit_count):
        p = RNG.choice(plist)
        pv = f"PV_HOME_{uid}_{vi+1}"
        ts = base_date + timedelta(days=RNG.randint(0, 71), seconds=RNG.randint(7*3600, 23*3600))
        meta = make_meta(account_visitor.get(uid, p["visitor_id"]), uid, "AUTHENTICATED", p["participant_id"], p["room_id"], None)
        start_flag = bool(p.get("is_host") and p.get("room_id") is not None and RNG.random() < 0.9)
        join_flag = bool(not p.get("is_host") and p.get("room_id") is not None and RNG.random() < 0.58)
        flags = [
            ("start_session_clicked", start_flag),
            ("join_room_clicked", join_flag),
            ("view_sessions_clicked", RNG.random() < 0.23),
            ("session_details_clicked", RNG.random() < 0.31),
            ("settings_clicked", RNG.random() < 0.19),
            ("explore_taste_clicked", RNG.random() < 0.26),
        ]
        for name, value in flags:
            add_metric(writer, "11_home_signed_in.csv", pv, ts, name, value, "boolean", "FRONTEND", meta)
        if any(name == "settings_clicked" and val for name, val in flags):
            home_rows.append((uid, account_visitor.get(uid, p["visitor_id"]), p["participant_id"], p["room_id"], ts))

# Settings page: only users who opened Settings from Home.
for i, (uid, vid, pid, room_id, home_ts) in enumerate(home_rows, 1):
    pv = f"PV_SETTINGS_{i:05d}"
    ts = home_ts + timedelta(seconds=RNG.randint(5, 300))
    meta = make_meta(vid, uid, "AUTHENTICATED", pid, room_id, None)
    flags = [
        ("profile_photo_upload_clicked", RNG.random() < 0.035),
        ("change_password_clicked", RNG.random() < 0.075),
        ("taste_profile_preference_changed", RNG.random() < 0.13),
        ("delete_account_clicked", RNG.random() < 0.008),
    ]
    for name, value in flags:
        add_metric(writer, "12_settings.csv", pv, ts, name, value, "boolean", "FRONTEND", meta)

writer.close()

# Data quality verification.
assert len(rooms) == 500
assert len({r["room_code"] for r in rooms}) == 500
assert Counter(r["group_size"] for r in rooms) == {2:100, 3:175, 4:150, 5:75}
assert sum(len(r["participants"]) for r in rooms) == 1700
assert sum(len(r["votes"]) for r in rooms) == 34000
assert sum(1 for r in rooms if r["room_id"] == zero_winner_room_id and not r["winners"]) == 1
assert len([r for r in rooms if r["room_id"] == tie_winner_room_id and len(r["winners"]) == 2]) == 1
for room in rooms:
    assert len(room["deck"]) == 20
    assert len({p["display_name"].casefold() for p in room["participants"]}) == room["group_size"]
    assert len({c["title_id"] for c in room["deck"]}) == 20
    assert len({c["position"] for c in room["deck"]}) == 20
    assert all(c["position"] in range(20) for c in room["deck"])
    assert all(c["runtime_minutes"] <= room["max_duration"] for c in room["deck"])
    assert all(not room["genres_selected"] or any(g in room["genres_selected"] for g in c["genres"]) for c in room["deck"])
    assert len(room["votes"]) == room["group_size"] * 20
    for p in room["participants"]:
        pvotes = [v for v in room["votes"] if v["participant"]["participant_id"] == p["participant_id"]]
        assert len(pvotes) == 20
        assert len({v["card"]["room_title_id"] for v in pvotes}) == 20
        assert all(v["participant"]["room_id"] == v["room"]["room_id"] for v in pvotes)

# Summaries for README / final response.
file_counts = {fn: sum(1 for _ in open(OUT/fn, encoding="utf-8-sig")) - 1 for fn in FILES}
with open(OUT / "DATASET_SUMMARY.txt", "w", encoding="utf-8") as f:
    f.write("Movie Match Synthetic Simulation — Quality Summary\n")
    f.write(f"Seed: {SEED}\nCompleted rooms: {len(rooms)}\nParticipants: {len(participants)}\nVotes: {sum(len(r['votes']) for r in rooms)}\n")
    f.write("Group distribution: 2=100, 3=175, 4=150, 5=75\n")
    f.write(f"Guest-hosted rooms: {GUEST_HOST_COUNT}\nAuthenticated-hosted rooms: {ROOM_COUNT-GUEST_HOST_COUNT}\n")
    f.write(f"Zero-winner edge case room_id: {zero_winner_room_id}\nTwo-way tie edge case room_id: {tie_winner_room_id}\n")
    f.write("\nCSV row counts (excluding headers):\n")
    for fn, n in file_counts.items(): f.write(f"{fn}: {n}\n")

print(json.dumps({
    "rooms": len(rooms),
    "participants": len(participants),
    "votes": sum(len(r["votes"]) for r in rooms),
    "group_distribution": dict(Counter(r["group_size"] for r in rooms)),
    "guest_hosted_rooms": GUEST_HOST_COUNT,
    "authenticated_hosted_rooms": ROOM_COUNT-GUEST_HOST_COUNT,
    "zero_winner_room_id": zero_winner_room_id,
    "tie_winner_room_id": tie_winner_room_id,
    "files": file_counts,
}, ensure_ascii=False, indent=2))
