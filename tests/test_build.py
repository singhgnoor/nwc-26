"""build_site.py: validators, publish rule, output scan, atomic build, Hindi support."""
import copy
import json
import os
import re
import shutil
import struct
import tempfile
import unittest
import zlib
from html.parser import HTMLParser

from tests.helpers import REPO

import build_site  # noqa: E402  (tests.helpers puts the repo on sys.path)

with open(os.path.join(REPO, "content", "content.en.json"), encoding="utf-8") as f:
    REAL_CONTENT = json.load(f)


def sessions(content):
    return {s["id"]: s for day in content["days"] for s in day["sessions"]}


def tiny_png(width=4, height=3):
    """A valid PNG of the given size (standard library only)."""
    raw = b"".join(b"\x00" + b"\xcc\xbb\xaa" * width for _ in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class BuildTestCase(unittest.TestCase):
    """Each test gets a scratch copy of templates/ and static/ plus its own content file."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="nwc-build-")
        shutil.copytree(os.path.join(REPO, "templates"), os.path.join(self.root, "templates"))
        shutil.copytree(os.path.join(REPO, "static"), os.path.join(self.root, "static"))
        os.makedirs(os.path.join(self.root, "content"))
        self.content = copy.deepcopy(REAL_CONTENT)
        self.output = []

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def save(self, content=None, name="content.en.json"):
        with open(os.path.join(self.root, "content", name), "w", encoding="utf-8") as f:
            json.dump(self.content if content is None else content, f, ensure_ascii=False, indent=2)

    def run_build(self, **kw):
        self.save()
        self.output = []
        return build_site.build(root=self.root, out=self.output.append, **kw)

    def add_static(self, rel, data):
        path = os.path.join(self.root, "static", *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    @property
    def log(self):
        return "\n".join(self.output)

    def page(self, rel="index.html", folder="site"):
        with open(os.path.join(self.root, folder, *rel.split("/")), encoding="utf-8") as f:
            return f.read()

    def assertFails(self, *fragments, **kw):
        code = self.run_build(**kw)
        self.assertEqual(code, 1, self.log)
        for fragment in fragments:
            self.assertIn(fragment, self.log)
        self.assertFalse(os.path.exists(os.path.join(self.root, "site")), "a failed build must not write site/")


class TestRealContent(BuildTestCase):
    def test_builds_and_holds_back_only_rizwi(self):
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        self.assertNotIn("Rizwi", html)
        self.assertIn("Sh Syed Ekram Rizwi [tbc] (not referenced)", self.log)
        held = [line for line in self.output if line.startswith("  - ")]
        self.assertEqual(len(held), 1, self.log)  # nobody else is held back
        for shown in ("Shri Pralhad Joshi", "Ms. Deepti Gaur Mukerjee", "Dr. Tony Thomas", "Dr. Ananya Syal",
                      "Prof. Rajeev Ahuja", "Dr. Jitendra Nagpal", "Speaker and Moderator",
                      "Ms. Geeta Mehrotra and Team", "Shri Devendra Kumar Sharma", "Dr. Palak Upadhyay",
                      "Dr. Nancy Sahni"):
            self.assertIn(shown, html)
        self.assertNotIn("noindex", html)
        self.assertNotIn("PREVIEW", html)
        for rel in ("404.html", "robots.txt", "sitemap.xml", "assets/css/main.css", "assets/js/main.js",
                    "assets/img/og-image.png", "assets/img/favicon.svg", "assets/fonts/OFL-eczar.txt"):
            self.assertTrue(os.path.isfile(os.path.join(self.root, "site", *rel.split("/"))), rel)
        self.assertFalse(os.path.exists(os.path.join(self.root, "site", "assets", "img", "logos", "SOURCES.md")))

    def test_v6_designations_word_for_word(self):
        self.run_build()
        html = self.page()
        for text in ("Chairperson, Student Affairs, Indian Institute of Management Amritsar",
                     "Professor, Centre for Health and Mental Health, Tata Institute of Social Sciences, Mumbai",
                     "Professor, Department of Neurology, PGIMER, Chandigarh", "TISS, Mumbai",
                     "PGIMER, Chandigarh (Speaker on Nutrition)",
                     "Assistant Professor, Department of Humanities and Social Sciences, IIT Roorkee"):
            self.assertIn(text, html)
        for short in ("IIM Amritsar", "TISS Mumbai", "Dept. of Neurology", "PGIMER Chandigarh<"):
            self.assertNotIn(short, html)

    def test_identity_and_markup(self):
        self.run_build()
        html = self.page()
        self.assertIn('<html lang="en">', html)
        self.assertIn("<title>Samarasyam 2026 · 3rd National Well-being Conclave · IIT Ropar</title>", html)
        self.assertIn('<span lang="hi">समरस्यम्</span>', html)
        self.assertIn('<span lang="hi">स्वस्थ मन | समरस समाज | सशक्त राष्ट्र</span>', html)
        self.assertIn('<meta property="og:url" content="https://iitrpr.ac.in/national-wellbeing-conclave-2026/">', html)
        self.assertIn('<meta property="og:image" content="https://iitrpr.ac.in/national-wellbeing-conclave-2026/assets/img/og-image.png">', html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
        self.assertIn('role="tablist"', html)
        self.assertIn('<details class="session" id="details-s5" data-type="panel">', html)
        self.assertIn('class="tl tl--break" id="session-d1-lunch"', html)
        self.assertIn("19.00</time> <span class=\"rail__onwards\">onwards", html)
        self.assertIn(">06.30 / 07.00</time>", html)
        self.assertIn(">Coming soon<", html)
        self.assertIn("Opens on 7 December, after the valedictory session", html)
        self.assertIn('href="tel:18008914416"', html)
        self.assertIn('href="tel:+911881232505"', html)  # Conclave Helpdesk
        self.assertIn('href="mailto:nwc@iitrpr.ac.in"', html)
        self.assertIn('#<span lang="hi">समरस्यम्</span>2026', html)
        self.assertIn("#NationalWellbeingConclave", html)
        self.assertIn("Designed and developed by <strong>SAC Team</strong>", html)
        # relative paths only; external links are the socials, maps and iitrpr.ac.in, all in new tabs
        self.assertNotIn('href="/', html)
        self.assertNotIn('src="/', html)
        self.assertNotRegex(html, r'src="https?://')
        for m in re.finditer(r'<a[^>]+href="https?://[^"]+"[^>]*>', html):
            self.assertIn('target="_blank"', m.group(0))
            self.assertIn('rel="noopener noreferrer"', m.group(0))
        # the brief's Devanagari word is marked as Hindi; no apostrophe after the name
        self.assertIn('formally open <span lang="hi">समरस्यम्</span> 2026', html)
        self.assertNotIn("समरस्यम्'", html)

    def test_session_cards_follow_the_design(self):
        self.run_build()
        html = self.page()
        self.assertIn("Panel Discussion I: Transforming social connectedness", html)  # title: subtitle
        self.assertIn('class="session__number">Session 1<', html)
        self.assertNotIn("session__venue", html)  # V6 has no venues
        self.assertNotIn("Stakeholder groups", html)  # Session 10 card shows the brief only, as in Figma
        s4 = html[html.index('id="details-s4"'):html.index("</details>", html.index('id="details-s4"'))]
        self.assertNotIn("chip", s4)  # Session 4: no presenter until the Dean's office names one
        self.assertIn('class="session session--plain" data-type="cultural"', html)

    def test_speakers_follow_the_selected_day(self):
        self.run_build()
        html = self.page()
        day1 = html[html.index('id="speakers-day1"'):html.index('id="speakers-day2"')]
        day2 = html[html.index('id="speakers-day2"'):html.index("</section>", html.index('id="speakers-day2"'))]
        self.assertEqual(day1.count('class="speaker"'), 16)
        self.assertEqual(day2.count('class="speaker"'), 4)
        self.assertIn("Inaugural Ceremony", day1)
        self.assertIn("Valedictory Session", day2)
        self.assertNotIn("Dean, Student Affairs", day1)  # role-only entry is not a grid card
        self.assertNotIn("Dr. Jitendra Nagpal</p><p class=\"speaker", day2)  # Day 2 dignitary, not repeated
        self.assertIn('data-day="day1"', html)

    def test_nearby_band_and_map_links(self):
        self.run_build()
        html = self.page()
        self.assertIn('id="nearby"', html)
        links = re.findall(r'<a class="place__map" href="([^"]+)"[^>]*aria-label="([^"]+)"', html)
        self.assertEqual(len(links), 8)
        self.assertIn(("https://www.google.com/maps/search/?api=1&amp;query=Ropar%20Wetland",
                       "Open in Google Maps: Ropar Wetland (opens in a new tab)"), links)
        self.assertIn("ancestral home", html)
        self.assertNotIn("birthplace", html.lower())
        self.assertIn('<a href="#nearby">Around IIT Ropar</a>', html)

    def test_socials_in_figma_order(self):
        self.run_build()
        html = self.page()
        urls = re.findall(r'<a class="social" href="([^"]+)"[^>]*aria-label="IIT Ropar on (\w+)', html)
        self.assertEqual([u for _, u in urls], ["Facebook", "LinkedIn", "X", "Instagram", "YouTube"])
        self.assertEqual(urls[0][0], "https://www.facebook.com/iitrpr/")
        self.assertEqual(urls[4][0], "https://www.youtube.com/@IITRoparOfficialChannel")

    def test_briefs_only_no_outcomes(self):
        self.run_build()
        self.assertNotIn("session__outcomes", self.page())

    def test_check_writes_nothing(self):
        self.assertEqual(self.run_build(check_only=True), 0, self.log)
        self.assertFalse(os.path.exists(os.path.join(self.root, "site")))

    def test_html_is_well_formed_with_unique_ids_and_valid_references(self):
        self.assertEqual(self.run_build(), 0, self.log)
        for rel in ("index.html", "404.html"):
            checker = TagChecker()
            checker.feed(self.page(rel))
            self.assertEqual(checker.errors, [], rel)
            self.assertEqual(checker.stack, [], rel + ": unclosed tags")
            duplicates = {i for i in checker.ids if checker.ids.count(i) > 1}
            self.assertEqual(duplicates, set(), rel)
        html = self.page()
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        refs = re.findall(r'(?:aria-labelledby|aria-controls)="([^"]+)"', html)
        refs += [h[1:] for h in re.findall(r'href="(#[^"]+)"', html)]
        refs += re.findall(r'<use href="#([^"]+)"', html)
        self.assertEqual(sorted(set(r for r in refs if r not in ids)), [])
        self.assertEqual(html.count("<h1"), 1)
        # every section from the spec is present, in order
        order = [html.index('id="%s"' % s) for s in ("hero", "glance", "about", "programme", "speakers",
                                                      "journey", "moments", "feedback", "contact", "nearby")]
        self.assertEqual(order, sorted(order))
        self.assertLess(html.index("<header"), order[0])
        self.assertGreater(html.index("<footer"), order[-1])
        # every image has an alt attribute and width/height
        for img in re.findall(r"<img [^>]+>", html):
            self.assertIn(" alt=", img)
            self.assertIn(" width=", img)


class TagChecker(HTMLParser):
    VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "wbr", "use"}

    def __init__(self):
        super().__init__()
        self.stack, self.ids, self.errors = [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append("unexpected </%s> at %s" % (tag, self.getpos()))
        else:
            self.stack.pop()


class TestValidators(BuildTestCase):
    def test_placeholder_text_fails(self):
        for token in ("TODO", "TBC", "lorem ipsum", "+91 00000 00000", "XXX", "placeholder", "Speaker Name",
                      "Designation, Institution", "Name of the Chief Guest", "sample programme"):
            with self.subTest(token=token):
                content = copy.deepcopy(REAL_CONTENT)
                sessions(content)["s2"]["brief"] = "Brief with %s inside." % token
                self.content = content
                self.assertFails("BUILD FAILED")

    def test_coming_soon_only_in_the_designed_state(self):
        sessions(self.content)["s2"]["brief"] = "Details coming soon."
        self.assertFails("coming soon")
        self.content = copy.deepcopy(REAL_CONTENT)
        self.assertEqual(self.run_build(), 0, self.log)  # the Moments card itself passes

    def test_institution_words_in_real_text_pass(self):
        # "Institutions" and "University/Institution Wellness Indicators" are real content, not placeholders
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertIn("University/Institution Wellness Indicators Checklist", self.page())

    def test_misspellings_fail(self):
        for wrong, where in (("Shri Prahlad Joshi", "name"), ("Ms. Deepti Gaur Mukherjee", "name")):
            with self.subTest(wrong=wrong):
                self.content = copy.deepcopy(REAL_CONTENT)
                key = "pralhad-joshi" if "Prahlad" in wrong else "deepti-gaur-mukerjee"
                self.content["speakers"][key]["name"] = wrong
                self.assertFails("official spelling")
        self.content = copy.deepcopy(REAL_CONTENT)
        sessions(self.content)["s2"]["brief"] = "Opened by the minister, Shri prahlad Joshi."
        self.assertFails("official spelling is 'Pralhad'")

    def test_renamed_ids(self):
        self.assertIn("pralhad-joshi", REAL_CONTENT["speakers"])
        self.assertIn("deepti-gaur-mukerjee", REAL_CONTENT["speakers"])
        self.assertNotIn("prahlad-joshi", REAL_CONTENT["speakers"])
        self.assertNotIn("deepti-gaur-mukherjee", REAL_CONTENT["speakers"])
        self.assertEqual(sessions(REAL_CONTENT)["s1"]["speakers"][:2], ["pralhad-joshi", "deepti-gaur-mukerjee"])
        self.assertEqual(REAL_CONTENT["days"][0]["dignitaries"][:2], ["pralhad-joshi", "deepti-gaur-mukerjee"])
        for sid in ("pralhad-joshi", "deepti-gaur-mukerjee", "tony-thomas"):
            self.assertEqual(REAL_CONTENT["speakers"][sid]["status"], "confirmed")

    def test_unhyphenated_wellbeing_fails(self):
        for text in ("student wellbeing matters", "Student Wellbeing First", "WELLBEING"):
            with self.subTest(text=text):
                self.content = copy.deepcopy(REAL_CONTENT)
                sessions(self.content)["s3"]["brief"] = text
                self.assertFails('spell it "well-being"')

    def test_wellbeing_allow_list_passes(self):
        sessions(self.content)["s3"]["brief"] = ("Snehita Wellbeing Cell, #NationalWellbeingConclave and "
                                                 "national-wellbeing-conclave-2026 are allowed.")
        self.assertEqual(self.run_build(), 0, self.log)

    def test_changed_tagline_fails(self):
        self.content["event"]["tagline"] = "स्वस्थ मन | समरस समाज"
        self.assertFails("event.tagline", "identity lock")

    def test_apostrophe_in_name_fails(self):
        for name in ("समरस्यम्' 2026", "समरस्यम्’ 2026"):
            with self.subTest(name=name):
                self.content = copy.deepcopy(REAL_CONTENT)
                self.content["event"]["nameDevanagari"] = name
                self.assertFails("event.nameDevanagari")

    def test_apostrophe_in_body_text_fails(self):
        sessions(self.content)["s1"]["brief"] = "Opening समरस्यम्' 2026 today."
        self.assertFails("no apostrophe after")

    def test_other_identity_fields_locked(self):
        for key, value in (("theme", "Mental Wellness"), ("nameFull", "3rd National Wellbeing Conclave"),
                           ("hashtag", "#NWC2026"), ("hashtagDevanagari", "#समरस्यम्"),
                           ("dates", "6-7 December 2026")):
            with self.subTest(key=key):
                self.content = copy.deepcopy(REAL_CONTENT)
                self.content["event"][key] = value
                self.assertFails("event.%s" % key)

    def test_unknown_speaker_id_fails(self):
        sessions(self.content)["s5"]["speakers"].append("no-such-person")
        self.content["days"][0]["dignitaries"].append("also-missing")
        sessions(self.content)["s8"]["moderator"] = "ghost"
        self.assertFails("'no-such-person'", "'also-missing'", "'ghost'")

    def test_tbc_speaker_is_held_back(self):
        self.content["speakers"]["ananya-syal"]["status"] = "tbc"
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertNotIn("Ananya Syal", self.page())
        self.assertIn("Dr. Ananya Syal [tbc] in Session 5", self.log)

    def test_every_unpublished_status_is_held_back(self):
        for status in ("verbally-confirmed", "awaiting", "tbc", "alternate"):
            with self.subTest(status=status):
                self.content = copy.deepcopy(REAL_CONTENT)
                self.content["speakers"]["akshay-anand"]["status"] = status
                self.assertEqual(self.run_build(), 0, self.log)
                self.assertNotIn("Akshay Anand", self.page())

    def test_unknown_status_fails(self):
        self.content["speakers"]["akshay-anand"]["status"] = "Confirmed"
        self.assertFails("speakers.akshay-anand.status")

    def test_held_back_name_leaking_through_other_text_fails(self):
        sessions(self.content)["s2"]["brief"] = "Introduced by Sh Syed Ekram Rizwi."
        self.assertFails("held back")

    def test_preview_build(self):
        self.content["speakers"]["ananya-syal"]["status"] = "tbc"
        self.assertEqual(self.run_build(include_unconfirmed=True), 0, self.log)
        self.assertIn("PREVIEW BUILD", self.log)
        self.assertFalse(os.path.exists(os.path.join(self.root, "site")), "preview must never write site/")
        html = self.page(folder="site-preview")
        self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
        self.assertIn("PREVIEW", html)
        self.assertIn("Ananya Syal", html)
        self.assertIn("(to be confirmed)", html)
        self.assertIn("Disallow: /", self.page("robots.txt", folder="site-preview"))

    def test_bad_times_fail(self):
        s = sessions(self.content)
        s["s5"]["start"] = "9:30"
        s["s6"]["end"] = "12:00"  # before its start (12:30)
        s["s8"]["start"] = "25:00"
        self.assertFails("s5).start", "s6): start 12:30 must be before end 12:00", "s8).start")

    def test_overlap_fails_unless_parallel(self):
        s = sessions(self.content)
        s["s9"]["start"], s["s9"]["end"] = "14:30", "15:45"  # overlaps s8 (14:15-15:00)
        self.assertFails("overlaps")
        self.content = copy.deepcopy(REAL_CONTENT)
        s = sessions(self.content)
        s["s9"]["start"], s["s9"]["end"] = "14:30", "15:45"
        s["s8"]["parallel"] = s["s9"]["parallel"] = True
        self.assertEqual(self.run_build(), 0, self.log)

    def test_out_of_order_sessions_fail(self):
        day = self.content["days"][0]["sessions"]
        day[1], day[2] = day[2], day[1]
        self.assertFails("time order")

    def test_wrong_weekday_fails(self):
        self.content["days"][0]["weekday"] = "Saturday"
        self.assertFails("2026-12-06 is a Sunday")

    def test_schema_errors_are_all_listed(self):
        del self.content["contact"]["email"]
        sessions(self.content)["s2"]["breif"] = "typo"
        self.content["feedback"]["status"] = "maybe"
        sessions(self.content)["s3"]["number"] = "3"
        self.assertFails("contact.email: missing", "breif: unknown key", "feedback.status",
                         "days[0].sessions[3].number: expected a whole number")

    def test_duplicate_json_key_fails(self):
        with open(os.path.join(self.root, "content", "content.en.json"), "w", encoding="utf-8") as f:
            f.write('{"event": {}, "event": {}}')
        code = build_site.build(root=self.root, out=self.output.append)
        self.assertEqual(code, 1)
        self.assertIn("duplicate key", self.log)

    def test_break_with_speakers_fails(self):
        sessions(self.content)["d1-lunch"]["speakers"] = ["ananya-syal"]
        self.assertFails("a break has no speakers")

    def test_contact_email_and_phones_are_checked(self):
        self.content["contact"]["email"] = "nwc@iitb.ac.in"
        self.assertFails("contact.email: must be nwc@iitrpr.ac.in")
        self.content = copy.deepcopy(REAL_CONTENT)
        self.content["emergency"][4]["number"] = "+91 00000"
        self.assertFails("emergency[4].number")
        self.content = copy.deepcopy(REAL_CONTENT)
        self.content["contact"]["people"][0]["phone"] = "231181"
        self.assertFails("contact.people[0].phone")

    def test_nearby_schema(self):
        self.content["nearby"]["groups"][0]["id"] = "far"
        self.assertFails("nearby.groups[0].id")
        self.content = copy.deepcopy(REAL_CONTENT)
        del self.content["nearby"]["groups"][1]["places"][0]["mapsQuery"]
        self.assertFails("nearby.groups[1].places[0].mapsQuery: missing")
        self.content = copy.deepcopy(REAL_CONTENT)
        self.content["nearby"]["groups"][2]["places"][0]["blurb"] = "Bhagat Singh's birthplace."
        self.assertFails("ancestral home")
        self.content = copy.deepcopy(REAL_CONTENT)
        self.content["nearby"]["groups"][0]["places"] = []
        self.assertFails("a group needs at least one place")
        self.content = copy.deepcopy(REAL_CONTENT)
        self.content["nearby"]["groups"][1]["id"] = "close"
        self.assertFails("is used twice")

    def test_broken_anchor_fails(self):
        self.content["ui"]["nav"]["about"] = "About"
        self.assertEqual(self.run_build(), 0, self.log)
        errors = build_site.check_links("x.html", '<a href="#missing">x</a><a href="#">y</a><p id="ok"></p>', None)
        self.assertTrue(any("#missing" in e for e in errors), errors)
        self.assertTrue(any('empty href="#"' in e for e in errors), errors)
        errors = build_site.check_links("x.html", '<a href="tel:+91123">x</a><a href="mailto:a@b.c">y</a>', None)
        self.assertEqual(len(errors), 2, errors)

    def test_missing_asset_fails(self):
        self.content["logos"][0]["src"] = "img/logos/nope.png"
        self.assertFails("static/img/logos/nope.png does not exist")
        self.content = copy.deepcopy(REAL_CONTENT)
        os.remove(os.path.join(self.root, "static", "img", "art", "band.svg"))  # referenced from main.css
        self.assertFails("url(../img/art/band.svg) does not exist")

    def test_feedback_open_requires_google_form(self):
        self.content["feedback"] = {"status": "open", "formUrl": "https://example.com/form", "qr": None}
        self.assertFails("feedback.formUrl")

    def test_feedback_open_state_renders_without_placeholder_qr(self):
        self.content["feedback"] = {"status": "open", "formUrl": "https://docs.google.com/forms/d/e/abc/viewform", "qr": None}
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        self.assertIn('href="https://docs.google.com/forms/d/e/abc/viewform" target="_blank" rel="noopener noreferrer"', html)
        self.assertIn("Thank you for being part of the conclave", html)
        self.assertNotIn("fb-open__qr", html)
        self.assertNotIn("<iframe", html)

    def test_feedback_open_state_with_qr(self):
        self.add_static("img/feedback-qr.png", tiny_png(112, 112))
        self.content["feedback"] = {"status": "open", "formUrl": "https://forms.gle/abc", "qr": "img/feedback-qr.png"}
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        self.assertIn('alt="QR code for the feedback form" width="112" height="112"', html)
        self.assertIn("Scan at the venue", html)

    def test_moments_carousel_renders_from_fixture(self):
        for i in (1, 2, 3):
            self.add_static("img/moments/%d.png" % i, tiny_png(1200, 620))
        self.content["photos"] = {"status": "live", "items": [
            {"src": "img/moments/%d.png" % i, "alt": "Photo %d alt" % i, "caption": "Caption %d" % i,
             "label": "Day 1 · Inaugural Ceremony"} for i in (1, 2, 3)]}
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        self.assertIn('aria-roledescription="carousel"', html)
        self.assertEqual(html.count('class="carousel__slide"'), 3)
        self.assertIn('alt="Photo 2 alt" width="1200" height="620"', html)
        self.assertIn("02 / 03", html)
        self.assertIn('aria-label="Show photo 3"', html)
        self.assertNotIn(">Coming soon<", html)
        self.assertIn("Hand-picked by the organising team", html)

    def test_live_photos_need_items(self):
        self.content["photos"] = {"status": "live", "items": []}
        self.assertFails("there are no items")

    def test_missing_photo_file_fails_and_existing_one_renders(self):
        self.content["speakers"]["sidharth-sood"]["photo"] = "img/speakers/sidharth-sood-352.webp"
        self.assertFails("static/img/speakers/sidharth-sood-352.webp does not exist")
        for size in (128, 352):
            self.add_static("img/speakers/sidharth-sood-%d.webp" % size, b"RIFF\x00\x00\x00\x00WEBP")
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        self.assertIn("assets/img/speakers/sidharth-sood-128.webp?v=", html)
        self.assertIn('alt="Dr. Sidharth Sood" width="64" height="64"', html)
        self.assertRegex(html, r'srcset="assets/img/speakers/sidharth-sood-128\.webp\?v=\w+ 128w, assets/img/speakers/sidharth-sood-352\.webp\?v=\w+ 352w"')

    def test_empty_values_are_hidden_not_blank(self):
        s = sessions(self.content)
        s["s5"]["subtitle"] = ""
        s["s5"]["brief"] = None
        self.content["event"]["programmeNote"] = ""
        self.content["ui"]["hero"]["eyebrow"] = None
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        start = html.index('id="details-s5"')
        block = html[start:html.index("</details>", start)]
        self.assertNotIn("session__brief", block)
        self.assertNotIn("Transforming social", block)
        self.assertNotIn("programme__note", html)
        self.assertNotIn("hero__eyebrow", html)
        visible = re.sub(r'<span [^>]*aria-hidden="true"[^>]*></span>', "", html)  # decorative rules/accents
        self.assertNotRegex(visible, r"<(p|span|h[1-6]|li)( [^>]*)?></\1>")

    def test_session_with_nothing_to_expand_is_plain(self):
        s = sessions(self.content)["s2"]
        s["brief"] = None
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertIn('<div class="session session--plain" data-type="exhibition">', self.page())

    def test_html_is_escaped(self):
        sessions(self.content)["s2"]["brief"] = 'Tags <script>alert(1)</script> & "quotes"'
        self.content["contact"]["people"][0]["name"] = 'Dr. "X" <b>'
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        self.assertIn("Tags &lt;script&gt;alert(1)&lt;/script&gt; &amp; &quot;quotes&quot;", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<b>", html)


class TestAtomicBuild(BuildTestCase):
    def test_failed_build_leaves_live_site_untouched(self):
        self.assertEqual(self.run_build(), 0, self.log)
        marker = os.path.join(self.root, "site", "index.html")
        with open(marker, encoding="utf-8") as f:
            before = f.read()
        self.content["event"]["tagline"] = "changed"
        self.assertEqual(self.run_build(), 1)
        with open(marker, encoding="utf-8") as f:
            self.assertEqual(f.read(), before)
        self.assertFalse(os.path.exists(os.path.join(self.root, "site.tmp")))

    def test_rebuild_replaces_site_and_cleans_up(self):
        self.assertEqual(self.run_build(), 0, self.log)
        stale = os.path.join(self.root, "site", "stale.html")
        open(stale, "w").close()
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertFalse(os.path.exists(stale))
        for leftover in ("site.tmp", "site.old"):
            self.assertFalse(os.path.exists(os.path.join(self.root, leftover)))

    def test_asset_version_changes_with_static_files(self):
        self.run_build()
        first = self.page()
        with open(os.path.join(self.root, "static", "css", "main.css"), "a", encoding="utf-8") as f:
            f.write("\n/* changed */\n")
        self.run_build()
        self.assertNotEqual(first, self.page())
        self.assertRegex(self.page(), r'assets/css/main\.css\?v=[0-9a-f]{10}"')


class TestHindi(BuildTestCase):
    def hindi(self):
        hi = copy.deepcopy(REAL_CONTENT)
        hi["event"]["theme"] = "मानसिक कल्याण, सामाजिक समरसता और सामूहिक विकास"
        hi["ui"]["nav"]["about"] = "परिचय"
        hi["days"][0]["weekday"] = "रविवार"
        return hi

    def test_matching_hindi_file_builds_hi_folder(self):
        self.save(self.hindi(), "content.hi.json")
        self.assertEqual(self.run_build(), 0, self.log)
        hi_html = self.page("hi/index.html")
        self.assertIn('<html lang="hi">', hi_html)
        self.assertIn('href="../assets/css/main.css', hi_html)
        self.assertIn("परिचय", hi_html)
        self.assertIn('href="hi/"', self.page())  # language toggle on the English page
        self.assertIn("https://iitrpr.ac.in/national-wellbeing-conclave-2026/hi/", self.page("sitemap.xml"))

    def test_no_language_toggle_without_hindi(self):
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertNotIn('class="lang"', self.page())

    def test_hindi_with_missing_key_fails(self):
        hi = self.hindi()
        del hi["about"]["quote"]
        self.save(hi, "content.hi.json")
        self.assertFails("hi about: missing key 'quote'")

    def test_hindi_with_changed_invariants_fails(self):
        hi = self.hindi()
        hi["speakers"]["pralhad-joshi"]["status"] = "tbc"
        hi["days"][0]["sessions"][1]["start"] = "09:00"
        hi["event"]["tagline"] = "something else"
        self.save(hi, "content.hi.json")
        self.assertFails("speakers.pralhad-joshi.status", "sessions[1].start", "event.tagline")

    def test_hindi_with_extra_list_item_fails(self):
        hi = self.hindi()
        hi["benefits"].append({"audience": "x", "text": "y"})
        self.save(hi, "content.hi.json")
        self.assertFails("hi benefits: expected a list of 3 items")


class TestHelpers(unittest.TestCase):
    def test_initials(self):
        self.assertEqual(build_site.initials("Dr. Ananya Syal"), "AS")
        self.assertEqual(build_site.initials("Prof. (Dr.) J. C. Suri"), "JS")
        self.assertEqual(build_site.initials("Ms. Geeta Mehrotra and Team"), "GM")
        self.assertEqual(build_site.initials("Sh Syed Ekram Rizwi"), "SR")

    def test_tel_href(self):
        self.assertEqual(build_site.tel_href("+91-1881-231181"), "tel:+911881231181")
        self.assertEqual(build_site.tel_href("+91 1881 232505"), "tel:+911881232505")
        self.assertEqual(build_site.tel_href("1800-89-14416"), "tel:18008914416")
        self.assertTrue(build_site.TEL_RE.match("tel:+911881232505"))
        self.assertTrue(build_site.TEL_RE.match("tel:18008914416"))
        self.assertFalse(build_site.TEL_RE.match("tel:+91188123250"))

    def test_phone_display(self):
        self.assertEqual(build_site.phone_display("+91-1881-231181"), "+91 1881 231181")

    def test_image_size(self):
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "x.png")
            with open(path, "wb") as f:
                f.write(tiny_png(7, 5))
            self.assertEqual(build_site.image_size(path), (7, 5))
            svg = os.path.join(tmp, "x.svg")
            with open(svg, "w") as f:
                f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 560"></svg>')
            self.assertEqual(build_site.image_size(svg), (1440, 560))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
