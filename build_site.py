#!/usr/bin/env python3
"""
Build the Samarasyam 2026 portal from content/content.en.json into site/.

    python3 build_site.py                        validate, then build site/
    python3 build_site.py --check                validate only; writes nothing
    python3 build_site.py --include-unconfirmed  PREVIEW build into site-preview/ (never site/)

The build stops, with a list of every problem, if the content breaks a rule:
the schema, the identity lock, the "Well-being" spelling, leftover placeholder
text, unknown speaker IDs, bad or overlapping times. A failed build never
touches the live site/ folder. Only speakers with status "confirmed" or
"ex-officio" are published; everyone else is held back and listed.

Standard library only; Python 3.8+.
"""
import argparse
import copy
import datetime
import hashlib
import html
import json
import os
import re
import shutil
import sys
from string import Template

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
SLUG = "national-wellbeing-conclave-2026"

IDENTITY = {
    "nameDevanagari": NAME_DEVANAGARI, "nameLatin": NAME_LATIN, "nameFull": NAME_FULL,
    "tagline": TAGLINE, "theme": THEME, "dates": DATES, "venue": VENUE,
    "hashtag": HASHTAG, "slug": SLUG,
}
# A Hindi file translates the theme, dates and venue, but these never change.
LANGUAGE_NEUTRAL_IDENTITY = ("nameDevanagari", "nameLatin", "tagline", "hashtag", "slug")

STATUSES = ("confirmed", "verbally-confirmed", "awaiting", "tbc", "ex-officio", "alternate")
PUBLISHED_STATUSES = ("confirmed", "ex-officio")
STATUS_WORDS = {  # shown next to names in PREVIEW builds only
    "confirmed": "confirmed", "ex-officio": "ex officio", "verbally-confirmed": "verbally confirmed",
    "awaiting": "awaiting confirmation", "tbc": "to be confirmed", "alternate": "alternate",
}
SESSION_TYPES = ("inaugural", "exhibition", "presentation", "panel", "symposium", "workshop",
                 "icebreaker", "breakaway", "students", "valedictory", "break", "cultural", "social")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
HONORIFICS = {"dr.", "prof.", "(dr.)", "shri", "sh", "sh.", "smt.", "ms.", "mr.", "mrs."}

