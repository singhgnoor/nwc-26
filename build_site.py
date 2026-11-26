#!/usr/bin/env python3
"""
Build the Samarasyam 2026 portal from content/content.en.json into site/.

    python3 build_site.py                        validate, then build site/
    python3 build_site.py --check                validate only; writes nothing
    python3 build_site.py --include-unconfirmed  PREVIEW build into site-preview/ (never site/)

The build stops, with a list of every problem, if the content breaks a rule:
the schema, the identity lock, the "Well-being" spelling, official name
spellings, leftover placeholder text, unknown speaker IDs, bad or overlapping
times, broken anchors, missing asset files or malformed phone/mail links. A
failed build never touches the live site/ folder. Only speakers with status
"confirmed" or "ex-officio" are published; everyone else is held back and listed.

Standard library only; Python 3.8+.
"""
import argparse
import copy
import datetime
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import struct
import sys
from string import Template
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://iitrpr.ac.in/national-wellbeing-conclave-2026/"
TIMEZONE = "+05:30"  # IST

# ---------------------------------------------------------------------------
# Identity constants, from the Ministry (17 Nov 2026). These are the source of
# truth: the content file must match them exactly.
# ---------------------------------------------------------------------------
NAME_DEVANAGARI = "समरस्यम् 2026"            # no apostrophe
NAME_LATIN = "Samarasyam 2026"
NAME_FULL = "3rd National Well-being Conclave"
TAGLINE = "स्वस्थ मन | समरस समाज | सशक्त राष्ट्र"   # Devanagari only, never translated
THEME = "Mental Wellness, Social Harmony and Collective Development"
DATES = "6–7 December 2026"
VENUE = "Indian Institute of Technology Ropar, Rupnagar, Punjab"
HASHTAG = "#NationalWellbeingConclave"
HASHTAG_DEVANAGARI = "#समरस्यम्2026"
SLUG = "national-wellbeing-conclave-2026"
CONTACT_EMAIL = "nwc@iitrpr.ac.in"

IDENTITY = {
    "nameDevanagari": NAME_DEVANAGARI, "nameLatin": NAME_LATIN, "nameFull": NAME_FULL,
    "tagline": TAGLINE, "theme": THEME, "dates": DATES, "venue": VENUE,
    "hashtag": HASHTAG, "hashtagDevanagari": HASHTAG_DEVANAGARI, "slug": SLUG,
}
# A Hindi file translates the theme, dates and venue, but these never change.
LANGUAGE_NEUTRAL_IDENTITY = ("nameDevanagari", "nameLatin", "tagline", "hashtag", "hashtagDevanagari", "slug")

STATUSES = ("confirmed", "verbally-confirmed", "awaiting", "tbc", "ex-officio", "alternate")
PUBLISHED_STATUSES = ("confirmed", "ex-officio")
STATUS_WORDS = {  # shown next to names in PREVIEW builds only
    "confirmed": "confirmed", "ex-officio": "ex officio", "verbally-confirmed": "verbally confirmed",
    "awaiting": "awaiting confirmation", "tbc": "to be confirmed", "alternate": "alternate",
}
SESSION_TYPES = ("inaugural", "exhibition", "presentation", "panel", "symposium", "workshop",
                 "icebreaker", "breakaway", "students", "valedictory", "break", "cultural", "social")
NEARBY_GROUPS = ("close", "half", "day")
EMERGENCY_ICONS = ("medical", "phone", "helpdesk")
SOCIAL_PLATFORMS = ("facebook", "linkedin", "x", "instagram", "youtube")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
HONORIFICS = {"dr.", "prof.", "(dr.)", "shri", "sh", "sh.", "smt.", "ms.", "mr.", "mrs."}
NAV_ORDER = ("about", "programme", "speakers", "journey", "moments", "feedback", "contact")

PLACEHOLDER_PATTERNS = (
    (re.compile(r"\bTODO\b", re.I), "TODO"),
    (re.compile(r"\bTBC\b", re.I), "TBC"),
    (re.compile(r"lorem", re.I), "lorem"),
    (re.compile(r"00000"), "00000"),
    (re.compile(r"XXX", re.I), "XXX"),
    (re.compile(r"placeholder", re.I), "placeholder"),
    (re.compile(r"\bsample\b", re.I), "sample"),
    (re.compile(r"Speaker Name", re.I), "Speaker Name"),
    (re.compile(r"Designation, Institution", re.I), "Designation, Institution"),
    (re.compile(r"Name of the Chief Guest", re.I), "Name of the Chief Guest"),
    (re.compile(r">\s*(?:Designation|Institution)\s*<"), "a bare Designation/Institution label"),
    (re.compile(r"""\b(?:href|src|srcset)\s*=\s*(?:""|''|"#"|'#')"""), "an empty href/src"),
    (re.compile(r"""href\s*=\s*["']\s*javascript:""", re.I), "a javascript: link"),
    (re.compile(r"<script(?![^>]*\bsrc=)", re.I), "an inline <script> (blocked by the CSP)"),
    (re.compile(r"<style", re.I), "an inline <style> (blocked by the CSP)"),
    (re.compile(r"""\sstyle\s*=""", re.I), "a style= attribute (blocked by the CSP)"),
    (re.compile(r"""\son[a-z]+\s*=""", re.I), "an inline event handler (blocked by the CSP)"),
    (re.compile(r"\$\{?[A-Za-z_]"), "an unfilled $template variable"),
)
COMING_SOON = re.compile(r"coming soon", re.I)  # allowed only as the designed Moments state
# Official spellings (Ministry notices): Pralhad Joshi, Deepti Gaur Mukerjee.
MISSPELLINGS = ((re.compile(r"Prahlad", re.I), "Pralhad"), (re.compile(r"Mukherjee", re.I), "Mukerjee"))
WELLBEING_ALLOWED = ("#NationalWellbeingConclave", "national-wellbeing-conclave-2026", "Snehita Wellbeing Cell")
WELLBEING = re.compile(r"wellbeing", re.I)
# समरस्यम् followed by any kind of apostrophe: ' ` and the curly/accent forms U+2018, U+2019, U+00B4, U+02BC
APOSTROPHES = "'`" + chr(0x2018) + chr(0x2019) + chr(0x00B4) + chr(0x02BC)
NAME_APOSTROPHE = re.compile(re.escape(NAME_DEVANAGARI.split()[0]) + r"\s*[" + re.escape(APOSTROPHES) + "]")
ASSET_VERSION = re.compile(r"\?v=[0-9a-f]+")
TAG = re.compile(r"<[^>]*>")
# A run of Devanagari (U+0900-U+097F, plus the zero-width joiners U+200C/U+200D), e.g. "स्वस्थ मन | समरस समाज"
_DEVA = "[%s-%s%s%s]" % (chr(0x0900), chr(0x097F), chr(0x200C), chr(0x200D))
DEVANAGARI_RUN = re.compile(_DEVA + "+(?:[ |]+" + _DEVA + "+)*")
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# tel: links must be E.164 (+91 and 10 digits) or an Indian toll-free number (1800 and 7 digits).
TEL_RE = re.compile(r"^tel:(?:\+91\d{10}|1800\d{7})$")
PHOTO_SIZE = re.compile(r"^(?P<stem>.+)-(?P<size>\d+)\.webp$")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
class Opt:
    """A key that may be left out."""
    def __init__(self, inner):
        self.inner = inner


class MapOf:
    """An object whose keys are free-form IDs and whose values share one shape."""
    def __init__(self, inner):
        self.inner = inner


class Enum:
    def __init__(self, *values):
        self.values = values


TEXT = (str,)
OPT_TEXT = (str, type(None))
BOOL = (bool,)
NUMBER = (int, type(None))

