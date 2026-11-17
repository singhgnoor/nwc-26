"""build_site.py: validators, publish rule, output scan, atomic build, Hindi support."""
import copy
import json
import os
import re
import shutil
import tempfile
import unittest
from html.parser import HTMLParser

from tests.helpers import REPO

import build_site  # noqa: E402  (tests.helpers puts the repo on sys.path)

with open(os.path.join(REPO, "content", "content.en.json"), encoding="utf-8") as f:
    REAL_CONTENT = json.load(f)


def sessions(content):
    return {s["id"]: s for day in content["days"] for s in day["sessions"]}


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
    def test_builds_and_holds_back_unconfirmed(self):
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        for held in ("Prahlad Joshi", "Deepti Gaur Mukherjee", "Ram Manohar Singh", "Nancy Sahni",
                     "Jyoti Mishra", "Rizwi", "Bani Tamber Aeri", "Sunita Malhotra", "Poonam Khanna"):
            self.assertNotIn(held, html)
            self.assertIn(held, self.log)  # listed in the held-back summary
        for shown in ("Dr. Ananya Syal", "Prof. Rajeev Ahuja", "Dr. Jitendra Nagpal", "Speaker and Moderator",
                      "Ms. Geeta Mehrotra and Team", "Shri Devendra Kumar Sharma"):
            self.assertIn(shown, html)
        self.assertNotIn("noindex", html)
        self.assertNotIn("PREVIEW", html)
        for rel in ("404.html", "robots.txt", "sitemap.xml", "assets/css/main.css", "assets/js/main.js"):
            self.assertTrue(os.path.isfile(os.path.join(self.root, "site", *rel.split("/"))), rel)
        self.assertFalse(os.path.exists(os.path.join(self.root, "site", "assets", "img", ".gitkeep")))

    def test_identity_and_markup(self):
        self.run_build()
        html = self.page()
        self.assertIn('<html lang="en">', html)
        self.assertIn("<title>Samarasyam 2026 · 3rd National Well-being Conclave · IIT Ropar</title>", html)
        self.assertIn('<span lang="hi">समरस्यम् 2026</span>', html)
        self.assertIn('<span lang="hi">स्वस्थ मन | समरस समाज | सशक्त राष्ट्र</span>', html)
        self.assertIn('<meta property="og:url" content="https://iitrpr.ac.in/national-wellbeing-conclave-2026/">', html)
        self.assertIn('role="tablist"', html)
        self.assertIn('<details class="session" id="session-s5" data-type="panel">', html)
        self.assertIn('<div class="session session--break" id="session-d1-lunch"', html)
        self.assertIn("19.00</time> onwards", html)
        self.assertIn(">06.30 / 07.00</time>", html)
        self.assertIn("Photos coming soon", html)
        self.assertIn("Feedback opens after the event", html)
        self.assertIn('href="tel:18008914416"', html)
        self.assertIn('href="mailto:nwc@iitrpr.ac.in"', html)
        # relative paths only, and no third-party requests
        self.assertNotIn('href="/', html)
        self.assertNotIn('src="/', html)
        self.assertNotRegex(html, r'(?:src|href)="https?://(?!iitrpr\.ac\.in/)')
        # the brief's Devanagari word is marked as Hindi; no apostrophe after the name
        self.assertIn('formally open <span lang="hi">समरस्यम्</span> 2026', html)
        self.assertNotIn("समरस्यम्'", html)

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
        self.assertEqual(sorted(set(r for r in refs if r not in ids)), [])
        self.assertEqual(html.count("<h1"), 1)
        # every section from the spec is present, in order
        order = [html.index('id="%s"' % s) for s in ("hero", "glance", "about", "benefits", "programme",
                                                      "speakers", "journey", "moments", "feedback", "contact")]
        self.assertEqual(order, sorted(order))
        self.assertLess(html.index("<header"), order[0])
        self.assertGreater(html.index("<footer"), order[-1])


class TagChecker(HTMLParser):
    VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "wbr"}

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
        if not self.stack or self.stack[-1] != tag:
            self.errors.append("unexpected </%s> at %s" % (tag, self.getpos()))
        else:
            self.stack.pop()