PLACEHOLDER_PATTERNS = (
    (re.compile(r"\bTODO\b", re.I), "TODO"),
    (re.compile(r"\bTBC\b", re.I), "TBC"),
    (re.compile(r"lorem", re.I), "lorem"),
    (re.compile(r"00000"), "00000"),
    (re.compile(r"XXX", re.I), "XXX"),
    (re.compile(r"placeholder", re.I), "placeholder"),
    (re.compile(r"""\b(?:href|src)\s*=\s*(?:""|''|"#"|'#')"""), "an empty href/src"),
    (re.compile(r"<script(?![^>]*\bsrc=)", re.I), "an inline <script> (blocked by the CSP)"),
    (re.compile(r"<style", re.I), "an inline <style> (blocked by the CSP)"),
    (re.compile(r"""\sstyle\s*=""", re.I), "a style= attribute (blocked by the CSP)"),
    (re.compile(r"""\son[a-z]+\s*=""", re.I), "an inline event handler (blocked by the CSP)"),
    (re.compile(r"\$\{?[A-Za-z_]"), "an unfilled $template variable"),
)
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
    "status": Enum(*STATUSES), "photo": Opt(OPT_TEXT), "bio": Opt(OPT_TEXT),
}
SPEAKER_DEFAULTS = {"designation": None, "institution": None, "photo": None, "bio": None}
UI = {
    "skipLink": TEXT, "navLabel": TEXT, "heroEyebrow": OPT_TEXT, "viewProgramme": TEXT,
    "nav": {k: TEXT for k in ("about", "programme", "speakers", "journey", "moments", "feedback", "contact")},
    "headings": {k: TEXT for k in ("glance", "benefits", "programme", "speakers", "dignitaries",
                                   "speakerGrid", "moments", "feedback", "contact", "emergency")},
    "labels": {k: TEXT for k in (
        "dates", "venue", "countdown", "countdownDays", "countdownDay", "countdownLive", "countdownOver",
        "programmeTabs", "session", "moderator", "speakers", "voteOfThanks", "groups", "onwards",
        "email", "onBehalf", "photosComingSoon", "feedbackClosed", "feedbackOpen", "copyright")},
    "typeLabels": {k: TEXT for k in SESSION_TYPES},
    "months": [TEXT],
    "notFound": {"title": TEXT, "text": TEXT, "link": TEXT},
}
SCHEMA = {
    "event": {
        "nameDevanagari": TEXT, "nameLatin": TEXT, "nameFull": TEXT, "tagline": TEXT, "theme": TEXT,
        "dates": TEXT, "startDate": TEXT, "venue": TEXT, "slug": TEXT, "hashtag": TEXT,
        "programmeNote": OPT_TEXT, "organisers": OPT_TEXT,
    },
    "ui": UI,
    "logos": [{"src": TEXT, "alt": TEXT}],
    "about": {"heading": OPT_TEXT, "body": [TEXT], "quote": {"text": OPT_TEXT, "credit": OPT_TEXT}},
    "benefits": [{"audience": TEXT, "text": TEXT}],
    "days": [{"id": TEXT, "label": TEXT, "date": TEXT, "weekday": TEXT, "theme": OPT_TEXT, "sessions": [SESSION]}],
    "speakers": MapOf(SPEAKER),
    "dignitaries": [TEXT],
    "journey": {
        "heading": OPT_TEXT, "intro": OPT_TEXT,
        "milestones": [{"year": OPT_TEXT, "place": TEXT, "text": OPT_TEXT,
                        "stats": [{"value": TEXT, "label": TEXT}]}],
    },
    "photos": {"status": Enum("coming-soon", "live"), "items": [{"src": TEXT, "alt": TEXT, "caption": OPT_TEXT}]},
    "feedback": {"status": Enum("closed", "open"), "formUrl": OPT_TEXT},
    "contact": {"team": TEXT, "lines": [TEXT], "email": TEXT,
                "people": [{"name": TEXT, "role": OPT_TEXT, "phone": OPT_TEXT}]},
    "emergency": [{"service": TEXT, "number": TEXT, "note": OPT_TEXT}],
    "footer": {"credit": OPT_TEXT, "socials": [{"label": TEXT, "url": TEXT}]},
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

    ev = content["event"]
    locked = IDENTITY if lang == "en" else {k: IDENTITY[k] for k in LANGUAGE_NEUTRAL_IDENTITY}
    for key, expected in locked.items():
        if ev[key] != expected:
            errors.append("event.%s: must be exactly %r (identity lock in build_site.py), found %r"
                          % (key, expected, ev[key]))
    for where, value in walk_strings(content, ""):
        if NAME_APOSTROPHE.search(value):
            errors.append("%s: no apostrophe after समरस्यम् (write समरस्यम् 2026)" % where)
    if len(content["ui"]["months"]) != 12:
        errors.append("ui.months: must list 12 month names")

    speakers = content["speakers"]
    for sid, sp in speakers.items():
        if not ID_RE.match(sid):
            errors.append("speakers.%s: IDs use lowercase letters, digits and hyphens only" % sid)
        if not sp["name"].strip():
            errors.append("speakers.%s.name: must not be empty" % sid)
        if sp["photo"]:
            check_asset_path(sp["photo"], "speakers.%s.photo" % sid, static_dir, errors)

    def check_ref(sid, where):
        if sid not in speakers:
            errors.append("%s: unknown speaker ID %r (not in \"speakers\")" % (where, sid))

    for i, sid in enumerate(content["dignitaries"]):
        check_ref(sid, "dignitaries[%d]" % i)
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
    url = content["feedback"]["formUrl"]
    if content["feedback"]["status"] == "open":
        if not url or not (url.startswith("https://docs.google.com/forms/") or url.startswith("https://forms.gle/")):
            errors.append("feedback.formUrl: when open, must be a Google Form link (https://docs.google.com/forms/...)")
    if not EMAIL_RE.match(content["contact"]["email"]):
        errors.append("contact.email: %r is not an email address" % content["contact"]["email"])
    phones = [("contact.people[%d].phone" % i, p["phone"]) for i, p in enumerate(content["contact"]["people"])]
    phones += [("emergency[%d].number" % i, e["number"]) for i, e in enumerate(content["emergency"])]
    for where, number in phones:
        if number and len(re.sub(r"\D", "", number)) < 5:
            errors.append("%s: %r does not look like a phone number" % (where, number))
    for i, social in enumerate(content["footer"]["socials"]):
        if not social["url"].startswith("https://"):
            errors.append("footer.socials[%d].url: must start with https://" % i)
    return errors


INVARIANT_KEYS = {"id", "number", "start", "end", "type", "parallel", "moderator", "speakers", "voteOfThanks",
                  "status", "photo", "src", "date", "startDate", "slug", "hashtag", "formUrl", "email", "phone"}


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
# Rendering
# ---------------------------------------------------------------------------
def esc(value):
    return html.escape(value or "", quote=True)


def tel_href(number):
    return "tel:" + re.sub(r"[^\d+]", "", number)


def core_name(name):
    """'Dr. Ram Manohar Singh' -> 'Ram Manohar Singh'; 'Ms. Geeta Mehrotra and Team' -> 'Geeta Mehrotra'."""
    words = name.split(" and ")[0].replace(",", " ").split()
    return " ".join(w for w in words if w.lower() not in HONORIFICS)


def initials(name):
    words = [w for w in core_name(name).split() if w[:1].isalpha()]
    if not words:
        return ""
    return (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper()


class Renderer:
    def __init__(self, content, lang, templates, include_unconfirmed, asset_version, has_hindi):
        self.c = content
        self.ui = content["ui"]
        self.lang = lang
        self.t = templates
        self.preview = include_unconfirmed
        self.asset_version = asset_version
        self.has_hindi = has_hindi
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

    def date_text(self, iso, weekday=None):
        d = datetime.date.fromisoformat(iso)
        text = "%d %s %d" % (d.day, self.ui["months"][d.month - 1], d.year)
        return "%s, %s" % (weekday, text) if weekday else text

    def time_html(self, date, s):
        start = '<time datetime="%sT%s%s">%%s</time>' % (date, s["start"], TIMEZONE)
        if s["timeLabel"]:
            inner = start % esc(s["timeLabel"])
        elif s["end"]:
            end = '<time datetime="%sT%s%s">%s</time>' % (date, s["end"], TIMEZONE, s["end"].replace(":", "."))
            inner = start % s["start"].replace(":", ".") + " – " + end
        else:
            inner = start % s["start"].replace(":", ".") + " " + esc(self.ui["labels"]["onwards"])
        return '<span class="session__time">%s</span>' % inner

    def publishable(self, sid):
        return is_publishable(self.c["speakers"][sid], self.preview)

    def person(self, sid, with_bio=False):
        sp = self.c["speakers"][sid]
        if sp["photo"]:
            media = '<img class="person__photo" src="%sassets/%s" alt="" loading="lazy" decoding="async">' % (
                self.root, esc(sp["photo"]))
        else:
            media = self.el("span", esc(initials(sp["name"])), "person__initials", ' aria-hidden="true"')
        parts = [self.el("span", self.text(sp["designation"]), "person__designation"),
                 self.el("span", self.text(sp["institution"]), "person__institution")]
        role = self.el("span", ", ".join(p for p in parts if p), "person__role")
        status = ""
        if sp["status"] not in PUBLISHED_STATUSES:  # only reachable in PREVIEW builds
            status = self.el("span", "(%s)" % STATUS_WORDS[sp["status"]], "person__status")
        bio = self.el("p", self.text(sp["bio"]), "person__bio") if with_bio else ""
        return self.fill("_person.html", media=media, name=self.text(sp["name"]), role=role,
                         status=status, bio=bio)

    def people_list(self, ids, cls="people", with_bio=False):
        items = [self.person(sid, with_bio) for sid in ids if self.publishable(sid)]
        return self.el("ul", "\n".join(items), cls)

    # -- sections --
    def header(self, nav):
        logos = "\n".join('<img class="site-header__logo" src="%sassets/%s" alt="%s">' % (
            self.root, esc(logo["src"]), esc(logo["alt"])) for logo in self.c["logos"])
        nav_items = "\n".join('      <li><a href="#%s">%s</a></li>' % (sid, self.text(label)) for sid, label in nav)
        toggle = ""
        if self.has_hindi:
            if self.lang == "hi":
                toggle = '<a href="../" hreflang="en" lang="en">EN</a> | <span aria-current="page">हिन्दी</span>'
            else:
                toggle = '<span aria-current="page">EN</span> | <a href="hi/" hreflang="hi" lang="hi">हिन्दी</a>'
        return self.fill("_header.html", logos=logos, brand=self.text(self.c["event"]["nameLatin"]),
                         nav_label=esc(self.ui["navLabel"]), nav_items=nav_items, lang_toggle=toggle)

    def hero(self):
        ev = self.c["event"]
        return self.fill(
            "_hero.html", eyebrow=self.el("p", self.text(self.ui["heroEyebrow"]), "hero__eyebrow"),
            name_devanagari=self.devanagari(ev["nameDevanagari"]), name_latin=self.text(ev["nameLatin"]),
            name_full=self.text(ev["nameFull"]), tagline=self.devanagari(ev["tagline"]),
            theme=self.text(ev["theme"]), start_date=esc(ev["startDate"]), dates=self.text(ev["dates"]),
            venue=self.text(ev["venue"]), view_programme=self.text(self.ui["viewProgramme"]))

    def glance(self):
        ev, labels, days = self.c["event"], self.ui["labels"], self.c["days"]
        first = days[0]["sessions"][0]["start"] if days[0]["sessions"] else "00:00"
        last_day = days[-1]
        last = last_day["sessions"][-1] if last_day["sessions"] else None
        end_time = (last["end"] or last["start"]) if last else "23:59"
        return self.fill(
            "_glance.html", heading=self.text(self.ui["headings"]["glance"]),
            dates_label=self.text(labels["dates"]), venue_label=self.text(labels["venue"]),
            countdown_label=self.text(labels["countdown"]), start_date=esc(ev["startDate"]),
            dates=self.text(ev["dates"]), venue=self.text(ev["venue"]),
            start_datetime="%sT%s%s" % (esc(days[0]["date"]), first, TIMEZONE),
            end_datetime="%sT%s%s" % (esc(last_day["date"]), end_time, TIMEZONE),
            label_days=esc(labels["countdownDays"]), label_day=esc(labels["countdownDay"]),
            label_live=esc(labels["countdownLive"]), label_over=esc(labels["countdownOver"]),
            start_text=self.text(self.date_text(days[0]["date"], days[0]["weekday"])))

    def about(self):
        a = self.c["about"]
        if not a["heading"]:
            return ""
        body = "\n".join(self.el("p", self.text(p)) for p in a["body"] if p)
        quote = ""
        if a["quote"]["text"]:
            quote = '<figure class="about__quote">\n<blockquote><p>%s</p></blockquote>\n%s\n</figure>' % (
                self.text(a["quote"]["text"]), self.el("figcaption", self.text(a["quote"]["credit"])))
        return self.fill("_about.html", heading=self.text(a["heading"]), body=body, quote=quote)

    def benefits(self):
        items = "\n".join(
            '    <li class="benefit">%s%s</li>' % (self.el("h3", self.text(b["audience"]), "benefit__audience"),
                                                   self.el("p", self.text(b["text"]), "benefit__text"))
            for b in self.c["benefits"])
        if not items:
            return ""
        return self.fill("_benefits.html", heading=self.text(self.ui["headings"]["benefits"]), items=items)

    def session(self, day, s):
        labels = self.ui["labels"]
        time_html = self.time_html(day["date"], s)
        tag = self.el("span", self.text(self.ui["typeLabels"][s["type"]]), "session__tag")
        title = self.text(s["title"])
        subtitle = self.el("span", self.text(s["subtitle"]), "session__subtitle")
        if s["type"] == "break":
            return self.fill("_session_plain.html", variant="break", id=esc(s["id"]), type=esc(s["type"]),
                             time=time_html, tag="", title=title, subtitle=subtitle)
        people = []
        for heading, ids in (((s["moderatorRole"] or labels["moderator"]), [s["moderator"]] if s["moderator"] else []),
                             (labels["speakers"], s["speakers"]),
                             (labels["voteOfThanks"], [s["voteOfThanks"]] if s["voteOfThanks"] else [])):
            block = self.people_list(ids)
            if block:
                people.append(self.el("h4", self.text(heading), "session__people-heading") + "\n" + block)
        groups = ""
        if s["groups"]:
            groups = self.el("h4", self.text(labels["groups"]), "session__people-heading") + "\n" + self.el(
                "ul", "".join(self.el("li", self.text(g)) for g in s["groups"]), "session__groups")
        body = {
            "brief": self.el("p", self.text(s["brief"]), "session__brief"),
            "outcomes": self.el("ul", "".join(self.el("li", self.text(o)) for o in s["outcomes"] if o),
                                "session__outcomes"),
            "venue": self.el("p", self.text(s["venue"]), "session__venue"),
            "groups": groups,
            "people": "\n".join(people),
        }
        number = ""
        if s["number"] is not None:
            number = self.el("span", "%s %d" % (self.text(labels["session"]), s["number"]), "session__number")
        if not any(body.values()):  # e.g. Cultural Programme: nothing to expand
            return self.fill("_session_plain.html", variant="plain", id=esc(s["id"]), type=esc(s["type"]),
                             time=time_html, tag=tag, title=title, subtitle=subtitle)
        return self.fill("_session.html", id=esc(s["id"]), type=esc(s["type"]), time=time_html, tag=tag,
                         number=number, title=title, subtitle=subtitle, **body)

    def programme(self):
        tabs, panels = [], []
        for i, day in enumerate(self.c["days"]):
            day_id = esc(day["id"])
            date_text = self.text(self.date_text(day["date"], day["weekday"]))
            tabs.append('    <a class="programme__tab" role="tab" id="tab-%s" href="#%s" aria-controls="%s" '
                        'aria-selected="%s">%s <span class="programme__tab-date">%s</span></a>' % (
                            day_id, day_id, day_id, "true" if i == 0 else "false", self.text(day["label"]), date_text))
            sessions = "\n".join(self.session(day, s) for s in day["sessions"])
            panels.append(self.fill("_day.html", id=day_id, date=esc(day["date"]), label=self.text(day["label"]),
                                    date_text=date_text, theme=self.el("p", self.text(day["theme"]), "programme__day-theme"),
                                    sessions=sessions))
        return self.fill("_programme.html", heading=self.text(self.ui["headings"]["programme"]),
                         note=self.el("p", self.text(self.c["event"]["programmeNote"]), "programme__note"),
                         tabs_label=esc(self.ui["labels"]["programmeTabs"]), tabs="\n".join(tabs),
                         panels="\n".join(panels))

    def speakers(self):
        dignitaries = [sid for sid in self.c["dignitaries"] if self.publishable(sid)]
        grid, seen = [], set(self.c["dignitaries"])
        for day in self.c["days"]:
            for s in day["sessions"]:
                for sid in ([s["moderator"]] if s["moderator"] else []) + s["speakers"]:
                    if sid not in seen and self.publishable(sid):
                        grid.append(sid)
                    seen.add(sid)
        if not dignitaries and not grid:
            return ""
        h = self.ui["headings"]
        dig_html = ""
        if dignitaries:
            dig_html = self.el("h3", self.text(h["dignitaries"])) + "\n" + self.people_list(
                dignitaries, "people people--dignitaries", with_bio=True)
        grid_html = ""
        if grid:
            grid_html = self.el("h3", self.text(h["speakerGrid"])) + "\n" + self.people_list(
                grid, "people people--grid", with_bio=True)
        return self.fill("_speakers.html", heading=self.text(h["speakers"]), dignitaries=dig_html, grid=grid_html)

    def journey(self):
        j = self.c["journey"]
        if not j["milestones"] or not j["heading"]:
            return ""
        items = []
        for m in j["milestones"]:
            stats = self.el("ul", "".join(
                '<li><strong class="stat__value">%s</strong> <span class="stat__label">%s</span></li>' % (
                    self.text(st["value"]), self.text(st["label"])) for st in m["stats"]), "milestone__stats")
            items.append('    <li class="milestone">%s%s%s%s</li>' % (
                self.el("p", self.text(m["year"]), "milestone__year"),
                self.el("h3", self.text(m["place"]), "milestone__place"),
                self.el("p", self.text(m["text"]), "milestone__text"), stats))
        return self.fill("_journey.html", heading=self.text(j["heading"]),
                         intro=self.el("p", self.text(j["intro"]), "journey__intro"), milestones="\n".join(items))

    def moments(self):
        photos = self.c["photos"]
        if photos["status"] == "live":
            body = self.el("ul", "\n".join(
                '<li><figure><img src="%sassets/%s" alt="%s" loading="lazy" decoding="async">%s</figure></li>' % (
                    self.root, esc(p["src"]), esc(p["alt"]), self.el("figcaption", self.text(p["caption"])))
                for p in photos["items"]), "moments__list")
        else:
            body = self.el("p", self.text(self.ui["labels"]["photosComingSoon"]), "moments__soon")
        return self.fill("_moments.html", heading=self.text(self.ui["headings"]["moments"]), body=body)

    def feedback(self):
        fb, labels = self.c["feedback"], self.ui["labels"]
        if fb["status"] == "open":
            body = '<p class="feedback__open"><a href="%s" rel="noopener">%s</a></p>' % (
                esc(fb["formUrl"]), self.text(labels["feedbackOpen"]))
        else:
            body = self.el("p", self.text(labels["feedbackClosed"]), "feedback__closed")
        return self.fill("_feedback.html", heading=self.text(self.ui["headings"]["feedback"]), body=body)

    def contact(self):
        ct, labels = self.c["contact"], self.ui["labels"]
        lines = "".join("<br>" + self.text(line) for line in ct["lines"] if line)
        people = ""
        rows = []
        for p in ct["people"]:
            parts = [self.el("span", self.text(p["name"]), "contact__name"),
                     self.el("span", self.text(p["role"]), "contact__role")]
            if p["phone"]:
                parts.append('<a href="%s">%s</a>' % (esc(tel_href(p["phone"])), self.text(p["phone"])))
            rows.append("      <li>%s</li>" % ", ".join(x for x in parts if x))
        if rows:
            people = "    %s\n    <ul class=\"contact__people\">\n%s\n    </ul>" % (
                self.el("p", self.text(labels["onBehalf"]), "contact__on-behalf"), "\n".join(rows))
        return self.fill("_contact.html", heading=self.text(self.ui["headings"]["contact"]),
                         team=self.text(ct["team"]), lines=lines, email_label=self.text(labels["email"]),
                         email_href=esc("mailto:" + ct["email"]), email=self.text(ct["email"]), people=people)

    def footer(self):
        ev, labels = self.c["event"], self.ui["labels"]
        emergency = ""
        if self.c["emergency"]:
            rows = "\n".join('      <li><span class="emergency__service">%s</span> <a href="%s">%s</a>%s</li>' % (
                self.text(e["service"]), esc(tel_href(e["number"])), self.text(e["number"]),
                (" " + self.el("span", "(%s)" % self.text(e["note"]), "emergency__note")) if e["note"] else "")
                for e in self.c["emergency"])
            emergency = ('  <div class="site-footer__emergency">\n    <h2 id="emergency-title">%s</h2>\n'
                         '    <ul>\n%s\n    </ul>\n  </div>') % (self.text(self.ui["headings"]["emergency"]), rows)
        socials = self.el("ul", "".join('<li><a href="%s" rel="noopener">%s</a></li>' % (
            esc(s["url"]), self.text(s["label"])) for s in self.c["footer"]["socials"]), "site-footer__socials")
        identity = "%s · %s · %s" % (self.text(ev["nameLatin"]), self.devanagari(ev["nameDevanagari"]),
                                     self.text(ev["nameFull"]))
        return self.fill("_footer.html", identity=identity,
                         organisers=self.el("p", self.text(ev["organisers"]), "site-footer__organisers"),
                         emergency=emergency, venue=self.text(ev["venue"]), socials=socials,
                         hashtag=self.text(ev["hashtag"]), copyright=self.text(labels["copyright"]),
                         credit=self.el("p", self.text(self.c["footer"]["credit"]), "site-footer__credit"))

    def head_values(self):
        ev = self.c["event"]
        alternates = ""
        if self.has_hindi:
            alternates = ('<link rel="alternate" hreflang="en" href="%s">\n<link rel="alternate" hreflang="hi" '
                          'href="%shi/">' % (SITE_URL, SITE_URL))
        return {
            "lang": self.lang, "root": self.root, "asset_version": self.asset_version,
            "title": esc("%s · %s · IIT Ropar" % (ev["nameLatin"], ev["nameFull"])),
            "description": esc("%s. %s, %s." % (ev["theme"], ev["dates"], ev["venue"])),
            "canonical": esc(self.canonical), "alternates": alternates,
            "og_locale": "hi_IN" if self.lang == "hi" else "en_IN",
            "robots_meta": '<meta name="robots" content="noindex, nofollow">' if self.preview else "",
        }

    def index(self):
        sections = [("about", self.about()), ("benefits", self.benefits()), ("programme", self.programme()),
                    ("speakers", self.speakers()), ("journey", self.journey()), ("moments", self.moments()),
                    ("feedback", self.feedback()), ("contact", self.contact())]
        nav = [(sid, self.ui["nav"][sid]) for sid, markup in sections if markup and sid in self.ui["nav"]]
        banner = ""
        if self.preview:
            banner = ('<p class="preview-banner" role="note"><strong>PREVIEW</strong>: this build includes '
                      'speakers who are not yet confirmed. Do not share or publish it.</p>')
        values = dict(self.head_values(), skip_link=self.text(self.ui["skipLink"]), preview_banner=banner,
                      header=self.header(nav), hero=self.hero(), glance=self.glance(), footer=self.footer(),
                      **dict(sections))
        return self.fill("base.html", **values)

    def not_found(self):
        nf = self.ui["notFound"]
        return self.fill("404.html", **dict(self.head_values(), title=esc("%s · %s" % (nf["title"], self.c["event"]["nameLatin"])),
                                             heading=self.text(nf["title"]), text=self.text(nf["text"]),
                                             link=self.text(nf["link"])))


# ---------------------------------------------------------------------------
# Output checks
# ---------------------------------------------------------------------------
def scan_outputs(outputs, held_back_names):
    errors = []
    for name, text in sorted(outputs.items()):
        body = ASSET_VERSION.sub("", text)
        for pattern, label in PLACEHOLDER_PATTERNS:
            for m in pattern.finditer(body):
                errors.append("site/%s: contains %s: ...%s..." % (name, label, context(body, m.start())))
        text = html.unescape(TAG.sub("", body))  # what a reader sees
        for source in (body, text):
            visible = source
            for allowed in WELLBEING_ALLOWED:
                visible = visible.replace(allowed, "")
            for m in WELLBEING.finditer(visible):
                errors.append("site/%s: spell it \"well-being\" (with the hyphen): ...%s..." % (name, context(visible, m.start())))
            for m in NAME_APOSTROPHE.finditer(source):
                errors.append("site/%s: no apostrophe after समरस्यम्: ...%s..." % (name, context(source, m.start())))
        for person in held_back_names:
            if person and (person in text or person in html.unescape(body)):
                errors.append("site/%s: mentions %r, who is held back (not confirmed)" % (name, person))
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
    for sid in content["dignitaries"]:
        refs.setdefault(sid, []).append("dignitaries")
    for day in content["days"]:
        for s in day["sessions"]:
            label = "Session %d" % s["number"] if s["number"] is not None else s["id"]
            for sid in s["speakers"] + [s["moderator"], s["voteOfThanks"]]:
                if sid:
                    refs.setdefault(sid, []).append(label)
    return [(sid, sp, refs.get(sid, [])) for sid, sp in content["speakers"].items()
            if sp["status"] not in PUBLISHED_STATUSES]


def write_site(outputs, static_dir, target):
    """Render into <target>.tmp, then swap it in. A failure leaves <target> untouched."""
    tmp, old = target + ".tmp", target + ".old"
    for leftover in (tmp, old):
        if os.path.exists(leftover):
            shutil.rmtree(leftover)
    try:
        shutil.copytree(static_dir, os.path.join(tmp, "assets"), ignore=shutil.ignore_patterns(".*"))
        for rel, text in outputs.items():
            path = os.path.join(tmp, *rel.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
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
    if errors:
        return fail(errors, out)

    version = asset_version(static_dir)
    try:
        en_renderer = Renderer(en, "en", templates, include_unconfirmed, version, hi is not None)
        outputs = {"index.html": en_renderer.index(), "404.html": en_renderer.not_found()}
        if hi is not None:
            outputs["hi/index.html"] = Renderer(hi, "hi", templates, include_unconfirmed, version, True).index()
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
    errors = scan_outputs(outputs, names)
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