SESSION = {
    "id": TEXT, "number": Opt(NUMBER), "start": TEXT, "end": OPT_TEXT, "timeLabel": Opt(OPT_TEXT),
    "type": Enum(*SESSION_TYPES), "title": TEXT, "subtitle": Opt(OPT_TEXT), "brief": Opt(OPT_TEXT),
    "outcomes": Opt([TEXT]), "venue": Opt(OPT_TEXT), "parallel": Opt(BOOL), "moderator": Opt(OPT_TEXT),
    "moderatorRole": Opt(OPT_TEXT), "speakers": Opt([TEXT]), "voteOfThanks": Opt(OPT_TEXT),
    "groups": Opt([TEXT]),
}
SESSION_DEFAULTS = {
    "number": None, "timeLabel": None, "subtitle": None, "brief": None, "outcomes": [], "venue": None,
    "parallel": False, "moderator": None, "moderatorRole": None, "speakers": [], "voteOfThanks": None,
    "groups": [],
}
SPEAKER = {
    "name": TEXT, "designation": Opt(OPT_TEXT), "institution": Opt(OPT_TEXT),
    "status": Enum(*STATUSES), "photo": Opt(OPT_TEXT), "bio": Opt(OPT_TEXT), "grid": Opt(BOOL),
}
SPEAKER_DEFAULTS = {"designation": None, "institution": None, "photo": None, "bio": None, "grid": True}
FOLIO = {"number": TEXT, "label": TEXT}
UI = {
    "skipLink": TEXT, "navLabel": TEXT, "menuOpen": TEXT, "menuClose": TEXT, "menuLabel": TEXT, "newTab": TEXT,
    "nav": {k: TEXT for k in NAV_ORDER},
    "hero": {"eyebrow": OPT_TEXT, "themeLabel": TEXT, "cta": TEXT, "artCaption": OPT_TEXT},
    "glance": {k: TEXT for k in ("heading", "datesLabel", "dates", "datesNote", "venueLabel", "venue", "venueNote",
                                 "countdownDays", "countdownDay", "countdownLive", "countdownLabel")},
    "sections": {
        "about": FOLIO,
        "benefits": {"title": TEXT},
        "programme": dict(FOLIO, title=TEXT, intro=OPT_TEXT, note=OPT_TEXT),
        "speakers": dict(FOLIO, title=TEXT, intro=OPT_TEXT, gridTitle=TEXT),
        "journey": FOLIO,
        "moments": dict(FOLIO, **{k: TEXT for k in ("title", "intro", "introLive", "soonTag", "soonTitle",
                                                    "soonText")}),
        "feedback": dict(FOLIO, **{k: TEXT for k in ("title", "intro", "closedTitle", "closedText", "closedButton",
                                                     "openTag", "openTitle", "openButton", "openNote", "qrCaption",
                                                     "qrAlt")}),
        "contact": dict(FOLIO, title=TEXT, intro=OPT_TEXT, onBehalf=TEXT),
        "nearby": {k: TEXT for k in ("label", "swipeHint", "here", "hereNote", "mapLink", "mapAria")},
    },
    "programme": {k: TEXT for k in ("tabsLabel", "session", "moderator", "speakers", "voteOfThanks",
                                    "viewSpeakers", "hideSpeakers", "details", "to", "onwards")},
    "carousel": {k: TEXT for k in ("label", "previous", "next", "position", "show")},
    "footer": {"organisedBy": TEXT, "hostedBy": TEXT, "onThisPage": TEXT, "emergency": TEXT,
               "links": {k: TEXT for k in NAV_ORDER + ("nearby",)}, "socialAria": TEXT, "copyright": TEXT},
    "typeLabels": {k: TEXT for k in SESSION_TYPES},
    "months": [TEXT],
    "notFound": {"title": TEXT, "text": TEXT, "link": TEXT},
}
SCHEMA = {
    "event": {
        "nameDevanagari": TEXT, "nameLatin": TEXT, "nameFull": TEXT, "tagline": TEXT, "theme": TEXT,
        "dates": TEXT, "startDate": TEXT, "opensAt": TEXT, "venue": TEXT, "venueShort": TEXT, "slug": TEXT,
        "hashtag": TEXT, "hashtagDevanagari": TEXT, "programmeNote": OPT_TEXT, "organisers": OPT_TEXT,
    },
    "ui": UI,
    "logos": [{"id": TEXT, "src": TEXT, "alt": TEXT, "lines": [TEXT]}],
    "about": {"heading": OPT_TEXT, "accent": OPT_TEXT, "quote": {"text": OPT_TEXT, "credit": OPT_TEXT}},
    "benefits": [{"audience": TEXT, "text": TEXT}],
    "days": [{"id": TEXT, "label": TEXT, "date": TEXT, "weekday": TEXT, "theme": OPT_TEXT,
              "dignitariesLabel": OPT_TEXT, "dignitaries": [TEXT], "sessions": [SESSION]}],
    "speakers": MapOf(SPEAKER),
    "journey": {
        "heading": OPT_TEXT, "intro": OPT_TEXT, "stats": [{"value": TEXT, "label": TEXT}], "hereLabel": TEXT,
        "milestones": [{"when": TEXT, "title": TEXT, "text": OPT_TEXT, "current": BOOL}],
    },
    "photos": {"status": Enum("coming-soon", "live"),
               "items": [{"src": TEXT, "alt": TEXT, "caption": OPT_TEXT, "label": Opt(OPT_TEXT)}]},
    "feedback": {"status": Enum("closed", "open"), "formUrl": OPT_TEXT, "qr": Opt(OPT_TEXT)},
    "contact": {"team": TEXT, "lines": [TEXT], "note": OPT_TEXT, "email": TEXT,
                "people": [{"name": TEXT, "role": OPT_TEXT, "phone": OPT_TEXT}]},
    "nearby": {
        "heading": TEXT, "subline": OPT_TEXT, "footnote": OPT_TEXT,
        "groups": [{"id": Enum(*NEARBY_GROUPS), "label": TEXT, "range": TEXT,
                    "places": [{"name": TEXT, "blurb": TEXT, "drive": TEXT, "note": OPT_TEXT,
                                "mapsQuery": TEXT}]}],
    },
    "emergency": [{"service": TEXT, "number": TEXT, "icon": Enum(*EMERGENCY_ICONS)}],
    "footer": {
        "credit": OPT_TEXT, "creditName": OPT_TEXT,
        "institute": {"namePunjabi": OPT_TEXT, "nameHindi": OPT_TEXT, "nameEnglish": TEXT, "address": OPT_TEXT,
                      "siteLabel": TEXT, "siteUrl": TEXT, "sealWhite": OPT_TEXT},
        "socials": [{"platform": Enum(*SOCIAL_PLATFORMS), "label": TEXT, "url": TEXT}],
    },
}


def check_schema(value, schema, where, errors):
    if isinstance(schema, Opt):
        schema = schema.inner
    here = where or "(top level)"
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            errors.append("%s: expected an object" % here)
            return
        for key, sub in schema.items():
            path = "%s.%s" % (where, key) if where else key
            if key not in value:
                if not isinstance(sub, Opt):
                    errors.append("%s: missing" % path)
                continue
            check_schema(value[key], sub, path, errors)
        for key in value:
            if key not in schema:
                errors.append("%s.%s: unknown key (a typo?)" % (where, key) if where else "%s: unknown key" % key)
    elif isinstance(schema, list):
        if not isinstance(value, list):
            errors.append("%s: expected a list" % here)
            return
        for i, item in enumerate(value):
            check_schema(item, schema[0], "%s[%d]" % (where, i), errors)
    elif isinstance(schema, MapOf):
        if not isinstance(value, dict):
            errors.append("%s: expected an object" % here)
            return
        for key, item in value.items():
            check_schema(item, schema.inner, "%s.%s" % (where, key), errors)
    elif isinstance(schema, Enum):
        if value not in schema.values:
            errors.append("%s: %r is not one of: %s" % (here, value, ", ".join(schema.values)))
    elif (isinstance(value, bool) and bool not in schema) or not isinstance(value, schema):
        names = " or ".join("null" if t is type(None) else {"str": "text", "int": "a whole number",
                                                             "bool": "true/false"}[t.__name__] for t in schema)
        errors.append("%s: expected %s, found %s" % (here, names, json.dumps(value, ensure_ascii=False)[:60]))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def to_minutes(hhmm):
    return int(hhmm[:2]) * 60 + int(hhmm[3:])


def is_publishable(speaker, include_unconfirmed):
    return include_unconfirmed or speaker["status"] in PUBLISHED_STATUSES


def check_asset_path(path, where, static_dir, errors):
    if path.startswith("/") or "\\" in path or ".." in path.split("/") or "://" in path:
        errors.append("%s: %r must be a path inside static/, e.g. img/speakers/name.webp" % (where, path))
    elif not os.path.isfile(os.path.join(static_dir, *path.split("/"))):
        errors.append("%s: file static/%s does not exist" % (where, path))


def tel_href(number):
    return "tel:" + re.sub(r"[^\d+]", "", number)


def walk_strings(value, where):
    if isinstance(value, str):
        yield where, value
    elif isinstance(value, dict):
        for key, item in value.items():
            for found in walk_strings(item, "%s.%s" % (where, key) if where else key):
                yield found
    elif isinstance(value, list):
        for i, item in enumerate(value):
            for found in walk_strings(item, "%s[%d]" % (where, i)):
                yield found


