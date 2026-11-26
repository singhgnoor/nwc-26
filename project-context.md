# Samarasyam 2026 (3rd National Well-being Conclave) Portal: project context

> **ROOT DECISION, 17 Nov 2026 (from the Office of the Union Education Minister). The Ministry's version is final and overrides anything else in this project.**
> - **Name:** समरस्यम् 2026 (exactly this spelling, no apostrophe) · Samarasyam 2026 · 3rd National Well-being Conclave
> - **Tagline:** स्वस्थ मन | समरस समाज | सशक्त राष्ट्र. Devanagari only; there will be **no English version**.
> - **Theme:** Mental Wellness, Social Harmony and Collective Development
> - **Spelling:** "Well-being" / "well-being" (with the hyphen) in all our text and on the page. Ministry sentences quoted on the page keep their words; only "wellbeing" is normalised to "well-being".
> - **Kept as they are:** the hashtag #NationalWellbeingConclave (as published by MoE), the URL slug `national-wellbeing-conclave-2026` (already final), proper names (e.g. Snehita Wellbeing Cell), and verbatim transcriptions of sources in `research-brief.md` (marked as such).

> **DECISION, 17 Nov 2026 (Gurnoor): the portal shows each session's BRIEF only, not the expected outcomes.**
> - Every session card on the portal shows the **Brief** from the Dean's office Session Briefs doc (V1, 15 Nov), copied **word for word**. The only changes are the two the root decision requires: "wellbeing" → "well-being", and समरस्यम् 2026 without the apostrophe.
> - The **expected outcomes are not shown** on the portal. They stay in `content-tracker.md` for reference only.
> - All session content on the portal (titles, times, speakers, designations, briefs) is copied word for word from the Dean's office docs (V5 programme, V1 briefs) as recorded in `content-tracker.md`. **No content from any other source.**

Everything decided and discovered so far (created 16 Nov 2026, updated 17 Nov). The design prompt, the build and the CLAUDE.md should all start from this file. Research details live in `research-brief.md`; the live list of content and decisions is `content-tracker.md`.

---

## 1. The project in one paragraph
IIT Ropar is hosting **समरस्यम् 2026 (Samarasyam 2026), the 3rd National Well-being Conclave**, on **6–7 December 2026**, organised with the **Department of Higher Education (DoHE), Ministry of Education (MoE), Government of India**, under the **Malaviya Mission Teacher Training Programme (MMTTP)**. Gurnoor Singh (B.Tech CSE, IIT Ropar) has been handed the job of building the conclave's web portal. The Dean wants the link in the invitation mail he sends on **21 November 2026**. Attendees include the Union Education Minister, senior MoE officials, and well-being coordinators of IITs, NITs, IIITs, IIMs and state and national institutions. It's high stakes and has to be national-level quality.

