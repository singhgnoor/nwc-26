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
| `templates/` | `base.html` plus one partial per section, with `$variables` the build fills. `_sprite.html` is the inline icon set (from Figma). |
| `static/` | `css/main.css` (the whole design, mobile-first), `js/main.js` (tabs, countdown, scroll-spy, mobile menu, carousel), `fonts/` (self-hosted, OFL), `img/` (art, logos, speaker photos, favicons, OG image). |
| `tools/` | **Dev-only** helpers (pip packages allowed, see `tools/requirements-dev.txt`): `prepare_photos.py`, `prepare_logos.py`, `render_assets.py`, `screenshots.py`, `check_links.py`. Only their outputs are committed. Never needed on the server. |
| `site/` | Build output: the **only** folder the server exposes. Not in git. |
| `deploy/` | systemd unit, nginx snippet, `update.sh`, runbook. |
| `tests/` | `unittest` tests for the server, the build and Python 3.8 compatibility. |

## Editing content (`content/content.en.json`)

- **Hiding something:** set any optional text to `""` or `null` and that element disappears. The build never renders an empty box.
- **Speakers** are defined once under `speakers` and referenced by ID from sessions (`moderator`, `speakers`, `voteOfThanks`) and from each day's `dignitaries`.
- **Dignitaries & speakers (section 03)** follows the selected day, as in the two Figma frames: each day lists its `dignitaries` (shown with the `dignitariesLabel` eyebrow, e.g. "Inaugural Ceremony"), and the grid is built automatically from that day's moderators and speakers, minus the day's dignitaries, vote-of-thanks people and anyone with `"grid": false` (role-only entries such as "Dean, Student Affairs").
- **`status` decides who appears.** It must be one of `confirmed`, `verbally-confirmed`, `awaiting`, `tbc`, `ex-officio` or `alternate`. Only `confirmed` and `ex-officio` are published. Everyone else is left out of the page and listed by the build. To publish someone, change their status; nothing else.
- **Photos:** add the source to `imgaes/`, map it in `tools/photo_map.json` and run `python tools/prepare_photos.py --write-content`. It writes `static/img/speakers/<id>-128.webp`, `-208` and `-352` (never upscaled) and sets `"photo"` to the largest. Without a photo, the neutral avatar from the design is shown.
- **Times** are 24-hour `HH:MM` and are displayed V5-style ("09.30 – 10.15"). `"end": null` shows "onwards". `"timeLabel"` overrides the displayed time (used for "06.30 / 07.00"). Sessions must be in time order and must not overlap unless both are marked `"parallel": true`.
- **Feedback:** when the Google Form is ready, set `"feedback": {"status": "open", "formUrl": "https://docs.google.com/forms/...", "qr": null}`. To show the QR code at the venue, add the image (e.g. `static/img/feedback-qr.png`) and set `"qr": "img/feedback-qr.png"`; without it the QR box is not shown.
- **Photos after the event:** set `"photos": {"status": "live", "items": [{"src": "img/moments/1.webp", "alt": "...", "caption": "...", "label": "Day 1 · Inaugural Ceremony"}]}` (1200 × 620 crops look best). The carousel replaces the "Coming soon" card.
- **Logos:** files live in `static/img/logos/` (sources in `SOURCES.md`); the `logos` list sets order, `alt` and the text lines of the Ministry lockup.
- **Around IIT Ropar:** the `nearby` block (groups `close`, `half`, `day`; each place has `name`, `blurb`, `drive`, `note`, `mapsQuery`). Each card links to `https://www.google.com/maps/search/?api=1&query=<mapsQuery>`.
- **Interface wording** (navigation, section headings and intros, button labels, countdown, carousel, footer labels, type tags, month names) is in `ui`, so a Hindi file can translate it.

### What the build refuses (the site stays unchanged when it fails)