def validate(content, lang, static_dir):
    """Check the content and fill in defaults. Returns a list of problems (empty = valid)."""
    errors = []
    check_schema(content, SCHEMA, "", errors)
    if errors:
        return errors  # the checks below rely on the shape being right
    for day in content["days"]:
        for s in day["sessions"]:
            for key, default in SESSION_DEFAULTS.items():
                s.setdefault(key, copy.deepcopy(default))
    for sp in content["speakers"].values():
        for key, default in SPEAKER_DEFAULTS.items():
            sp.setdefault(key, default)
    content["feedback"].setdefault("qr", None)
    for item in content["photos"]["items"]:
        item.setdefault("label", None)

    ev = content["event"]
    locked = IDENTITY if lang == "en" else {k: IDENTITY[k] for k in LANGUAGE_NEUTRAL_IDENTITY}
    for key, expected in locked.items():
        if ev[key] != expected:
            errors.append("event.%s: must be exactly %r (identity lock in build_site.py), found %r"
                          % (key, expected, ev[key]))
    for where, value in walk_strings(content, ""):
        if NAME_APOSTROPHE.search(value):
            errors.append("%s: no apostrophe after समरस्यम् (write समरस्यम् 2026)" % where)
        for pattern, right in MISSPELLINGS:
            if pattern.search(value):
                errors.append("%s: the official spelling is %r: %r" % (where, right, value[:80]))
    if len(content["ui"]["months"]) != 12:
        errors.append("ui.months: must list 12 month names")
    if not TIME_RE.match(ev["opensAt"]):
        errors.append("event.opensAt: %r is not a 24-hour time like 09:30" % ev["opensAt"])

    speakers = content["speakers"]
    for sid, sp in speakers.items():
        if not ID_RE.match(sid):
            errors.append("speakers.%s: IDs use lowercase letters, digits and hyphens only" % sid)
        if not sp["name"].strip():
            errors.append("speakers.%s.name: must not be empty" % sid)
        if sp["photo"]:
            check_asset_path(sp["photo"], "speakers.%s.photo" % sid, static_dir, errors)
            if not PHOTO_SIZE.match(sp["photo"].split("/")[-1]):
                errors.append("speakers.%s.photo: name the largest export <id>-<size>.webp" % sid)

    def check_ref(sid, where):
        if sid not in speakers:
            errors.append("%s: unknown speaker ID %r (not in \"speakers\")" % (where, sid))

    for i, logo in enumerate(content["logos"]):
        check_asset_path(logo["src"], "logos[%d].src" % i, static_dir, errors)
        if not logo["alt"].strip():
            errors.append("logos[%d].alt: describe the logo (e.g. 'IIT Ropar')" % i)

    try:
        start_date = datetime.date.fromisoformat(ev["startDate"])
    except ValueError:
        errors.append("event.startDate: %r is not a date like 2026-12-06" % ev["startDate"])
        start_date = None
    if not content["days"]:
        errors.append("days: the programme needs at least one day")
    seen_days, seen_sessions, seen_numbers, previous_date = set(), set(), set(), None
    for d, day in enumerate(content["days"]):
        where_day = "days[%d] (%s)" % (d, day["id"])
        if day["id"] in seen_days or not ID_RE.match(day["id"]):
            errors.append("%s: day IDs must be unique, lowercase letters/digits/hyphens" % where_day)
        seen_days.add(day["id"])
        for i, sid in enumerate(day["dignitaries"]):
            check_ref(sid, "%s.dignitaries[%d]" % (where_day, i))
        try:
            date = datetime.date.fromisoformat(day["date"])
        except ValueError:
            errors.append("%s.date: %r is not a date like 2026-12-06" % (where_day, day["date"]))
            date = None
        if date:
            if lang == "en" and WEEKDAYS[date.weekday()] != day["weekday"]:
                errors.append("%s.weekday: %s is a %s, not %s" % (where_day, day["date"], WEEKDAYS[date.weekday()], day["weekday"]))
            if d == 0 and start_date and date != start_date:
                errors.append("%s.date: the first day must equal event.startDate (%s)" % (where_day, ev["startDate"]))
            if previous_date and date <= previous_date:
                errors.append("%s.date: days must be in date order" % where_day)
            previous_date = date
        timed = []
        for i, s in enumerate(day["sessions"]):
            where = "%s.sessions[%d] (%s)" % (where_day, i, s["id"])
            if s["id"] in seen_sessions or not ID_RE.match(s["id"]):
                errors.append("%s: session IDs must be unique, lowercase letters/digits/hyphens" % where)
            seen_sessions.add(s["id"])
            if not s["title"].strip():
                errors.append("%s.title: must not be empty" % where)
            if s["number"] is not None:
                if s["number"] < 1 or s["number"] in seen_numbers:
                    errors.append("%s.number: session numbers must be unique and positive" % where)
                seen_numbers.add(s["number"])
            ok = True
            for key in ("start", "end"):
                if s[key] is not None and not TIME_RE.match(s[key]):
                    errors.append("%s.%s: %r is not a 24-hour time like 09:30" % (where, key, s[key]))
                    ok = False
            if ok and s["end"] is not None and to_minutes(s["start"]) >= to_minutes(s["end"]):
                errors.append("%s: start %s must be before end %s" % (where, s["start"], s["end"]))
                ok = False
            if ok:
                if timed and to_minutes(s["start"]) < to_minutes(timed[-1][1]["start"]):
                    errors.append("%s: sessions must be listed in time order" % where)
                timed.append((where, s))
            for j, sid in enumerate(s["speakers"]):
                check_ref(sid, "%s.speakers[%d]" % (where, j))
            for key in ("moderator", "voteOfThanks"):
                if s[key]:
                    check_ref(s[key], "%s.%s" % (where, key))
            if s["moderatorRole"] and not s["moderator"]:
                errors.append("%s.moderatorRole: set only when there is a moderator" % where)
            if s["type"] == "break" and (s["speakers"] or s["moderator"] or s["voteOfThanks"]):
                errors.append("%s: a break has no speakers, moderator or vote of thanks" % where)
        # Overlaps: open-ended sessions (end null) count as a single moment at their start.
        for a in range(len(timed)):
            for b in range(a + 1, len(timed)):
                (wa, sa), (wb, sb) = timed[a], timed[b]
                if sa["parallel"] or sb["parallel"]:
                    continue
                a0, b0 = to_minutes(sa["start"]), to_minutes(sb["start"])
                a1 = to_minutes(sa["end"]) if sa["end"] else None
                b1 = to_minutes(sb["end"]) if sb["end"] else None
                if a1 is not None and b1 is not None:
                    clash = a0 < b1 and b0 < a1
                elif a1 is not None:
                    clash = a0 <= b0 < a1
                elif b1 is not None:
                    clash = b0 <= a0 < b1
                else:
                    clash = a0 == b0
                if clash:
                    errors.append("%s overlaps %s (mark both \"parallel\": true if intended)" % (wb, wa))

    for i, item in enumerate(content["photos"]["items"]):
        check_asset_path(item["src"], "photos.items[%d].src" % i, static_dir, errors)
        if not item["alt"].strip():
            errors.append("photos.items[%d].alt: describe the photo" % i)
    if content["photos"]["status"] == "live" and not content["photos"]["items"]:
        errors.append("photos: status is \"live\" but there are no items")
    fb = content["feedback"]
    if fb["status"] == "open":
        url = fb["formUrl"]
        if not url or not (url.startswith("https://docs.google.com/forms/") or url.startswith("https://forms.gle/")):
            errors.append("feedback.formUrl: when open, must be a Google Form link (https://docs.google.com/forms/...)")
    if fb["qr"]:
        check_asset_path(fb["qr"], "feedback.qr", static_dir, errors)
    if not EMAIL_RE.match(content["contact"]["email"]):
        errors.append("contact.email: %r is not an email address" % content["contact"]["email"])
    elif lang == "en" and content["contact"]["email"] != CONTACT_EMAIL:
        errors.append("contact.email: must be %s" % CONTACT_EMAIL)
    phones = [("contact.people[%d].phone" % i, p["phone"]) for i, p in enumerate(content["contact"]["people"])]
    phones += [("emergency[%d].number" % i, e["number"]) for i, e in enumerate(content["emergency"])]
    for where, number in phones:
        if number and not TEL_RE.match(tel_href(number)):
            errors.append("%s: %r must be +91 and 10 digits, or a 1800 toll-free number" % (where, number))

    seen_groups = set()
    for g, group in enumerate(content["nearby"]["groups"]):
        where = "nearby.groups[%d]" % g
        if group["id"] in seen_groups:
            errors.append("%s.id: %r is used twice" % (where, group["id"]))
        seen_groups.add(group["id"])
        if not group["places"]:
            errors.append("%s.places: a group needs at least one place" % where)
        for p, place in enumerate(group["places"]):
            for key in ("name", "blurb", "drive", "mapsQuery"):
                if not place[key].strip():
                    errors.append("%s.places[%d].%s: must not be empty" % (where, p, key))
            if re.search(r"birthplace", place["name"] + " " + place["blurb"], re.I):
                errors.append("%s.places[%d]: Bhagat Singh's home is his ancestral home, never his birthplace"
                              % (where, p))

    for i, social in enumerate(content["footer"]["socials"]):
        if not social["url"].startswith("https://"):
            errors.append("footer.socials[%d].url: must start with https://" % i)
    inst = content["footer"]["institute"]
    if not inst["siteUrl"].startswith("https://"):
        errors.append("footer.institute.siteUrl: must start with https://")
    if inst["sealWhite"]:
        check_asset_path(inst["sealWhite"], "footer.institute.sealWhite", static_dir, errors)
    return errors


INVARIANT_KEYS = {"id", "number", "start", "end", "type", "parallel", "moderator", "speakers", "voteOfThanks",
                  "status", "photo", "src", "date", "startDate", "opensAt", "slug", "hashtag", "hashtagDevanagari",
                  "formUrl", "email", "phone", "number", "url", "siteUrl", "mapsQuery", "icon", "platform",
                  "dignitaries", "grid", "current", "qr", "sealWhite"}


def compare_structure(en, hi, where, errors):
    """content.hi.json must have exactly the same keys and structure as the English file."""
    here = where or "(top level)"
    if isinstance(en, dict):
        if not isinstance(hi, dict):
            errors.append("hi %s: expected an object, as in the English file" % here)
            return
        for key in sorted(set(en) - set(hi)):
            errors.append("hi %s: missing key %r" % (here, key))
        for key in sorted(set(hi) - set(en)):
            errors.append("hi %s: extra key %r (not in the English file)" % (here, key))
        for key in sorted(set(en) & set(hi)):
            path = "%s.%s" % (where, key) if where else key
            # Interface text (ui.*) is all translated; elsewhere IDs, times, statuses etc. stay identical.
            if (key in INVARIANT_KEYS and not path.startswith("ui.") and not isinstance(en[key], dict)
                    and en[key] != hi[key]):
                errors.append("hi %s: must be the same as the English file (%r)" % (path, en[key]))
            else:
                compare_structure(en[key], hi[key], path, errors)
    elif isinstance(en, list):
        if not isinstance(hi, list) or len(hi) != len(en):
            errors.append("hi %s: expected a list of %d items, as in the English file" % (here, len(en)))
            return
        for i, (a, b) in enumerate(zip(en, hi)):
            compare_structure(a, b, "%s[%d]" % (where, i), errors)
    elif isinstance(en, (str, type(None))):
        if not isinstance(hi, (str, type(None))):
            errors.append("hi %s: expected text or null" % here)
    elif type(en) is not type(hi) or (isinstance(en, bool) and en != hi):
        errors.append("hi %s: must match the English file (%r)" % (here, en))


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def esc(value):
    return html.escape(value or "", quote=True)


def core_name(name):
    """'Dr. Ram Manohar Singh' -> 'Ram Manohar Singh'; 'Ms. Geeta Mehrotra and Team' -> 'Geeta Mehrotra'."""
    words = name.split(" and ")[0].replace(",", " ").split()
    return " ".join(w for w in words if w.lower() not in HONORIFICS)