class TestValidators(BuildTestCase):
    def test_placeholder_text_fails(self):
        for token in ("TODO", "TBC", "lorem ipsum", "+91 00000 00000", "XXX", "placeholder"):
            with self.subTest(token=token):
                content = copy.deepcopy(REAL_CONTENT)
                sessions(content)["s2"]["brief"] = "Brief with %s inside." % token
                self.content = content
                self.assertFails("BUILD FAILED", token.split()[0] if token != "+91 00000 00000" else "00000")

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
                           ("hashtag", "#NWC2026"), ("dates", "6-7 December 2026")):
            with self.subTest(key=key):
                self.content = copy.deepcopy(REAL_CONTENT)
                self.content["event"][key] = value
                self.assertFails("event.%s" % key)

    def test_unknown_speaker_id_fails(self):
        sessions(self.content)["s5"]["speakers"].append("no-such-person")
        self.content["dignitaries"].append("also-missing")
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
        sessions(self.content)["s2"]["brief"] = "Opened by Shri Prahlad Joshi."
        self.assertFails("held back")

    def test_preview_build(self):
        self.content["speakers"]["ananya-syal"]["status"] = "tbc"
        self.assertEqual(self.run_build(include_unconfirmed=True), 0, self.log)
        self.assertIn("PREVIEW BUILD", self.log)
        self.assertFalse(os.path.exists(os.path.join(self.root, "site")), "preview must never write site/")
        html = self.page(folder="site-preview")
        self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
        self.assertIn("PREVIEW", html)
        self.assertIn("Prahlad Joshi", html)
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

    def test_feedback_open_requires_google_form(self):
        self.content["feedback"] = {"status": "open", "formUrl": "https://example.com/form"}
        self.assertFails("feedback.formUrl")
        self.content["feedback"] = {"status": "open", "formUrl": "https://docs.google.com/forms/d/e/abc/viewform"}
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertIn('href="https://docs.google.com/forms/d/e/abc/viewform"', self.page())
        self.assertNotIn("<iframe", self.page())

    def test_missing_photo_file_fails_and_existing_one_renders(self):
        self.content["speakers"]["ananya-syal"]["photo"] = "img/speakers/ananya-syal.webp"
        self.assertFails("static/img/speakers/ananya-syal.webp does not exist")
        os.makedirs(os.path.join(self.root, "static", "img", "speakers"))
        with open(os.path.join(self.root, "static", "img", "speakers", "ananya-syal.webp"), "wb") as f:
            f.write(b"RIFF")
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertIn('src="assets/img/speakers/ananya-syal.webp"', self.page())

    def test_empty_values_are_hidden_not_blank(self):
        s = sessions(self.content)
        s["s5"]["subtitle"] = ""
        s["s5"]["brief"] = None
        self.content["event"]["programmeNote"] = ""
        self.content["ui"]["heroEyebrow"] = None
        self.assertEqual(self.run_build(), 0, self.log)
        html = self.page()
        start = html.index('id="session-s5"')
        block = html[start:html.index("</details>", start)]
        self.assertNotIn("session__subtitle", block)
        self.assertNotIn("session__brief", block)
        self.assertNotIn("programme__note", html)
        self.assertNotIn("hero__eyebrow", html)
        self.assertNotRegex(html, r"<(p|span|h[1-6]|li)( [^>]*)?></\1>")

    def test_session_with_nothing_to_expand_is_plain(self):
        s = sessions(self.content)["s2"]
        s["brief"] = None
        self.assertEqual(self.run_build(), 0, self.log)
        self.assertIn('<div class="session session--plain" id="session-s2"', self.page())

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

    def test_hindi_with_missing_key_fails(self):
        hi = self.hindi()
        del hi["about"]["quote"]
        self.save(hi, "content.hi.json")
        self.assertFails("hi about: missing key 'quote'")

    def test_hindi_with_changed_invariants_fails(self):
        hi = self.hindi()
        hi["speakers"]["prahlad-joshi"]["status"] = "confirmed"
        hi["days"][0]["sessions"][1]["start"] = "09:00"
        hi["event"]["tagline"] = "something else"
        self.save(hi, "content.hi.json")
        self.assertFails("speakers.prahlad-joshi.status", "sessions[1].start", "event.tagline")

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
        self.assertEqual(build_site.tel_href("1800-89-14416"), "tel:18008914416")


if __name__ == "__main__":
    unittest.main()