1. **Schema:** missing or misspelt keys, wrong types, unknown speaker IDs, bad or overlapping times, a wrong weekday for a date, duplicate JSON keys.
2. **Identity lock:** the name, Devanagari name, tagline, theme, dates, venue, both hashtags and the slug must equal the constants at the top of `build_site.py`, which come from the Ministry (17 Nov 2026). Any apostrophe after समरस्यम्, anywhere, is an error.
3. **Placeholders:** `TODO`, `TBC`, `lorem`, `00000`, `XXX`, `placeholder`, `sample`, "Speaker Name", "Designation, Institution", "Name of the Chief Guest", a bare Designation/Institution label, "coming soon" anywhere except the designed Moments card, an empty `href`/`src`, a `javascript:` link, or an unfilled `$variable` anywhere in the output. (Real words such as "Institutions" are fine: the checks match phrases, not single words.)
4. **Official spellings:** "Prahlad" and "Mukherjee" anywhere in the content or output (the Ministry writes Pralhad Joshi and Deepti Gaur Mukerjee).
5. **Links and assets:** every `href="#x"` needs a matching `id`; every `src`, `srcset` entry and CSS `url()` must exist in `static/`; `tel:` links must be +91 and 10 digits or a 1800 toll-free number; `mailto:` must be nwc@iitrpr.ac.in.
6. **Spelling:** "wellbeing" without the hyphen anywhere in the output. Allowed only in `#NationalWellbeingConclave`, `national-wellbeing-conclave-2026` and `Snehita Wellbeing Cell`.
7. **CSP safety:** inline `<script>`, `<style>`, `style=` or `on…=` handlers, all of which the Content-Security-Policy would block.
8. **Leaks:** the name of a held-back (unconfirmed) person appearing anywhere on the page.

### Hindi version (ready, not started)

Create `content/content.hi.json` as a translated copy of the English file. It must have the same keys, list lengths, IDs, times and statuses; the build checks this. The build then writes `site/hi/index.html` and adds an EN | हिन्दी toggle and `hreflang` links. No nginx change is needed. In the Hindi file the name, Devanagari name, tagline, hashtag and slug stay locked; the theme, dates and venue may be translated. Use the official Hindi wording from the Dean's office or MoE, reviewed by the Rajbhasha cell.

## Decisions taken in the design build (26 Nov 2026)

Agreed with Gurnoor on 26 Nov unless marked as a default. All are content edits if they change.