def initials(name):
    words = [w for w in core_name(name).split() if w[:1].isalpha()]
    if not words:
        return ""
    return (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper()


def phone_display(number):
    """'+91-1881-231181' / '+91 1881 231181' -> '+91 1881 231181' (as the design writes them)."""
    return re.sub(r"[-\s]+", " ", number).strip()


def image_size(path):
    """(width, height) of a PNG, WebP, JPEG or SVG file, standard library only; None if unknown."""
    try:
        with open(path, "rb") as f:
            head = f.read(65536)
    except OSError:
        return None
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        chunk = head[12:16]
        if chunk == b"VP8X":
            return (int.from_bytes(head[24:27], "little") + 1, int.from_bytes(head[27:30], "little") + 1)
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", head[26:30])
            return (w & 0x3FFF, h & 0x3FFF)
        if chunk == b"VP8L":
            b = head[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return (w, h)
    if head[:2] == b"\xff\xd8":
        i = 2
        while i < len(head) - 9:
            if head[i] != 0xFF:
                i += 1
                continue
            marker = head[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                return (w, h)
            i += 2 + struct.unpack(">H", head[i + 2:i + 4])[0]
    text = head.decode("utf-8", "ignore")
    m = re.search(r'viewBox="\s*[-\d.]+[ ,]+[-\d.]+[ ,]+([\d.]+)[ ,]+([\d.]+)', text)
    if m:
        return (int(round(float(m.group(1)))), int(round(float(m.group(2)))))
    return None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
class Renderer:
    def __init__(self, content, lang, templates, include_unconfirmed, asset_version, has_hindi, static_dir):
        self.c = content
        self.ui = content["ui"]
        self.lang = lang
        self.t = templates
        self.preview = include_unconfirmed
        self.asset_version = asset_version
        self.has_hindi = has_hindi
        self.static_dir = static_dir
        self.root = "../" if lang == "hi" else ""
        self.canonical = SITE_URL + ("hi/" if lang == "hi" else "")

    # -- small helpers: every value is escaped; empty values render nothing --
    def text(self, value):
        """Escaped text; on the English page, Devanagari runs are marked lang="hi"."""
        out = esc(value)
        if self.lang != "hi":
            out = DEVANAGARI_RUN.sub(lambda m: '<span lang="hi">%s</span>' % m.group(0), out)
        return out

    def devanagari(self, value):
        return esc(value) if self.lang == "hi" else '<span lang="hi">%s</span>' % esc(value)

    @staticmethod
    def el(tag, inner, cls=None, extra=""):
        if not inner:
            return ""
        attrs = (' class="%s"' % cls if cls else "") + extra
        return "<%s%s>%s</%s>" % (tag, attrs, inner, tag.split()[0])

    def fill(self, template_name, **values):
        return self.t[template_name].substitute(**values)

    def asset(self, path):
        return "%sassets/%s?v=%s" % (self.root, path, self.asset_version)

    def size_attrs(self, path):
        size = image_size(os.path.join(self.static_dir, *path.split("/")))
        return ' width="%d" height="%d"' % size if size else ""

    @staticmethod
    def icon(name, cls=""):
        return ('<svg class="icon icon--%s%s" aria-hidden="true" focusable="false"><use href="#i-%s"></use></svg>'
                % (name, (" " + cls) if cls else "", name))

    def fmt(self, template, **values):
        """Fill {name} slots in interface wording (values are escaped)."""
        out = esc(template)
        for key, value in values.items():
            out = out.replace("{%s}" % key, esc(value))
        return out

    def folio(self, section, star=True):
        f = self.ui["sections"][section]
        text = "%s &nbsp;·&nbsp; %s" % (esc(f["number"]), self.text(f["label"])) if f.get("number") else self.text(f["label"])
        return '<p class="folio">%s<span>%s</span></p>' % (self.icon("star", "folio__star") if star else "", text)

    def date_text(self, iso, weekday=None):
        d = datetime.date.fromisoformat(iso)
        text = "%d %s %d" % (d.day, self.ui["months"][d.month - 1], d.year)
        return "%s, %s" % (weekday, text) if weekday else text

    def day_month(self, iso):
        d = datetime.date.fromisoformat(iso)
        return "%d %s" % (d.day, self.ui["months"][d.month - 1])

    def publishable(self, sid):
        return is_publishable(self.c["speakers"][sid], self.preview)

    def external(self, url, inner, cls=None, label=None):
        aria = ' aria-label="%s"' % esc(label) if label else ""
        sr = "" if label else '<span class="visually-hidden"> %s</span>' % esc(self.ui["newTab"])
        return '<a%s href="%s" target="_blank" rel="noopener noreferrer"%s>%s%s</a>' % (
            ' class="%s"' % cls if cls else "", esc(url), aria, inner, sr)

    # -- people --
    def photo_variants(self, photo):
        """[(path, size)] for <stem>-<size>.webp files that exist next to the given (largest) photo."""
        folder, name = photo.rsplit("/", 1) if "/" in photo else ("", photo)
        m = PHOTO_SIZE.match(name)
        if not m:
            return [(photo, None)]
        found = []
        disk = os.path.join(self.static_dir, *folder.split("/"))
        for entry in sorted(os.listdir(disk)):
            mm = PHOTO_SIZE.match(entry)
            if mm and mm.group("stem") == m.group("stem"):
                found.append(("%s/%s" % (folder, entry) if folder else entry, int(mm.group("size"))))
        return sorted(found, key=lambda x: x[1])

    def avatar(self, sid, size, cls="avatar", lazy=True):
        """A round portrait (or the neutral avatar) shown at `size` CSS pixels."""
        sp = self.c["speakers"][sid]
        if not sp["photo"]:
            return '<span class="%s avatar--empty" aria-hidden="true"><svg viewBox="0 0 176 176" focusable="false"><use href="#i-avatar"></use></svg></span>' % cls
        variants = self.photo_variants(sp["photo"])
        pick = next((p for p, s in variants if s and s >= size * 2), variants[-1][0])
        srcset = ", ".join("%s %dw" % (self.asset(p), s) for p, s in variants if s)
        attrs = ' srcset="%s" sizes="%dpx"' % (srcset, size) if srcset else ""
        # every portrait is below the first screen (section 03 starts far down), so all are lazy-loaded
        loading = ' loading="lazy"' if lazy else ""
        return ('<span class="%s"><img src="%s"%s alt="%s" width="%d" height="%d"%s decoding="async"></span>'
                % (cls, self.asset(pick), attrs, esc(sp["name"]), size, size, loading))

    def role_line(self, sp):
        return ", ".join(self.text(x) for x in (sp["designation"], sp["institution"]) if x)

    def status_note(self, sp):
        if sp["status"] in PUBLISHED_STATUSES:  # only reachable in PREVIEW builds
            return ""
        return ' <span class="person__status">(%s)</span>' % STATUS_WORDS[sp["status"]]

    def chip(self, sid, role=None):
        sp = self.c["speakers"][sid]
        role_html = self.el("span", self.text(role), "chip__role") if role else ""
        return ('<li class="chip%s">%s<span class="chip__text">%s<span class="chip__name">%s%s</span>%s</span></li>'
                % (" chip--role" if role else "", self.avatar(sid, 64, "avatar avatar--64"), role_html,
                   self.text(sp["name"]), self.status_note(sp), self.el("span", self.role_line(sp), "chip__meta")))

    # -- sections --
    def logo_row(self, cls, lazy=False):
        items = []
        for logo in self.c["logos"]:
            src = logo["src"]
            img = '<img class="logo__img" src="%s" alt="%s"%s%s>' % (
                self.asset(src), esc(logo["alt"]), self.size_attrs(src), ' loading="lazy" decoding="async"' if lazy else "")
            lines = "".join('<span class="logo__line logo__line--%d">%s</span>' % (i + 1, self.text(line))
                            for i, line in enumerate(logo["lines"]))
            text = '<span class="logo__text">%s</span>' % lines if lines else ""
            items.append('<li class="logo logo--%s">%s%s</li>' % (esc(logo["id"]), img, text))
        return '<ul class="%s" role="list">%s</ul>' % (cls, "".join(items))

    def header(self, nav):
        ui = self.ui
        links = "\n".join('<li><a class="nav__link" href="#%s">%s</a></li>' % (sid, self.text(label))
                          for sid, label in nav if sid != "feedback")
        menu_links = "\n".join(
            '<li><a class="menu__link" href="#%s"><span class="menu__num">%02d</span><span class="menu__label">%s</span></a></li>'
            % (sid, i + 1, self.text(label)) for i, (sid, label) in enumerate(nav))
        toggle = ""
        if self.has_hindi:
            if self.lang == "hi":
                toggle = ('<p class="lang"><a href="../" hreflang="en" lang="en">EN</a> <span aria-hidden="true">|</span> '
                          '<span aria-current="page">हिन्दी</span></p>')
            else:
                toggle = ('<p class="lang"><span aria-current="page">EN</span> <span aria-hidden="true">|</span> '
                          '<a href="hi/" hreflang="hi" lang="hi">हिन्दी</a></p>')
        feedback = ""
        if any(sid == "feedback" for sid, _ in nav):
            feedback = '<a class="btn btn--secondary btn--nav" href="#feedback">%s</a>' % self.text(ui["nav"]["feedback"])
        name = self.c["event"]["nameLatin"].rsplit(" ", 1)
        wordmark = '%s<span class="wordmark__name">%s</span> <span class="wordmark__year">%s</span>' % (
            self.icon("star", "wordmark__star"), self.text(name[0]), self.text(name[1] if len(name) > 1 else ""))
        menu_wordmark = '%s<span class="wordmark__name">%s</span>' % (self.icon("star", "wordmark__star"), self.text(name[0]))
        menu_cta = '<a class="btn btn--primary btn--block" href="#programme">%s%s</a>' % (
            self.text(ui["hero"]["cta"]), self.icon("arrow-down"))
        return self.fill("_header.html", logos=self.logo_row("logo-row"), wordmark=wordmark,
                         menu_wordmark=menu_wordmark, nav_label=esc(ui["navLabel"]), nav_links=links,
                         lang_toggle=toggle, feedback=feedback, menu_open=esc(ui["menuOpen"]),
                         menu_close=esc(ui["menuClose"]), menu_label=esc(ui["menuLabel"]), menu_links=menu_links,
                         menu_cta=menu_cta, icon_menu=self.icon("menu"), icon_close=self.icon("close"))

    def hero(self):
        ev, h = self.c["event"], self.ui["hero"]
        word, _, year = ev["nameDevanagari"].partition(" ")
        art = ('<picture><source media="(min-width: 768px)" srcset="%s">'
               '<img class="hero-art__land" src="%s" alt=""%s fetchpriority="high"></picture>'
               '<img class="hero-art__pillars" src="%s" alt=""%s>') % (
            self.asset("img/art/ascent-wide.svg"), self.asset("img/art/ascent-mobile.svg"),
            self.size_attrs("img/art/ascent-mobile.svg"), self.asset("img/art/gate-pillars.svg"),
            self.size_attrs("img/art/gate-pillars.svg"))
        return self.fill(
            "_hero.html",
            eyebrow=self.el("p", self.text(h["eyebrow"]), "hero__eyebrow"),
            name_devanagari=self.devanagari(word), year=esc(year), name_latin=self.text(ev["nameLatin"]),
            name_full=self.text(ev["nameFull"]), diamond=self.icon("diamond"), tagline=self.devanagari(ev["tagline"]),
            theme_label=self.text(h["themeLabel"]), theme=self.text(ev["theme"]), cta=self.text(h["cta"]),
            icon_down=self.icon("arrow-down"), art=art,
            caption=self.el("p", self.text(h["artCaption"]), "hero__caption", ' aria-hidden="true"'))

    def glance(self):
        g, ev, days = self.ui["glance"], self.c["event"], self.c["days"]
        start = "%sT%s:00%s" % (days[0]["date"], ev["opensAt"], TIMEZONE)
        end = "%sT23:59:59%s" % (days[-1]["date"], TIMEZONE)
        day_attrs = " ".join('data-day-%d="%s|%s"' % (i + 1, esc(d["date"]), esc(d["label"])) for i, d in enumerate(days))
        first = datetime.date.fromisoformat(days[0]["date"])
        return self.fill(
            "_glance.html", heading=self.text(g["heading"]), icon_calendar=self.icon("calendar"),
            icon_pin=self.icon("pin"), dates_label=self.text(g["datesLabel"]), dates=self.text(g["dates"]),
            dates_note=self.text(g["datesNote"]), venue_label=self.text(g["venueLabel"]), venue=self.text(g["venue"]),
            venue_note=self.text(g["venueNote"]), countdown_label=self.text(g["countdownLabel"]),
            start=esc(start), end=esc(end), start_date=esc(days[0]["date"]), day_attrs=day_attrs, label_days=esc(g["countdownDays"]),
            label_day=esc(g["countdownDay"]), label_live=esc(g["countdownLive"]),
            static_num=str(first.day), static_text=self.text("%s %d" % (self.ui["months"][first.month - 1], first.year)))

    def about(self):
        a = self.c["about"]
        if not a["heading"]:
            return ""
        accent = ""
        if a["accent"]:
            accent = '<p class="about__accent">%s<span>%s</span></p>' % (self.icon("diamond"), self.text(a["accent"]))
        quote = ""
        if a["quote"]["text"]:
            quote = ('<figure class="about__quote framed"><span class="corners" aria-hidden="true"></span>'
                     '<blockquote><p>“%s”</p></blockquote>%s</figure>') % (
                self.text(a["quote"]["text"]), self.el("figcaption", self.text(a["quote"]["credit"])))
        return self.fill("_about.html", folio=self.folio("about"), heading=self.text(a["heading"]), accent=accent,
                         quote=quote, benefits=self.benefits())

    def benefits(self):
        icons, numerals = ("users", "lamp", "map"), ("i", "ii", "iii", "iv", "v", "vi")
        items = []
        for i, b in enumerate(self.c["benefits"]):
            items.append(
                '<li class="benefit benefit--%d"><span class="benefit__hem" aria-hidden="true"></span>'
                '<div class="benefit__body"><div class="benefit__top"><span class="benefit__icon">%s</span>'
                '<span class="benefit__num" aria-hidden="true">%s</span></div>%s%s</div></li>' % (
                    i % 3 + 1, self.icon(icons[i % 3]), numerals[i % 6],
                    self.el("h3", self.text(b["audience"]), "benefit__audience"),
                    self.el("p", self.text(b["text"]), "benefit__text")))
        if not items:
            return ""
        return ('<div class="benefits"><div class="rule-head"><h2 class="rule-head__title" id="benefits-title">%s</h2>'
                '<span class="rule-head__line" aria-hidden="true"></span></div>'
                '<ul class="benefits__list" role="list">%s</ul></div>') % (
            self.text(self.ui["sections"]["benefits"]["title"]), "".join(items))

    def time_parts(self, date, s):
        """(rail html, inline html) for a session's time."""
        p = self.ui["programme"]
        t0 = '<time datetime="%sT%s%s">%s</time>' % (date, s["start"], TIMEZONE, "%s")
        if s["timeLabel"]:
            main = t0 % esc(s["timeLabel"])
            return '<span class="rail__start">%s</span>' % main, main
        start = t0 % s["start"].replace(":", ".")
        if s["end"]:
            end_t = '<time datetime="%sT%s%s">%s</time>' % (date, s["end"], TIMEZONE, s["end"].replace(":", "."))
            rail = '<span class="rail__start">%s</span><span class="rail__end">%s %s</span>' % (
                start, esc(p["to"]), end_t)
            return rail, "%s–%s" % (start, end_t)
        rail = '<span class="rail__start">%s <span class="rail__onwards">%s</span></span>' % (start, esc(p["onwards"]))
        return rail, "%s %s" % (start, esc(p["onwards"]))

    def session_people(self, s):
        """Publishable people in display order: (id, role label or None) for moderator, speakers, vote of thanks."""
        p = self.ui["programme"]
        out = []
        if s["moderator"] and self.publishable(s["moderator"]):
            out.append((s["moderator"], s["moderatorRole"] or p["moderator"], "moderator"))
        out += [(sid, None, "speaker") for sid in s["speakers"] if self.publishable(sid)]
        if s["voteOfThanks"] and self.publishable(s["voteOfThanks"]):
            out.append((s["voteOfThanks"], p["voteOfThanks"], "thanks"))
        return out

    def session(self, day, s):
        p, labels = self.ui["programme"], self.ui["typeLabels"]
        rail, inline = self.time_parts(day["date"], s)
        title = self.text(s["title"]) + ((": " + self.text(s["subtitle"])) if s["subtitle"] else "")
        if s["type"] == "break":
            # breaks are quiet rows: start time only, as in the design ("13.15  Lunch")
            if not s["timeLabel"] and s["end"]:
                start_only = '<time datetime="%sT%s%s">%s</time>' % (day["date"], s["start"], TIMEZONE, s["start"].replace(":", "."))
                rail = '<span class="rail__start">%s</span>' % start_only
                inline = start_only
            return ('<li class="tl tl--break" id="session-%s"><div class="tl__rail" aria-hidden="true">%s</div>'
                    '<span class="tl__dot" aria-hidden="true"></span>'
                    '<p class="brk"><span class="brk__time">%s</span><span class="brk__title">%s</span></p></li>') % (
                esc(s["id"]), rail, inline, title)
        tag = '<span class="tag tag--%s">%s</span>' % (esc(s["type"]), self.text(labels[s["type"]]))
        number = ""
        if s["number"] is not None:
            number = '<span class="session__number">%s %d</span>' % (self.text(p["session"]), s["number"])
        meta = '<span class="session__meta"><span class="session__when">%s</span>%s%s</span>' % (inline, tag, number)
        people = self.session_people(s)
        body_parts = [self.el("p", self.text(s["brief"]), "session__brief")]
        if s["venue"]:
            body_parts.append('<p class="session__venue">%s%s</p>' % (self.icon("pin"), self.text(s["venue"])))
        mods = [x for x in people if x[2] == "moderator"]
        spk = [x for x in people if x[2] == "speaker"]
        thanks = [x for x in people if x[2] == "thanks"]
        if mods:
            body_parts.append('<ul class="chips chips--single" role="list">%s</ul>' % "".join(self.chip(i, r) for i, r, _ in mods))
        if spk:
            body_parts.append('<h4 class="label">%s</h4><ul class="chips" role="list">%s</ul>' % (
                self.text(p["speakers"]), "".join(self.chip(i) for i, _, _ in spk)))
        if thanks:
            body_parts.append('<ul class="chips chips--single" role="list">%s</ul>' % "".join(self.chip(i, r) for i, r, _ in thanks))
        body = "".join(x for x in body_parts if x)
        wrap_open = '<li class="tl" id="session-%s"><div class="tl__rail" aria-hidden="true">%s</div>%s' % (
            esc(s["id"]), rail, self.icon("diamond", "tl__marker"))
        if not body:  # e.g. Cultural Programme: nothing to expand
            return wrap_open + ('<div class="session session--plain" data-type="%s">%s<p class="session__title">%s</p></div></li>'
                                % (esc(s["type"]), meta, title))
        stack = ""
        if people:
            faces = "".join(self.avatar(i, 44, "avatar avatar--44") for i, _, _ in people[:4])
            more = len(people) - 4
            if more > 0:
                faces += '<span class="avatar avatar--44 avatar--more" aria-hidden="true">+%d</span>' % more
            stack = '<span class="stack" aria-hidden="true">%s</span>' % faces
        hint = ('<span class="session__hint session__hint--view">%s</span>'
                '<span class="session__hint session__hint--hide">%s</span>') % (
            self.text(p["viewSpeakers"] if people else p["details"]), self.text(p["hideSpeakers"] if people else p["details"]))
        return wrap_open + self.fill("_session.html", id=esc(s["id"]), type=esc(s["type"]), meta=meta, title=title,
                                     hint=hint, stack=stack, toggle=self.icon("chevron-down"), body=body)

    def programme(self):
        sec = self.ui["sections"]["programme"]
        tabs, panels = [], []
        for i, day in enumerate(self.c["days"]):
            day_id = esc(day["id"])
            tabs.append('<a class="tab" role="tab" id="tab-%s" href="#%s" aria-controls="%s" aria-selected="%s">'
                        '<span class="tab__label">%s</span><span class="tab__date">%s</span></a>' % (
                            day_id, day_id, day_id, "true" if i == 0 else "false", self.text(day["label"]),
                            self.text(self.day_month(day["date"]))))
            sessions = "\n".join(self.session(day, s) for s in day["sessions"])
            panels.append(self.fill("_day.html", id=day_id, date=esc(day["date"]),
                                    title=self.text("%s · %s" % (day["label"], self.date_text(day["date"], day["weekday"]))),
                                    theme=self.el("p", self.text(day["theme"]), "programme__theme"), sessions=sessions))
        return self.fill("_programme.html", folio=self.folio("programme"), title=self.text(sec["title"]),
                         intro=self.el("p", self.text(sec["intro"]), "section-head__intro"),
                         note=self.el("p", self.text(sec["note"]), "section-head__note"),
                         tabs_label=esc(self.ui["programme"]["tabsLabel"]), tabs="\n".join(tabs),
                         panels="\n".join(panels),
                         footnote=self.el("p", self.text(self.c["event"]["programmeNote"]), "programme__note"))

    def day_grid(self, day):
        dignitaries = set(day["dignitaries"])
        grid, seen = [], set()
        for s in day["sessions"]:
            for sid in ([s["moderator"]] if s["moderator"] else []) + s["speakers"]:
                sp = self.c["speakers"][sid]
                if sid in seen or sid in dignitaries or not sp["grid"] or not self.publishable(sid):
                    continue
                seen.add(sid)
                grid.append(sid)
        return grid

    def speakers(self):
        sec = self.ui["sections"]["speakers"]
        intros, panels = [], []
        for i, day in enumerate(self.c["days"]):
            dig = [sid for sid in day["dignitaries"] if self.publishable(sid)]
            grid = self.day_grid(day)
            if not dig and not grid:
                continue
            d = datetime.date.fromisoformat(day["date"])
            if sec["intro"]:
                intros.append('<p class="section-head__intro" data-day="%s">%s</p>' % (esc(day["id"]), self.fmt(
                    sec["intro"], day=day["label"], weekday=day["weekday"], date=self.day_month(day["date"]))))
            parts = ['<h3 class="visually-hidden">%s</h3>' % self.text("%s · %s" % (day["label"], self.date_text(day["date"], day["weekday"])))]
            if dig:
                label = self.el("p", self.text(day["dignitariesLabel"]), "dignitary__eyebrow")
                lead = self.c["speakers"][dig[0]]
                cards = [('<div class="dignitary dignitary--lead framed"><span class="corners" aria-hidden="true"></span>'
                          '<span class="dignitary__ring">%s</span><div class="dignitary__text">%s<p class="dignitary__name">%s%s</p>%s</div></div>') % (
                    self.avatar(dig[0], 176, "avatar avatar--176"), label, self.text(lead["name"]),
                    self.status_note(lead), self.el("p", self.role_line(lead), "dignitary__role"))]
                side = []
                for sid in dig[1:]:
                    sp = self.c["speakers"][sid]
                    side.append(('<div class="dignitary dignitary--side">%s<div class="dignitary__text">%s'
                                 '<p class="dignitary__name">%s%s</p>%s</div></div>') % (
                        self.avatar(sid, 88, "avatar avatar--88"), label, self.text(sp["name"]),
                        self.status_note(sp), self.el("p", self.role_line(sp), "dignitary__role")))
                if side:
                    cards.append('<div class="dignitaries__side">%s</div>' % "".join(side))
                parts.append('<div class="dignitaries">%s</div>' % "".join(cards))
            if grid:
                cards = []
                for sid in grid:
                    sp = self.c["speakers"][sid]
                    cards.append('<li class="speaker">%s<p class="speaker__name">%s%s</p>%s%s</li>' % (
                        self.avatar(sid, 104, "avatar avatar--104"), self.text(sp["name"]), self.status_note(sp),
                        self.el("p", self.text(sp["designation"]), "speaker__designation"),
                        self.el("p", self.text(sp["institution"]), "speaker__institution")))
                parts.append('<div class="rule-head"><h3 class="rule-head__title">%s</h3><span class="rule-head__line" aria-hidden="true"></span></div>'
                             '<ul class="speaker-grid" role="list">%s</ul>' % (self.text(sec["gridTitle"]), "".join(cards)))
            panels.append('<div class="speakers__day" data-day="%s" id="speakers-%s">%s</div>' % (
                esc(day["id"]), esc(day["id"]), "".join(parts)))
        if not panels:
            return ""
        return self.fill("_speakers.html", folio=self.folio("speakers"), title=self.text(sec["title"]),
                         intros="".join(intros), panels="".join(panels))

    def journey(self):
        j = self.c["journey"]
        if not j["heading"] or not j["milestones"]:
            return ""
        stats = "".join('<li class="stat"><span class="stat__value">%s</span><span class="stat__label">%s</span></li>' % (
            self.text(s["value"]), self.text(s["label"])) for s in j["stats"])
        items = []
        for m in j["milestones"]:
            here = '<span class="pill">%s</span>' % self.text(j["hereLabel"]) if m["current"] else ""
            items.append('<li class="milestone%s">%s<p class="milestone__when">%s</p>%s<h3 class="milestone__title">%s</h3>%s</li>' % (
                " milestone--current" if m["current"] else "",
                self.icon("star" if m["current"] else "diamond", "milestone__marker"),
                self.text(m["when"]), here, self.text(m["title"]), self.el("p", self.text(m["text"]), "milestone__text")))
        profile = ('<div class="ascent__profile" aria-hidden="true"><img src="%s" alt=""%s loading="lazy" decoding="async">'
                   '<span class="pill ascent__here">%s</span></div>') % (
            self.asset("img/art/journey-profile.svg"), self.size_attrs("img/art/journey-profile.svg"),
            self.text(j["hereLabel"]))
        return self.fill("_journey.html", folio=self.folio("journey"), heading=self.text(j["heading"]),
                         intro=self.el("p", self.text(j["intro"]), "section-head__intro"),
                         stats=self.el("ul", stats, "stats", ' role="list"'), profile=profile, milestones="".join(items))

    def moments(self):
        sec, photos, car = self.ui["sections"]["moments"], self.c["photos"], self.ui["carousel"]
        if photos["status"] == "live":
            items = photos["items"]
            slides, thumbs = [], []
            total = len(items)
            for i, ph in enumerate(items):
                size = self.size_attrs(ph["src"])
                slides.append(
                    '<li class="carousel__slide" id="moment-%d" aria-roledescription="slide" aria-label="%s">'
                    '<figure><img src="%s" alt="%s"%s loading="lazy" decoding="async">'
                    '<figcaption class="carousel__caption">%s%s<span class="carousel__count" aria-hidden="true">%02d / %02d</span></figcaption>'
                    '</figure></li>' % (
                        i + 1, self.fmt(car["position"], n=str(i + 1), total=str(total)), self.asset(ph["src"]),
                        esc(ph["alt"]), size,
                        self.el("span", self.text(ph["label"]), "carousel__label"),
                        self.el("span", self.text(ph["caption"]), "carousel__text"), i + 1, total))
                thumbs.append('<li><a class="carousel__thumb" href="#moment-%d" aria-label="%s"><img src="%s" alt=""%s loading="lazy" decoding="async"></a></li>' % (
                    i + 1, self.fmt(car["show"], n=str(i + 1)), self.asset(ph["src"]), size))
            body = self.fill("_carousel.html", label=esc(car["label"]), slides="".join(slides),
                             thumbs="".join(thumbs), previous=esc(car["previous"]), next=esc(car["next"]),
                             icon_arrow=self.icon("arrow-right"))
            intro = sec["introLive"]
        else:
            prints = "".join('<span class="print print--%d"><img src="%s" alt=""%s loading="lazy" decoding="async"></span>' % (
                i, self.asset("img/art/photo-print.svg"), self.size_attrs("img/art/photo-print.svg"))
                for i in (1, 2, 3))
            body = ('<div class="soon framed"><span class="corners" aria-hidden="true"></span>'
                    '<div class="soon__prints" aria-hidden="true">%s</div><div class="soon__text">'
                    '<p class="status">%s<span>%s</span></p><h3 class="soon__title moments__soon">%s</h3><p class="soon__body">%s</p></div></div>') % (
                prints, self.icon("camera"), self.text(sec["soonTag"]), self.text(sec["soonTitle"]),
                self.text(sec["soonText"]))
            intro = sec["intro"]
        return self.fill("_moments.html", folio=self.folio("moments"), title=self.text(sec["title"]),
                         intro=self.el("p", self.text(intro), "section-head__intro"), body=body)

    def feedback(self):
        sec, fb = self.ui["sections"]["feedback"], self.c["feedback"]
        if fb["status"] == "open":
            qr = ""
            if fb["qr"]:
                qr = '<figure class="fb-open__qr"><img src="%s" alt="%s"%s><figcaption>%s</figcaption></figure>' % (
                    self.asset(fb["qr"]), esc(sec["qrAlt"]), self.size_attrs(fb["qr"]), self.text(sec["qrCaption"]))
            link = self.external(fb["formUrl"], "%s%s" % (self.text(sec["openButton"]), self.icon("external")), "btn btn--primary")
            card = ('<div class="fb-card fb-card--open"><p class="status status--open">%s</p><div class="fb-open">'
                    '<div class="fb-open__text"><h3 class="fb-open__title">%s</h3>%s<p class="fb-open__note">%s</p></div>%s</div></div>') % (
                self.text(sec["openTag"]), self.text(sec["openTitle"]), link, self.text(sec["openNote"]), qr)
        else:
            card = ('<div class="fb-card"><p class="fb-card__title">%s<span>%s</span></p><p class="fb-card__text">%s</p>'
                    '<p class="btn btn--disabled" aria-disabled="true">%s</p></div>') % (
                self.icon("clock"), self.text(sec["closedTitle"]), self.text(sec["closedText"]), self.text(sec["closedButton"]))
        return self.fill("_feedback.html", folio=self.folio("feedback"), title=self.text(sec["title"]),
                         intro=self.el("p", self.text(sec["intro"]), "feedback__intro"), card=card)

    def contact(self):
        ct, sec = self.c["contact"], self.ui["sections"]["contact"]
        lines = "".join(self.el("p", self.text(line), "contact__line contact__line--%d" % (i + 1))
                        for i, line in enumerate(ct["lines"]) if line)
        rows = []
        for p in ct["people"]:
            phone = ""
            if p["phone"]:
                phone = '<a class="contact__phone" href="%s">%s%s</a>' % (
                    esc(tel_href(p["phone"])), self.icon("phone"), self.text(phone_display(p["phone"])))
            rows.append('<li class="contact__person"><div><p class="contact__name">%s</p>%s</div>%s</li>' % (
                self.text(p["name"]), self.el("p", self.text(p["role"]), "contact__role"), phone))
        people = ""
        if rows:
            people = '<div class="contact__people"><p class="label">%s</p><ul role="list">%s</ul></div>' % (
                self.text(sec["onBehalf"]), "".join(rows))
        return self.fill("_contact.html", folio=self.folio("contact"), title=self.text(sec["title"]),
                         intro=self.el("p", self.text(sec["intro"]), "section-head__intro"), team=self.text(ct["team"]),
                         lines=lines, note=self.el("p", self.text(ct["note"]), "contact__note"),
                         email_href=esc("mailto:" + ct["email"]), email=self.text(ct["email"]),
                         icon_mail=self.icon("mail"), people=people)

    def nearby(self):
        nb, sec = self.c["nearby"], self.ui["sections"]["nearby"]
        if not nb["groups"]:
            return ""
        stops = ['<li class="route__stop route__stop--here">%s<span><strong>%s</strong><small>%s</small></span></li>' % (
            self.icon("star"), self.text(sec["here"]), self.text(sec["hereNote"]))]
        groups = []
        for g in nb["groups"]:
            stops.append('<li class="route__stop route__stop--%s"><span class="dia" aria-hidden="true"></span><span><strong>%s</strong><small>%s</small></span></li>' % (
                esc(g["id"]), self.text(g["label"]), self.text(g["range"])))
            cards = []
            for p in g["places"]:
                url = "https://www.google.com/maps/search/?api=1&query=" + quote(p["mapsQuery"], safe="")
                note = ""
                if p["note"]:
                    note = '<p class="place__note">%s<span>%s</span></p>' % (self.icon("clock"), self.text(p["note"]))
                link = self.external(url, "%s%s" % (self.text(sec["mapLink"]), self.icon("external")), "place__map",
                                     label="%s %s" % (sec["mapAria"].replace("{place}", p["name"]), self.ui["newTab"]))
                cards.append('<li class="place place--%s"><span class="place__accent" aria-hidden="true"></span>'
                             '<p class="place__drive">%s<span>%s</span></p><h4 class="place__name">%s</h4>'
                             '<p class="place__blurb">%s</p>%s<span class="place__spacer" aria-hidden="true"></span>%s</li>' % (
                                 esc(g["id"]), self.icon("road"), self.text(p["drive"]), self.text(p["name"]),
                                 self.text(p["blurb"]), note, link))
            groups.append('<section class="nearby__group nearby__group--%s" aria-labelledby="nearby-%s">'
                          '<h3 class="nearby__group-title" id="nearby-%s"><span class="dia" aria-hidden="true"></span>%s'
                          '<span class="nearby__range"> · %s</span></h3><ul class="nearby__list" role="list">%s</ul></section>' % (
                              esc(g["id"]), esc(g["id"]), esc(g["id"]), self.text(g["label"]), self.text(g["range"]),
                              "".join(cards)))
        route = '<ol class="route" role="list">%s</ol>' % "".join(stops)
        return self.fill("_nearby.html", folio=self.folio("nearby"), heading=self.text(nb["heading"]),
                         subline=self.el("p", self.text(nb["subline"]), "section-head__intro"), route=route,
                         hint='<p class="nearby__hint" aria-hidden="true">%s%s</p>' % (self.text(sec["swipeHint"]), self.icon("arrow-right")),
                         groups="".join(groups), footnote=self.el("p", self.text(nb["footnote"]), "nearby__footnote"))

    def footer(self, links):
        ev, f, ui = self.c["event"], self.c["footer"], self.ui["footer"]
        emergency = "".join(
            '<li class="help">%s<span><span class="help__service">%s</span><a class="help__number" href="%s">%s</a></span></li>' % (
                self.icon(e["icon"]), self.text(e["service"]), esc(tel_href(e["number"])), self.text(phone_display(e["number"])))
            for e in self.c["emergency"])
        link_items = "".join('<li><a href="#%s">%s</a></li>' % (sid, self.text(ui["links"][key])) for key, sid in links)
        inst = f["institute"]
        seal = ""
        if inst["sealWhite"]:
            seal = '<img class="site-footer__seal" src="%s" alt="%s"%s loading="lazy" decoding="async">' % (
                self.asset(inst["sealWhite"]), esc(inst["nameEnglish"]), self.size_attrs(inst["sealWhite"]))
        punjabi = self.el("p", esc(inst["namePunjabi"]), "site-footer__pa", ' lang="pa"')
        socials = "".join('<li>%s</li>' % self.external(s["url"], self.icon("social-" + s["platform"]), "social",
                                                          label="%s %s" % (ui["socialAria"].replace("{platform}", s["label"]), self.ui["newTab"]))
                          for s in f["socials"])
        credit = ""
        if f["credit"]:
            credit = '<p class="site-footer__credit">%s%s</p>' % (
                self.text(f["credit"]), (" " + self.el("strong", self.text(f["creditName"]))) if f["creditName"] else "")
        hashtags = " ".join(self.el("span", self.text(h)) for h in (ev["hashtagDevanagari"], ev["hashtag"]) if h)
        return self.fill(
            "_footer.html", organised_by=self.text(ui["organisedBy"]), hosted_by=self.text(ui["hostedBy"]),
            logos_org=self.logo_row("logo-row logo-row--footer", lazy=True), star=self.icon("star"),
            name=self.text(ev["nameLatin"]), name_line="%s &nbsp;·&nbsp; %s" % (self.devanagari(ev["nameDevanagari"]), self.text(ev["nameFull"])),
            tagline=self.devanagari(ev["tagline"]), theme=self.text(ev["theme"]),
            when="%s &nbsp;·&nbsp; %s" % (self.text(ev["dates"]), self.text(ev["venueShort"])),
            organisers=self.el("p", self.text(ev["organisers"]), "site-footer__organisers"), hashtags=hashtags,
            on_this_page=self.text(ui["onThisPage"]), links=link_items, emergency_title=self.text(ui["emergency"]),
            emergency=emergency, seal=seal, punjabi=punjabi,
            hindi=self.el("p", self.devanagari(inst["nameHindi"]) if inst["nameHindi"] else "", "site-footer__hi"),
            english=self.text(inst["nameEnglish"]), address=self.el("p", self.text(inst["address"]), "site-footer__address"),
            socials=socials, site=self.external(inst["siteUrl"], "%s%s" % (self.text(inst["siteLabel"]), self.icon("external")), "site-footer__site"),
            copyright=self.text(ui["copyright"]), credit=credit)

    def head_values(self):
        ev = self.c["event"]
        alternates = ""
        if self.has_hindi:
            alternates = ('<link rel="alternate" hreflang="en" href="%s">\n<link rel="alternate" hreflang="hi" '
                          'href="%shi/">' % (SITE_URL, SITE_URL))
        og_alt = "%s · %s · %s · %s" % (ev["nameDevanagari"], ev["nameLatin"], ev["nameFull"], ev["dates"])
        return {
            "lang": self.lang, "root": self.root, "asset_version": self.asset_version,
            "title": esc("%s · %s · IIT Ropar" % (ev["nameLatin"], ev["nameFull"])),
            "description": esc("%s. %s, %s." % (ev["theme"], ev["dates"], ev["venue"])),
            "canonical": esc(self.canonical), "alternates": alternates,
            "og_locale": "hi_IN" if self.lang == "hi" else "en_IN",
            "og_image": esc(SITE_URL + "assets/img/og-image.png"), "og_image_alt": esc(og_alt),
            "robots_meta": '<meta name="robots" content="noindex, nofollow">' if self.preview else "",
        }

    def index(self):
        sections = [("about", self.about()), ("programme", self.programme()), ("speakers", self.speakers()),
                    ("journey", self.journey()), ("moments", self.moments()), ("feedback", self.feedback()),
                    ("contact", self.contact())]
        present = {sid for sid, markup in sections if markup}
        nav = [(sid, self.ui["nav"][sid]) for sid in NAV_ORDER if sid in present]
        nearby = self.nearby()
        links = [(key, key) for key in NAV_ORDER if key in present] + ([("nearby", "nearby")] if nearby else [])
        banner = ""
        if self.preview:
            banner = ('<p class="preview-banner" role="note"><strong>PREVIEW</strong>: this build includes '
                      'speakers who are not yet confirmed. Do not share or publish it.</p>')
        values = dict(self.head_values(), skip_link=self.text(self.ui["skipLink"]), preview_banner=banner,
                      sprite=self.t["_sprite.html"].template, header=self.header(nav), hero=self.hero(),
                      glance=self.glance(), nearby=nearby, footer=self.footer(links), **dict(sections))
        return self.fill("base.html", **values)

    def not_found(self):
        nf = self.ui["notFound"]
        return self.fill("404.html", **dict(self.head_values(), title=esc("%s · %s" % (nf["title"], self.c["event"]["nameLatin"])),
                                             heading=self.text(nf["title"]), text=self.text(nf["text"]),
                                             link=self.text(nf["link"])))


# ---------------------------------------------------------------------------
# Output checks
# ---------------------------------------------------------------------------
HREF_ANCHOR = re.compile(r'href="#([^"]*)"')
ID_ATTR = re.compile(r'\bid="([^"]+)"')
LOCAL_REF = re.compile(r'(?:src|href)="((?:\.\./)?assets/[^"?#]+)')
SRCSET = re.compile(r'srcset="([^"]+)"')
TEL_LINK = re.compile(r'href="(tel:[^"]*)"')
MAILTO = re.compile(r'href="mailto:([^"]*)"')
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")


def scan_outputs(outputs, held_back_names, static_dir=None, allowed=()):
    errors = []
    for name, text in sorted(outputs.items()):
        body = ASSET_VERSION.sub("", text)
        for pattern, label in PLACEHOLDER_PATTERNS:
            for m in pattern.finditer(body):
                errors.append("site/%s: contains %s: ...%s..." % (name, label, context(body, m.start())))
        reader = body
        for phrase in allowed:  # designed states, e.g. the Moments "Coming soon" card
            reader = reader.replace(">%s<" % esc(phrase), "><")
        for m in COMING_SOON.finditer(reader):
            errors.append("site/%s: contains \"coming soon\" outside the designed Moments state: ...%s..."
                          % (name, context(reader, m.start())))
        text = html.unescape(TAG.sub("", body))  # what a reader sees
        for source in (body, text):
            visible = source
            for allowed_word in WELLBEING_ALLOWED:
                visible = visible.replace(allowed_word, "")
            for m in WELLBEING.finditer(visible):
                errors.append("site/%s: spell it \"well-being\" (with the hyphen): ...%s..." % (name, context(visible, m.start())))
            for m in NAME_APOSTROPHE.finditer(source):
                errors.append("site/%s: no apostrophe after समरस्यम्: ...%s..." % (name, context(source, m.start())))
        for pattern, right in MISSPELLINGS:
            for m in pattern.finditer(html.unescape(body)):
                errors.append("site/%s: the official spelling is %r: ...%s..." % (name, right, context(html.unescape(body), m.start())))
        for person in held_back_names:
            if person and (person in text or person in html.unescape(body)):
                errors.append("site/%s: mentions %r, who is held back (not confirmed)" % (name, person))
        if name.endswith(".html"):
            errors += check_links(name, body, static_dir)
    return errors


def check_links(name, body, static_dir):
    """Internal anchors resolve, local assets exist, tel:/mailto: links are well formed."""
    errors = []
    ids = set(ID_ATTR.findall(body))
    for target in HREF_ANCHOR.findall(body):
        if not target:
            errors.append("site/%s: an empty href=\"#\"" % name)
        elif target not in ids:
            errors.append("site/%s: href=\"#%s\" has no matching id=\"%s\"" % (name, target, target))
    for tel in TEL_LINK.findall(body):
        if not TEL_RE.match(tel):
            errors.append("site/%s: %s is not a valid E.164 (+91...) or 1800 toll-free number" % (name, tel))
    for mail in MAILTO.findall(body):
        if mail != CONTACT_EMAIL:
            errors.append("site/%s: mailto:%s must be mailto:%s" % (name, mail, CONTACT_EMAIL))
    if static_dir:
        refs = LOCAL_REF.findall(body)
        for srcset in SRCSET.findall(body):
            refs += [part.strip().split()[0] for part in srcset.split(",") if part.strip()]
        for ref in refs:
            path = ASSET_VERSION.sub("", ref.split("?")[0])
            path = path[3:] if path.startswith("../") else path
            if not path.startswith("assets/"):
                continue
            if not os.path.isfile(os.path.join(static_dir, *path[len("assets/"):].split("/"))):
                errors.append("site/%s: %s does not exist (static/%s)" % (name, ref, path[len("assets/"):]))
    return errors


def check_css(static_dir):
    """Every url() in the stylesheets resolves to a file in static/."""
    errors = []
    css_dir = os.path.join(static_dir, "css")
    if not os.path.isdir(css_dir):
        return errors
    for name in sorted(os.listdir(css_dir)):
        if not name.endswith(".css"):
            continue
        with open(os.path.join(css_dir, name), encoding="utf-8") as f:
            css = f.read()
        for ref in CSS_URL.findall(css):
            if ref.startswith("data:") or ref.startswith("#"):
                continue
            if "://" in ref or ref.startswith("/"):
                errors.append("static/css/%s: url(%s) must be a relative path to a local file" % (name, ref))
                continue
            path = os.path.normpath(os.path.join(css_dir, ref.split("?")[0].split("#")[0]))
            if not os.path.isfile(path):
                errors.append("static/css/%s: url(%s) does not exist" % (name, ref))
    return errors


def context(text, pos):
    return text[max(0, pos - 30):pos + 40].replace("\n", " ")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def reject_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError("duplicate key %r" % key)
        seen[key] = value
    return seen


def load_json(path, errors):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=reject_duplicate_keys)
    except (OSError, ValueError) as e:
        errors.append("content/%s: %s" % (os.path.basename(path), e))
        return None


def load_templates(template_dir, errors):
    templates = {}
    if not os.path.isdir(template_dir):
        errors.append("templates/ folder not found at %s" % template_dir)
        return templates
    for name in sorted(os.listdir(template_dir)):
        if name.endswith(".html"):
            with open(os.path.join(template_dir, name), encoding="utf-8") as f:
                templates[name] = Template(f.read())
    return templates


def asset_version(static_dir):
    digest = hashlib.sha256()
    for folder, dirs, files in sorted(os.walk(static_dir)):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(f for f in files if not f.startswith(".")):
            path = os.path.join(folder, name)
            digest.update(os.path.relpath(path, static_dir).replace(os.sep, "/").encode())
            with open(path, "rb") as f:
                digest.update(f.read())
    return digest.hexdigest()[:10]


def held_back(content):
    """[(speaker id, speaker, [where referenced])] for everyone not confirmed or ex-officio."""
    refs = {}
    for day in content["days"]:
        for sid in day["dignitaries"]:
            refs.setdefault(sid, []).append("%s dignitaries" % day["label"])
        for s in day["sessions"]:
            label = "Session %d" % s["number"] if s["number"] is not None else s["id"]
            for sid in s["speakers"] + [s["moderator"], s["voteOfThanks"]]:
                if sid:
                    refs.setdefault(sid, []).append(label)
    return [(sid, sp, refs.get(sid, [])) for sid, sp in content["speakers"].items()
            if sp["status"] not in PUBLISHED_STATUSES]


COMPRESSIBLE = (".html", ".css", ".js", ".svg", ".xml", ".txt", ".json", ".webmanifest")  # same list as server.py


def precompress(folder):
    """Write <file>.gz next to every text file over 1 KB; server.py sends it to clients that accept gzip.
    Deterministic (mtime=0) so rebuilding the same content gives the same bytes."""
    for here, _, files in os.walk(folder):
        for name in files:
            path = os.path.join(here, name)
            if not name.endswith(COMPRESSIBLE) or os.path.getsize(path) < 1024:
                continue
            with open(path, "rb") as f:
                data = f.read()
            packed = gzip.compress(data, compresslevel=9, mtime=0)
            if len(packed) < len(data):
                with open(path + ".gz", "wb") as f:
                    f.write(packed)


def write_site(outputs, static_dir, target):
    """Render into <target>.tmp, then swap it in. A failure leaves <target> untouched."""
    tmp, old = target + ".tmp", target + ".old"
    for leftover in (tmp, old):
        if os.path.exists(leftover):
            shutil.rmtree(leftover)
    try:
        shutil.copytree(static_dir, os.path.join(tmp, "assets"), ignore=shutil.ignore_patterns(".*", "*.md"))
        for rel, text in outputs.items():
            path = os.path.join(tmp, *rel.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        precompress(tmp)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    if os.path.exists(target):
        os.rename(target, old)
    os.rename(tmp, target)
    shutil.rmtree(old, ignore_errors=True)


def build(root=ROOT, check_only=False, include_unconfirmed=False, out=print):
    content_dir = os.path.join(root, "content")
    static_dir = os.path.join(root, "static")
    errors = []
    en = load_json(os.path.join(content_dir, "content.en.json"), errors)
    hi_path = os.path.join(content_dir, "content.hi.json")
    hi = load_json(hi_path, errors) if os.path.exists(hi_path) else None
    if not os.path.isdir(static_dir):
        errors.append("static/ folder not found at %s" % static_dir)
    if en is not None and hi is not None:
        compare_structure(en, hi, "", errors)
    if en is not None:
        errors += validate(en, "en", static_dir)
    if hi is not None:
        errors += ["hi " + e for e in validate(hi, "hi", static_dir)]
    templates = load_templates(os.path.join(root, "templates"), errors)
    if os.path.isdir(static_dir):
        errors += check_css(static_dir)
    if errors:
        return fail(errors, out)

    version = asset_version(static_dir)
    try:
        en_renderer = Renderer(en, "en", templates, include_unconfirmed, version, hi is not None, static_dir)
        outputs = {"index.html": en_renderer.index(), "404.html": en_renderer.not_found()}
        if hi is not None:
            outputs["hi/index.html"] = Renderer(hi, "hi", templates, include_unconfirmed, version, True, static_dir).index()
    except (KeyError, ValueError) as e:
        return fail(["template problem: %s (a $variable in templates/ that the build does not fill?)" % e], out)
    today = datetime.date.today().isoformat()
    urls = [SITE_URL] + ([SITE_URL + "hi/"] if hi is not None else [])
    outputs["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n') % "".join(
        "  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n" % (u, today) for u in urls)
    outputs["robots.txt"] = ("User-agent: *\nDisallow: /\n" if include_unconfirmed else
                             "User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % SITE_URL)

    held = held_back(en)
    names = [] if include_unconfirmed else [core_name(sp["name"]) for _, sp, _ in held]
    allowed = [en["ui"]["sections"]["moments"]["soonTitle"]] if en["photos"]["status"] == "coming-soon" else []
    errors = scan_outputs(outputs, names, static_dir, allowed)
    if errors:
        return fail(errors, out)

    if held:
        out("Held back (not published; status is not confirmed or ex-officio):")
        for sid, sp, refs in held:
            out("  - %s [%s] %s" % (sp["name"], sp["status"], ("in " + ", ".join(refs)) if refs else "(not referenced)"))
    if include_unconfirmed:
        out("\n" + "!" * 72 + "\n!! PREVIEW BUILD: unconfirmed speakers ARE SHOWN. noindex + PREVIEW banner.\n"
            "!! Written to site-preview/, never site/. Do NOT publish this.\n" + "!" * 72)
    if check_only:
        out("Check passed: %d page(s) would be built. Nothing written (--check)." % len(outputs))
        return 0
    target = os.path.join(root, "site-preview" if include_unconfirmed else "site")
    write_site(outputs, static_dir, target)
    out("Built %d file(s) into %s/ (assets version %s)." % (len(outputs), os.path.basename(target), version))
    return 0


def fail(errors, out):
    out("BUILD FAILED: %d problem(s). Nothing was written; the live site/ is unchanged.\n" % len(errors))
    for e in errors:
        out("  - " + e)
    return 1


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")  # Devanagari on consoles that can't show it
    parser = argparse.ArgumentParser(description="Build the Samarasyam 2026 portal into site/.")
    parser.add_argument("--check", action="store_true", help="validate only; write nothing")
    parser.add_argument("--include-unconfirmed", action="store_true",
                        help="PREVIEW build with unconfirmed speakers, written to site-preview/ (never site/)")
    args = parser.parse_args(argv)
    return build(check_only=args.check, include_unconfirmed=args.include_unconfirmed)


if __name__ == "__main__":
    sys.exit(main())
