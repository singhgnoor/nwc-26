# समरस्यम् 2026 · Samarasyam 2026 · 3rd National Well-being Conclave: web portal

The official portal of the 3rd National Well-being Conclave, 6–7 December 2026, hosted by IIT Ropar with the Department of Higher Education, Ministry of Education, Government of India.

**Live address:** https://iitrpr.ac.in/national-wellbeing-conclave-2026/

It's a static site. A small build script turns one JSON file into HTML, and a small Python server serves only the built folder behind nginx. Both use only Python's standard library (3.8+). There is no database, no API and nothing to `pip install`. Deployment: [`deploy/DEPLOY.md`](deploy/DEPLOY.md).

## Run it locally

```sh
python3 build_site.py      # validate content/content.en.json and build site/
python3 server.py          # serve site/ on port 8100
```

Open http://127.0.0.1:8100/national-wellbeing-conclave-2026/ (http://127.0.0.1:8100/ works too).

```sh
python3 -m unittest                           # all tests
python3 build_site.py --check                 # validate only, write nothing
python3 build_site.py --include-unconfirmed   # PREVIEW with unconfirmed speakers, into site-preview/
NWC_SITE_DIR=site-preview python3 server.py   # look at the preview
```

On Windows, use `python` instead of `python3`.

## Layout

| Path | What it is |
|---|---|
| `server.py` | The web server. Serves `site/` only; strips the URL prefix; GET/HEAD only; security headers; no directory listings; blocks traversal and dotfiles. |
| `build_site.py` | Validates the content, renders `templates/` into `site/` atomically, copies `static/` to `site/assets/`. Holds the identity constants. |
| `content/content.en.json` | **All page text.** Content changes never need code changes. |
| `templates/` | HTML stubs (`base.html` plus one partial per section) with `$placeholders`. Structure only; the visual design comes later from Figma. |
| `static/` | `css/main.css` (colour and type tokens only), `js/main.js` (tabs, countdown, hover hook), `img/`, `fonts/`. |
| `site/` | Build output: the **only** folder the server exposes. Not in git. |
| `deploy/` | systemd unit, nginx snippet, `update.sh`, runbook. |
| `tests/` | `unittest` tests for the server, the build and Python 3.8 compatibility. |

## Editing content (`content/content.en.json`)

- **Hiding something:** set any optional text to `""` or `null` and that element disappears. The build never renders an empty box.
- **Speakers** are defined once under `speakers` and referenced by ID from sessions (`moderator`, `speakers`, `voteOfThanks`) and from `dignitaries`.
- **`status` decides who appears.** It must be one of `confirmed`, `verbally-confirmed`, `awaiting`, `tbc`, `ex-officio` or `alternate`. Only `confirmed` and `ex-officio` are published. Everyone else is left out of the page and listed by the build. To publish someone, change their status; nothing else.
- **Photos:** put the file in `static/img/speakers/` and set `"photo": "img/speakers/name.webp"`. Without a photo, the person's initials are shown.
- **Times** are 24-hour `HH:MM` and are displayed V5-style ("09.30 – 10.15"). `"end": null` shows "onwards". `"timeLabel"` overrides the displayed time (used for "06.30 / 07.00"). Sessions must be in time order and must not overlap unless both are marked `"parallel": true`.
- **Feedback:** when the Google Form is ready, set `"feedback": {"status": "open", "formUrl": "https://docs.google.com/forms/..."}`.
- **Photos after the event:** set `"photos": {"status": "live", "items": [{"src": "img/moments/1.webp", "alt": "...", "caption": "..."}]}`.
- **Logos:** add files under `static/img/logos/` and list them in `"logos": [{"src": "img/logos/iit-ropar.svg", "alt": "IIT Ropar"}]`.
- **Interface wording** (navigation, headings, "Photos coming soon", type tags, month names) is in `ui`, so a Hindi file can translate it.

### What the build refuses (the site stays unchanged when it fails)

1. **Schema:** missing or misspelt keys, wrong types, unknown speaker IDs, bad or overlapping times, a wrong weekday for a date, duplicate JSON keys.
2. **Identity lock:** the name, Devanagari name, tagline, theme, dates, venue, hashtag and slug must equal the constants at the top of `build_site.py`, which come from the Ministry (17 Nov 2026). Any apostrophe after समरस्यम्, anywhere, is an error.
3. **Placeholders:** `TODO`, `TBC`, `lorem`, `00000`, `XXX`, `placeholder`, an empty `href`/`src`, or an unfilled `$variable` anywhere in the output.
4. **Spelling:** "wellbeing" without the hyphen anywhere in the output. Allowed only in `#NationalWellbeingConclave`, `national-wellbeing-conclave-2026` and `Snehita Wellbeing Cell`.
5. **CSP safety:** inline `<script>`, `<style>`, `style=` or `on…=` handlers, all of which the Content-Security-Policy would block.
6. **Leaks:** the name of a held-back (unconfirmed) person appearing anywhere on the page.

### Hindi version (ready, not started)

Create `content/content.hi.json` as a translated copy of the English file. It must have the same keys, list lengths, IDs, times and statuses; the build checks this. The build then writes `site/hi/index.html` and adds an EN | हिन्दी toggle and `hreflang` links. No nginx change is needed. In the Hindi file the name, Devanagari name, tagline, hashtag and slug stay locked; the theme, dates and venue may be translated. Use the official Hindi wording from the Dean's office or MoE, reviewed by the Rajbhasha cell.