- **Design:** Figma v3.3 (`84ACfsxiRu5u9j5rUMHtZa`) is the source of truth: desktop frames `10:2` (Day 1) and `100:2173` (Day 2), mobile patterns from `33:2` and `36:761`, filled with the real desktop content. The mobile frame's sample text (day theme, venues, "Main Auditorium foyer", "Chief Guest" labels, +91 00000 00000) is not used.
- **Published (verified 26 Nov):** Shri **Pralhad** Joshi and Ms. Deepti Gaur **Mukerjee** (official spellings; IDs `pralhad-joshi`, `deepti-gaur-mukerjee`) and Dr. Tony Thomas are `confirmed`. Only Sh Syed Ekram Rizwi is held back.
- **Not shown although the Figma has them:** "Dr. Puneet Pasricha" on Session 3 (in no source; the card shows the role "Dean, Student Affairs, IIT Ropar"), Rizwi/Sharma on Session 4 (no presenter, as decided 17 Nov), the Session 11 "Clinical Psychologist" entry, every status label ("TBC", "Verbally Confirmed"), Geeta Mehrotra's invented grid sub-labels, and Session 10's stakeholder-group list (the card shows the brief only, as in Figma).
- **Designations:** the V6 wording for Dr. Ananya Syal, Dr. Asha Banu Soletti, Dr. Akshay Anand and Dr. Sujata Sriram (the Figma used short forms).
- **Titles where V6 and the tracker differ** (Session 7 "(followed by a briefing…)", Session 4 "of the Department of Higher Education"): the tracker wording, which ranks above V6.
- **No venues** on the cards: V6 has none, so the meta slot shows the session number.
- **About:** as in the Figma: heading, the italic line "Student Well-being First: Empowering Minds, Transforming Lives.", and the MoE statement in the framed quote card.
- **Emergency rows:** the Figma's five (Medical Centre, Ambulance (the Medical Centre mobile), Campus Security, Tele-MANAS, Conclave Helpdesk **+91 1881 232505**). The helpdesk shares Dr. Tripathy's number.
- **Footer:** both hashtags (`#समरस्यम्2026` and `#NationalWellbeingConclave`), "Designed and developed by **SAC Team**", IIT Ropar's five official social accounts in the Figma order.
- **Logos:** the official files, with sources in `static/img/logos/SOURCES.md`. The MMTTP logo is the official horizontal lockup from mmc.ugc.ac.in, shown whole (the Figma's 72 px circle slot is a placeholder; cropping the official artwork would alter it). The IIT Ropar "SVG" is a PNG inside an SVG, so the seals are raster (WebP). The emblem is rendered unaltered from Wikimedia Commons, with सत्यमेव जयते.
- **Speakers section follows the selected day** (Day 1 frame vs Day 2 frame); without JS both days show. The intro reads "Dignitaries and resource persons for Day 1, Sunday 6 December." (the Figma's "Portraits and short profiles will be added…" sentence is dropped: portraits are in, and no bios exist).
- **People without a photo** get the design's neutral avatar (silhouette), not initials.
- **Countdown** counts whole IST calendar days to 6 Dec; on 6–7 Dec (IST) it reads "Happening now · Day N"; after 7 Dec it disappears. Without JS it shows the date. Day 2 is the default tab on 7 Dec IST.
- **Hero art** is three external SVGs (wide and mobile crops via `<picture>`, plus the gate pillars) rather than inline SVG: about 90 KB of markup that the browser can now cache, and the server does not compress. They contain no `style=` attributes.
- **Map links** carry the accessible name "Open in Google Maps: <place> (opens in a new tab)": it names the place and contains the visible text (WCAG label-in-name).
- **Fonts:** Devanagari in Mukta 600/700 (the footer hashtag) uses the Mukta 500 file, saving about 200 KB; restore separate files if a full Hindi page is added.
- **New interface wording** not in any source (approved 26 Nov): "Happening now · Day 1/2", "View speakers"/"Hide speakers", menu, carousel and "(opens in a new tab)" labels.

## Decisions taken in this build (17 Nov 2026)

Kept unless superseded above.

- **Publish rule.** Following V5's legend ("no status = institutional or ex officio role"), these people are `ex-officio` and shown: Prof. Rajeev Ahuja, "Dean, Student Affairs, IIT Ropar", Dr. Surya Kant Sahdeo, Dr. Suryasnata Tripathy, Dr. Parwinder Singh, Dr. Dhiraj Mahajan, Shri Devendra Kumar Sharma, and Ms. Geeta Mehrotra and Team (shown without a designation until one arrives). Held back: the Minister and the Secretary (`tbc`), Dr. Ram Manohar Singh and Dr. Jyoti Mishra (`verbally-confirmed`), Dr. Nancy Sahni (`awaiting`), and the three Session 6 alternates.
- **Session 4 shows no presenter.** V5 lists either the Joint Secretary or the Director. Sh Syed Ekram Rizwi is kept as `tbc` (the spelling "Rizwi"/"Rizvi" is unconfirmed) and isn't linked to the session. When the Dean's office names the presenter, add their ID to `s4.speakers`.
- **Unnamed people are not entered:** the Session 11 clinical psychologist and the Session 14 CFIs.
- **Briefs only, no expected outcomes** (17 Nov decision). `outcomes` stays in the schema but is empty, and empty lists are hidden.
- **Session 10** is split as in Figma v3.1: the 16.00 card carries paragraph 1 of the brief, and an unnumbered 16.45 card carries paragraph 2.
- **Session 3** has no subtitle until the Dean's office answers whether to use "The Well-being Model of IIT Ropar: Where Excellence Meets Emotional Wellness".
- **Session summaries** show the title *and* the subtitle (the panel topic), as on the Figma cards. The body shows the brief and the people.
- **Journey** uses the MoE carousel figures (13 Nov), which are the Ministry's own published numbers. The tracker still lists formal sign-off as pending: set `journey.heading` to `null` to hide the section if sign-off is refused.
- **Preview builds** go to `site-preview/` and can never overwrite the live `site/`.
- **Assets** get a 1-day cache plus a content-hash `?v=` in their URLs, so CSS/JS changes reach visitors immediately. HTML is never cached.

## Still needed (from the Dean's office, MoE, IT)

| Item | Where it goes |
|---|---|
| Photos for Dr. Sidharth Sood, Dr. Parwinder Singh, Dr. Dhiraj Mahajan, Dr. Surya Kant Sahdeo, Dr. Suryasnata Tripathy (and the Dean, Student Affairs if named) | `imgaes/` + `tools/photo_map.json` |
| Better-resolution photos (optional): Dr. Akshay Anand, Dr. Ananya Syal, Dr. Mayuri Duggirala, Dr. Jitendra Nagpal, Ms. Geeta Mehrotra (headshot) | same |
| Short bios, with permission to publish | `speakers.*.bio` |
| A vector MMTTP logo (optional: the official PNG works) and a true vector IIT Ropar seal (optional) | `static/img/logos/` |
| Session 4 presenter and the spelling of "Rizwi" | `s4.speakers`, `speakers.syed-ekram-rizwi` |
| Name of the Dean, Student Affairs (Session 3), or keep the role only | `speakers.dean-student-affairs` |
| Session 11 psychologist; Session 14 CFIs | `speakers`, session `speakers` |
| Ms. Geeta Mehrotra's designation / organisation | `speakers.geeta-mehrotra` |
| Venues / halls for each session | session `venue` |
| Yoga / Campus Walk: 06.30 or 07.00 | `d2-yoga.start`, `timeLabel` |
| Google Form URL and (optional) QR image, after the event | `feedback` |
| Hand-picked photos after the event | `photos` |
| Sign-off on the MoE journey figures | `journey` |
| Hosting: machine, whether nginx runs on the same machine, the `nwc` user, uptime monitor | `deploy/DEPLOY.md` |

## Dev tools (`tools/`, never deployed)

```sh
pip install -r tools/requirements-dev.txt && python -m playwright install chromium
python tools/prepare_photos.py [--write-content]   # face-centred crops + tools/out/contact-sheet.png
python tools/prepare_logos.py --emblem Emblem_of_India.svg --mmttp ugc_logo.png
python tools/render_assets.py                      # favicon PNGs + og-image.png (from tools/og-card.html)
python tools/screenshots.py [--states] [--axe] [--nojs] [--only 390,1440]   # tools/out/*.png
python tools/check_links.py [--maps-screenshots]   # external links, needs network
```

## Notes for later work

- **CSP:** `style-src 'self'` and `script-src 'self'` mean no inline styles or scripts. That includes `style="..."` attributes in hero SVG markup: use classes and the stylesheet. Google Fonts can't be linked; fonts must be self-hosted in `static/fonts/`. An embedded Google Form iframe is allowed (`frame-src https://docs.google.com`).
- **`robots.txt`** under a subpath is advisory only (crawlers read `iitrpr.ac.in/robots.txt`). The `noindex` meta tag is what keeps preview builds out of search engines.
- **Zeitgeist:** this repository changes nothing in the Zeitgeist site. Its exposed `.git`, `server.py` and database are a separate issue to report to the seniors (see `project-context.md`). Keep this repository private, since its planning notes describe that issue.