## 2. Key facts
| Item | Value |
|---|---|
| Official name | **समरस्यम् 2026 · Samarasyam 2026 · 3rd National Well-being Conclave** (Ministry's spelling: "Well-being", not "Wellbeing" or "Wellness") |
| Tagline | **स्वस्थ मन \| समरस समाज \| सशक्त राष्ट्र** (Ministry). Devanagari only, no English version |
| Official theme | **"Mental Wellness, Social Harmony and Collective Development"** (Ministry header block). Replaces the earlier save-the-date line "Beyond Awareness: Institutionalising Mental Health, Resilience and Well-being in Higher Education" |
| MoE campaign line | "From awareness to action" (MoE 13 Nov post caption). Used as the About heading, not as the tagline |
| Dates | 6–7 December 2026 |
| Venue | IIT Ropar, Rupnagar, Punjab |
| Organisers | DoHE, MoE, GoI, with IIT Ropar, under MMTTP |
| Hashtag | #NationalWellbeingConclave (as published by MoE) |
| Target URL | **`iitrpr.ac.in/national-wellbeing-conclave-2026`** (final; slug unchanged) |
| Languages | English page with the Ministry's Devanagari name and tagline. **A full Hindi version is an open question** for the panel (see §5) |
| Session content | **Brief only** for every session (verbatim from the V1 Session Briefs); **no expected outcomes** on the portal (decided 17 Nov) |
| Hard deadline | Live and stable **before 21 Nov 2026** (invite mail) |
| Event-time use | Live schedule 6–7 Dec; photos and feedback after |

## 3. Who asked for what (the Dean and his panel)
- **Bad references:** the previous editions' pages are near-empty and "bakwas". Don't repeat them.
  - 1st, IIT Hyderabad 2024: https://mmc.ugc.ac.in/Home/Conclave2024 is four paragraphs written afterwards. No speakers, schedule, contacts or photos, broken nav, wrong copyright year.
  - 2nd, IIT Bombay 2025: https://acr.iitbombay.org/2nd-national-wellbeing-conclave-2025/ is a news post buried on the alumni/donor site. No dates, only Day 1 speakers, one image, the compendium mentioned but not linked.
- **Good reference (content only):** IIT Jammu's Aarohan, https://iitjammu.ac.in/aarohan2026/. It has:
  - its own identity: Hindi name (आरोहण), tagline "Journey towards Well-being", motto "Learn • Share • Connect • Act"
  - a summary strip (dates, venue, motto) and a theme for each day
  - a full timed schedule: every session with time, tag, title, named moderator and panellists with affiliations
  - human sessions (hostel visit, Director's dinner)
  - post-event photo albums, and a feedback form + QR poster
  - a passcode-protected editor that exports `content.json`, so the schedule updates without a developer
  - Gaps: no registration, travel, accommodation, contacts, FAQs or venue address.
- **Style instruction:** national-level, high stakes, and **must not look like a corporate website**.
- **Specific features asked for:**
  1. **Schedule with expandable sessions.** Hover (desktop) or tap (mobile) on a talk or panel to expand it and see the **speakers/panellists with photos** and details.
  2. **Event photos.** "Coming soon" for now, later a **hand-picked carousel** (not just a Drive link like Jammu's).
  3. **Feedback Google Form** section (required).
- **17 Nov feedback from the Dean (applied in design v2):** verify every Ministry line against its source (verification doc: https://claude.ai/artifact/6TpL5AL7Je1qN5Wn99cbLB); use the Ministry's name and tagline; add the four IIT Ropar gate pillars to the hero; "Key speakers" → "Speakers"; remove the "Getting to IIT Ropar" section.
- **17 Nov (Gurnoor):** each session shows its **brief only**, not the expected outcomes; all session content is copied word for word from the Dean's office docs.

## 4. What we know about the conclave (summary)
Full details and sources: `research-brief.md`.
- **MoE launch carousel (13 Nov 2026, X + Instagram)** sets the public narrative (spelling normalised to "well-being" here):
  - "Mental well-being is a national priority. The Department of Higher Education is bringing together institutional leaders, faculty and students to drive collective action towards building resilient, inclusive and well-being-oriented higher education campuses."
  - "Together, let's create safe and inclusive campuses where every individual feels supported, belongs and thrives!" / "Student Well-being First: Empowering Minds, Transforming Lives."
  - **From Conversation to Movement.** The Integrated Approach to Promoting Positive Mental Health, launched under MMTTP, has built momentum since May 2024: **54+** online capacity-building sessions, **3,800+** faculty, **160+** HEIs. 1st Conclave, Nov 2024, IIT Hyderabad: **350+ participants, 98 HEIs**. 2nd Conclave, Nov 2025, IIT Bombay: **77 HEIs, 300 participants**, student-led talk shows, nukkad nataks, Compendium of Emerging Practices. **5 regional Teacher Connect workshops** (IIT Madras, Indore, Guwahati, Bhubaneswar, Jammu): **450+ participants, 129 HEIs**.
  - **Who benefits.** Students: a safe, inclusive, stigma-free environment with counselling and peer support. Faculty & staff: training as compassionate first-line mentors. Institutions: standardised frameworks aligned with **Supreme Court guidelines** and the **University/Institution Wellness Indicators Checklist (UWIC)**.
  - **Use the MoE's numbers on the portal.** Press figures differ slightly.
- **Programme (17 Nov):** the Dean's office sent the tentative programme (V5, 16 Nov) and session briefs (V1, 15 Nov). Full detail in `content-tracker.md`. **The portal uses each session's brief only; the expected outcomes are not shown.**
- **Series format:** inaugural session with the Secretary (HE), symposia, panels, a wellness exhibition of institutional stalls, a compendium release, student workshops (nukkad natak, role-play), faculty workshops, valedictory with recommendations and an action plan. 2025 added a walkathon.
- **Recurring people:** Smt. Rina Sonowal Kouli (JS, HE), Dr. Jitendra Nagpal (Expressions India, the resource partner), Shri Devendra Kumar Sharma (Director, DoHE), Prof. Manoj Singh Gaur (Director, IIT Jammu). Past chief guests were Secretaries (HE): K. Sanjay Murthy (2024) and Dr. Vineet Joshi (2025).
- **IIT Ropar context:** Snehita Wellbeing Cell (Student Affairs); Center for Yogic Sciences and Holistic Development (groundbreaking Jan 2026).

## 5. Portal content plan (agreed direction; final structure is in `design-v1.md`)
The portal covers the whole event: **before** (invitation-ready by 21 Nov), **during** (live schedule) and **after** (photos, feedback, outcomes).

1. Header: logo row (MMTTP · GoI emblem + MoE DoHE · IIT Ropar seal), anchor nav (space reserved for an EN | हिन्दी toggle in case Hindi is approved)
2. Hero: समरस्यम् 2026 / Samarasyam 2026 / 3rd National Well-being Conclave, the Ministry tagline, the theme, dates and venue, CTA (View programme), the IIT Ropar gate pillars in the landscape
3. About: "From awareness to action" + the MoE statement
4. Who benefits: students / faculty & staff / institutions
5. **Programme:** Day 1 / Day 2; expandable session cards (speakers, moderators, photos, affiliations, and the **session brief, verbatim; no expected outcomes**); breaks as quiet rows
6. Dignitaries / speakers grid
7. The journey: Hyderabad 2024 → Bombay 2025 → regional workshops → Ropar 2026, with MoE stats
8. Moments: photos ("coming soon" → hand-picked carousel)
9. Feedback: Google Form
10. Contact / organisers
11. Footer: organiser line, campus emergency/medical numbers, logos

"Plan your visit / Getting to IIT Ropar" was **removed** on the Dean's instruction (17 Nov).

Later possibilities (not committed): compendium/outcomes download after the event, QR feedback poster like Jammu's.

### Hindi version (OPEN QUESTION, not decided)
- **Not a requirement.** Gurnoor likes the idea and will check with the panel. Until they answer, build English only (with the Ministry's Devanagari name and tagline), but keep everything Hindi-ready so adding it later is a content job, not a redesign:
  - fonts chosen as Latin + Devanagari pairs
  - no text baked into images
  - layouts with room for longer text
  - content kept in a JSON file, so a Hindi copy is a second file of the same shape
- Why it might be worth it: most invitees are government officials, and a Ministry of Education event looks right with a Hindi version.

**If the panel says yes, the plan is:**
- **Its own address:** English at `/national-wellbeing-conclave-2026/` and Hindi at `/national-wellbeing-conclave-2026/hi/`, so the Hindi page can be linked and shared directly. The header toggle switches between the same section in each language.
- **The same layout and content in both;** only the text changes. The design has to hold up with Devanagari, which runs longer and needs more line height.
- **Translation must be vetted, not machine output.** Use the Ministry's official Hindi terms (e.g. शिक्षा मंत्रालय, उच्चतर शिक्षा विभाग, Malaviya Mission's official Hindi name). The Hindi name is settled (समरस्यम् 2026); get the **official Hindi wording of the theme** from the Dean's office or MoE rather than translating it ourselves. Have IIT Ropar's Hindi cell (Rajbhasha) review it. People's names and designations need correct Hindi spellings.
- **Priority if time runs short:** hero, about and programme in Hindi by 21 Nov; the rest follows. Never leave a half-English Hindi page live.

## 6. Design direction (agreed constraints)
- Not corporate: warm, human and dignified.
- **Match the MoE campaign palette** so the portal reads as its official home: cream/off-white, coral-red → orange headings, deep navy, mustard highlights, teal/green accents, thin gold frame lines.
- **More refined than the posts:** no cartoon brains or clip-art.
- **Sense of place:** Sutlej river, Shivalik foothills, and the four stone-carved gate pillars of IIT Ropar. An "ascent/journey" motif suits the theme and the series story.
- **Readable for senior readers:** large type, WCAG AA contrast, mobile-first (the link opens from email on phones).
- Fonts from Google Fonts, chosen as **Latin + Devanagari pairs** (Eczar, Mukta, Tiro Devanagari Hindi), so the Ministry's Devanagari name and tagline render properly and a Hindi version could be added later.
- National emblem used unaltered.
- **Design tool:** Figma (via the Figma connector). File and decisions: `design-v1.md`. Frames: Desktop 1440 and Mobile 390, plus component states.

## 7. Tech and hosting decisions
### How the fest site (Zeitgeist) is hosted (Gurnoor's investigation)
- `iitrpr.ac.in/zeitgeist/` → **nginx** (IIT Ropar web server) → **reverse proxy** → a **Python `server.py`** on a college machine (likely `git clone` + `python3 server.py` on a port, default 8000). IT added roughly `location /zeitgeist/ { proxy_pass http://127.0.0.1:8000; }`.
- Evidence: `Server: nginx` on every response; no ETag on /zeitgeist/ pages; Python http.server's own 404 page; the `/zeitgeist/api/leaderboard` JSON is live; server.py strips the path prefix in `do_GET` only, so HEAD returns 404; `/zeitgeist/.git/HEAD` is downloadable.
- `vercel.json` is unused in production, so cleanUrls and security headers don't apply (`/events` 404s, `/events.html` works).

### Decision: same route, safer setup
- **Use the same nginx → reverse proxy → small process on a college machine route.** The seniors and IT have done it before, and the timeline is too short to learn a new path.
- **The site itself is static.** No logins, no database, no API. Content (schedule, speakers, photos, links) lives in **one JSON file**, so speaker changes after 21 Nov are content edits, not code edits.
- **Our own small Python server (about 50 lines, standard library only)** that:
  - serves **only a built `site/` folder**, never the repo root, so `.git`, scripts and data can't be reached
  - strips our URL prefix and handles **GET and HEAD**
  - supports clean URLs (`/schedule` → `schedule.html`)
  - shows a proper 404 page and adds basic security headers
  - refuses any path outside `site/`
- **No secrets and no database on the machine.** Feedback goes through Google Forms, and photos are static images.
- **Reliability (the bigger risk for this audience):**
  - run as a **service** (systemd, or at least cron `@reboot`) so it survives reboots
  - add a free **uptime monitor** (e.g. UptimeRobot)
  - keep a **ready-to-go mirror** on GitHub Pages or Vercel (same files)
- Framework: plain HTML/CSS/JS or a small static generator (e.g. Astro). Decide at build time; the output is a static folder either way. All paths must be **relative** so it works under the subpath.

### To ask the seniors / IT
1. Which machine? Can we get **our own port, folder and preferably our own user**, separate from Zeitgeist?
2. A new nginx `location` block for `/national-wellbeing-conclave-2026/` (it would also cover a `/hi/` version if Hindi is approved).
3. How do updates go out: `git pull` or file copy? Either is fine if only `site/` is served.

### Separate issue found: the Zeitgeist site is leaking (report to the seniors)
Anyone can download `server.py` (hardcoded admin emails and passwords), `zeitgeist.db` (users with **plain-text passwords**), `.git/`, and internal JSON and scripts. Gurnoor only confirmed these are reachable; he didn't open them. Minimum fix: rotate the admin passwords (they're also in the public GitHub repo), block `.git`, `*.db`, `*.py` and `*.json` in nginx or serve only a public folder with the DB outside it, and hash stored passwords. Gurnoor hasn't changed any Zeitgeist code.

## 8. Draft content data model (for design placeholders and the build)
One file, `content.en.json`. If Hindi is approved, add `content.hi.json` with the same shape: speaker photos and IDs are shared, only the text differs, and a small check at build time flags any key missing from the Hindi file.
```json
{
  "event": { "name": "3rd National Well-being Conclave", "nameDevanagari": "समरस्यम् 2026", "nameLatin": "Samarasyam 2026",
             "tagline": "स्वस्थ मन | समरस समाज | सशक्त राष्ट्र",
             "theme": "Mental Wellness, Social Harmony and Collective Development",
             "dates": "", "venue": "", "slug": "national-wellbeing-conclave-2026" },
  "days": [
    { "label": "Day 1", "date": "2026-12-06", "theme": "",
      "sessions": [
        { "start": "09:30", "end": "10:30", "type": "Inaugural|Keynote|Panel|Workshop|Exhibition|Cultural|Valedictory|Break",
          "title": "", "description": "", "venue": "",
          "moderator": "speakerId",
          "speakers": ["speakerId"] }
      ] }
  ],
  "speakers": { "speakerId": { "name": "", "designation": "", "institution": "", "photo": "", "bio": "" } },
  "dignitaries": ["speakerId"],
  "photos": { "status": "coming-soon|live", "items": [{ "src": "", "caption": "" }] },
  "feedback": { "status": "closed|open", "formUrl": "" },
  "contacts": [{ "role": "", "name": "", "email": "", "phone": "" }]
}
```
(The `visit` block was dropped with the Plan your visit section on 17 Nov.)
- **`description` = the session's Brief from the V1 Session Briefs, word for word** (only "wellbeing" → "well-being" and the name without the apostrophe). There is **no field for expected outcomes**; they are not published (decided 17 Nov).

## 9. Proposed timeline (to 21 Nov)
| Date | Work |
|---|---|
| Mon 16 Nov | Research done; hosting decided; Figma design started |
| Tue 17 Nov | Dean's feedback applied (design v2); Ministry name/tagline/theme final; programme V5 and session briefs received; collect logos and speaker photos; talk to seniors/IT about the machine, port and nginx block |
| Wed 18 – Thu 19 Nov | Build the static site + content JSON + small server; fill in real content (if Hindi is approved by then, send English copy for translation and Rajbhasha review as early as possible) |
| Fri 20 Nov | Deploy behind nginx as a service; uptime monitor; mirror; test on phones and desktop; Dean's final look |
| Sat 21 Nov | Invitation mail goes out with the link |
| 21 Nov – 5 Dec | Content updates (speakers, contacts) |
| 6–7 Dec | Event: live schedule |
| After | Photos carousel, feedback form open, outcomes |

## 10. Open items / waiting on
- [x] **Slug** final: `national-wellbeing-conclave-2026`
- [x] **Name, tagline, theme and spelling** final (17 Nov, Minister's office): समरस्यम् 2026 · Samarasyam 2026 · 3rd National Well-being Conclave · स्वस्थ मन | समरस समाज | सशक्त राष्ट्र (no English version) · Mental Wellness, Social Harmony and Collective Development · "Well-being" everywhere
- [x] **Schedule** received (V5, tentative, 16 Nov); details and open questions in `content-tracker.md`
- [x] **Session content on the portal:** brief only, verbatim; no expected outcomes (17 Nov, Gurnoor)
- [ ] Speaker photos and short bios
- [ ] Logos: MMTTP, GoI emblem / MoE DoHE lockup, IIT Ropar seal (confirm the round seal in the MoE posts is IIT Ropar's)
- [ ] Chief Guest and dignitaries (top two are TBC; don't publish before confirmation)
- [ ] Day themes (none in the Dean's office docs)
- [ ] Campus emergency numbers and organiser contacts (received 17 Nov; see `content-tracker.md`)
- [ ] Feedback Google Form URL
- [ ] UWIC checklist (does the Dean's office have it? no public copy found)
- [ ] **Open question, not a decision: full Hindi version?** Not a requirement. Gurnoor will check with the panel (see §5)
- [ ] *Only if Hindi is approved:* official Hindi wording of the theme, who translates, and Rajbhasha (Hindi cell) review before going live
- [ ] Hosting: machine, port, nginx block, update method (seniors/IT)

## 11. Working agreement
- **Design and plan together first; nothing is built or changed in the codebase until Gurnoor approves the plan.**
- Gurnoor is the point of contact with the Dean's office, the seniors and IT.
- Treat everything public-facing as going to the Minister's office: exact official wording, correct names and designations, no placeholder text left in production. The Ministry's version always wins (see the root decision at the top).
- **Session content is copied word for word from the Dean's office docs; nothing from other sources** (17 Nov).