## Decisions taken in this build (17 Nov 2026)

These follow `content-tracker.md` and the Ministry's root decision. Change them in `content/content.en.json` if the Dean's office decides otherwise.

- **Publish rule.** Following V5's legend ("no status = institutional or ex officio role"), these people are `ex-officio` and shown: Prof. Rajeev Ahuja, "Dean, Student Affairs, IIT Ropar", Dr. Surya Kant Sahdeo, Dr. Suryasnata Tripathy, Dr. Parwinder Singh, Dr. Dhiraj Mahajan, Shri Devendra Kumar Sharma, and Ms. Geeta Mehrotra and Team (shown without a designation until one arrives). Held back: the Minister and the Secretary (`tbc`), Dr. Ram Manohar Singh and Dr. Jyoti Mishra (`verbally-confirmed`), Dr. Nancy Sahni (`awaiting`), and the three Session 6 alternates.
- **Session 4 shows no presenter.** V5 lists either the Joint Secretary or the Director. Sh Syed Ekram Rizwi is kept as `tbc` (the spelling "Rizwi"/"Rizvi" is unconfirmed) and isn't linked to the session. When the Dean's office names the presenter, add their ID to `s4.speakers`.
- **Unnamed people are not entered:** the Session 11 clinical psychologist and the Session 14 CFIs.
- **Briefs only, no expected outcomes** (17 Nov decision). `outcomes` stays in the schema but is empty, and empty lists are hidden.
- **Session 10** is split as in Figma v3.1: the 16.00 card carries paragraph 1 of the brief, and an unnumbered 16.45 card carries paragraph 2.
- **Session 3** has no subtitle until the Dean's office answers whether to use "The Well-being Model of IIT Ropar: Where Excellence Meets Emotional Wellness".
- **Session summaries** show the title *and* the subtitle (the panel topic), as on the Figma cards. The body shows the brief and the people.
- **Journey** uses the MoE carousel figures (13 Nov), which are the Ministry's own published numbers. The tracker still lists formal sign-off as pending: set `journey.heading` to `null` to hide the section if sign-off is refused.
- **Emergency numbers** are the 24/7 subset from the tracker. The Conclave helpdesk number is left out until it exists.
- **Footer credit** ("Designed and developed by SAC Team") is `null` until the office confirms it.
- **Preview builds** go to `site-preview/` and can never overwrite the live `site/`.
- **Assets** get a 1-day cache plus a content-hash `?v=` in their URLs, so CSS/JS changes reach visitors immediately. HTML is never cached.

## Still needed (from the Dean's office, MoE, IT)

| Item | Where it goes |
|---|---|
| Logos: MMTTP, GoI emblem + MoE/DoHE lockup, IIT Ropar seal (SVG) | `static/img/logos/` + `logos` |
| Speaker headshots and short bios, with permission to publish | `static/img/speakers/` + `photo`, `bio` |
| Confirmation for TBC / verbally confirmed / awaiting speakers | change `status` |
| Session 4 presenter and the spelling of "Rizwi" | `s4.speakers`, `speakers.syed-ekram-rizwi` |
| Name of the Dean, Student Affairs (Session 3), or keep the role only | `speakers.dean-student-affairs` |
| Session 6 nutrition speaker; Session 11 psychologist; Session 14 CFIs | `speakers`, session `speakers` |
| Ms. Geeta Mehrotra's designation / organisation | `speakers.geeta-mehrotra` |
| Venues / halls for each session | session `venue` |
| Yoga / Campus Walk: 06.30 or 07.00 | `d2-yoga.start`, `timeLabel` |
| Conclave helpdesk number | `emergency` |
| Google Form URL (after the event) | `feedback` |
| Sign-off on the MoE journey figures | `journey` |
| Footer credit wording; social handles | `footer` |
| Self-hosted font files (Eczar, Mukta, Tiro Devanagari Hindi, Mukta Mahee) | `static/fonts/` + `@font-face` in the CSS |
| Open Graph image (1200×630) for link previews in mail/WhatsApp | `static/img/` + an `og:image` tag in `templates/base.html` |
| Hosting: machine, whether nginx runs on the same machine, the `nwc` user, uptime monitor | `deploy/DEPLOY.md` |
| Full visual design (from Figma) | `templates/`, `static/css/`, hero SVG in `.hero-art` |

## Notes for later work

- **CSP:** `style-src 'self'` and `script-src 'self'` mean no inline styles or scripts. That includes `style="..."` attributes in hero SVG markup: use classes and the stylesheet. Google Fonts can't be linked; fonts must be self-hosted in `static/fonts/`. An embedded Google Form iframe is allowed (`frame-src https://docs.google.com`).
- **`robots.txt`** under a subpath is advisory only (crawlers read `iitrpr.ac.in/robots.txt`). The `noindex` meta tag is what keeps preview builds out of search engines.
- **Zeitgeist:** this repository changes nothing in the Zeitgeist site. Its exposed `.git`, `server.py` and database are a separate issue to report to the seniors (see `project-context.md`). Keep this repository private, since its planning notes describe that issue.
