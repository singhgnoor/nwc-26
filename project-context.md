# National Wellbeing Conclave 2026 Portal: project context

Everything decided and discovered so far (as of 16 Nov 2026). The design prompt, the build and the CLAUDE.md should all start from this file. Research details live in `research-brief.md`.

---

## 1. The project in one paragraph
IIT Ropar is hosting the **3rd National Wellbeing Conclave** on **6–7 December 2026**, organised with the **Department of Higher Education (DoHE), Ministry of Education (MoE), Government of India**, under the **Malaviya Mission Teacher Training Programme (MMTTP)**. Gurnoor Singh (B.Tech CSE, IIT Ropar) has been handed the job of building the conclave's web portal. The Dean wants the link in the invitation mail he sends on **21 November 2026**. Attendees include the Union Education Minister, senior MoE officials, and wellness coordinators of IITs, NITs, IIITs, IIMs and state and national institutions. It's high stakes and has to be national-level quality.

## 2. Key facts
| Item | Value |
|---|---|
| Official name | **3rd National Wellbeing Conclave** ("Wellbeing", not "Wellness") |
| Dates | 6–7 December 2026 |
| Venue | IIT Ropar, Rupnagar, Punjab |
| Organisers | DoHE, MoE, GoI, with IIT Ropar, under MMTTP |
| Official theme | "Beyond Awareness: Institutionalising Mental Health, Resilience and Wellbeing in Higher Education" |
| Tagline | "From awareness to action" (MoE's own post caption) |
| Hashtag | #NationalWellbeingConclave |
| Target URL | **`iitrpr.ac.in/national-wellbeing-conclave-2026`** (final; replaces the earlier `nation-wellness-conclave-2026`) |
| Languages | English. **Hindi version is an open question** for the panel, not a decision (see §5) |
| Hard deadline | Live and stable **before 21 Nov 2026** (invite mail) |
| Event-time use | Live schedule 6–7 Dec; photos and feedback after |

## 3. Who asked for what (the Dean and his panel)
- **Bad references:** the previous editions' pages are near-empty and "bakwas". Don't repeat them.
  - 1st, IIT Hyderabad 2024: https://mmc.ugc.ac.in/Home/Conclave2024 is four paragraphs written afterwards. No speakers, schedule, contacts or photos, broken nav, wrong copyright year.
  - 2nd, IIT Bombay 2025: https://acr.iitbombay.org/2nd-national-wellbeing-conclave-2025/ is a news post buried on the alumni/donor site. No dates, only Day 1 speakers, one image, the compendium mentioned but not linked.
- **Good reference (content only):** IIT Jammu's Aarohan, https://iitjammu.ac.in/aarohan2026/. It has:
  - its own identity: Hindi name (आरोहण), tagline "Journey towards Wellbeing", motto "Learn • Share • Connect • Act"
  - a summary strip (dates, venue, motto) and a theme for each day
  - a full timed schedule: every session with time, tag, title, named moderator and panellists with affiliations
  - human sessions (hostel visit, Director's dinner)
  - post-event photo albums, and a feedback form + QR poster
  - a passcode-protected editor that exports `content.json`, so the schedule updates without a developer
  - Gaps: no registration, travel, accommodation, contacts, FAQs or venue address. Ours needs these because it goes out in an invitation.
- **Style instruction:** national-level, high stakes, and **must not look like a corporate website**.
- **Specific features asked for:**
  1. **Schedule with expandable sessions.** Hover (desktop) or tap (mobile) on a talk or panel to expand it and see the **speakers/panellists with photos** and details.
  2. **Event photos.** "Coming soon" for now, later a **hand-picked carousel** (not just a Drive link like Jammu's).
  3. **Feedback Google Form** section (required).

## 4. What we know about the conclave (summary)
Full details and sources: `research-brief.md`.
- **MoE launch carousel (13–14 Nov 2026, X + Instagram)** sets the official narrative:
  - "Mental wellbeing is a national priority. The Department of Higher Education is bringing together institutional leaders, faculty and students to drive collective action towards building resilient, inclusive and wellbeing-oriented higher education campuses."
  - "Together, let's create safe and inclusive campuses where every individual feels supported, belongs and thrives!" / "Student Wellbeing First: Empowering Minds, Transforming Lives."
  - **From Conversation to Movement.** The Integrated Approach to Promoting Positive Mental Health launched under MMTTP in May 2024: **54+** online capacity-building sessions, **3,800+** faculty, **160+** HEIs. 1st Conclave, Nov 2024, IIT Hyderabad: **350+ participants, 98 HEIs**. 2nd Conclave, Nov 2025, IIT Bombay: **77 HEIs, 300 participants**, student-led talk shows, nukkad nataks, Compendium of Emerging Practices. **5 regional Teacher Connect workshops** (IIT Madras, Indore, Guwahati, Bhubaneswar, Jammu): **450+ participants, 129 HEIs**.
  - **Who benefits.** Students: a safe, inclusive, stigma-free environment with counselling and peer support. Faculty & staff: training as compassionate first-line mentors. Institutions: standardised frameworks aligned with **Supreme Court guidelines** and the **University/Institution Wellness Indicators Checklist (UWIC)**.
  - **Use the MoE's numbers on the portal.** Press figures differ slightly.
- **Series format:** inaugural session with the Secretary (HE), symposia, panels, a wellness exhibition of institutional stalls, a compendium release, student workshops (nukkad natak, role-play), faculty workshops, valedictory with recommendations and an action plan. 2025 added a walkathon.
- **Recurring people:** Smt. Rina Sonowal Kouli (JS, HE), Dr. Jitendra Nagpal (Expressions India, the resource partner), Shri Devendra Kumar Sharma (Director, DoHE), Prof. Manoj Singh Gaur (Director, IIT Jammu). Past chief guests were Secretaries (HE): K. Sanjay Murthy (2024) and Dr. Vineet Joshi (2025).
- **IIT Ropar context:** Snehita Wellbeing Cell (Student Affairs); Center for Yogic Sciences and Holistic Development (groundbreaking Jan 2026).

## 5. Portal content plan (agreed direction; final structure is approved in the design step)
The portal covers the whole event: **before** (invitation-ready by 21 Nov), **during** (live schedule) and **after** (photos, feedback, outcomes).

1. Header: logo row (MMTTP · GoI emblem + MoE DoHE · IIT Ropar seal), anchor nav (space reserved for an EN | हिन्दी toggle in case Hindi is approved)
2. Hero: name, theme, tagline, dates and venue, CTAs (View programme, Plan your visit), optional countdown
3. About: the MoE statement
4. The journey: Hyderabad 2024 → Bombay 2025 → regional workshops → Ropar 2026, with MoE stats
5. Who benefits: students / faculty & staff / institutions
6. **Programme:** Day 1 / Day 2 with day themes; expandable session cards (speakers, moderators, photos, affiliations, description); breaks as quiet rows
7. Dignitaries / speakers grid
8. Plan your visit: venue, travel, accommodation, campus map, helpdesk
9. Moments: photos ("coming soon" → hand-picked carousel)
10. Feedback: Google Form
11. Contact / organisers (including Snehita)
12. Footer: organiser line, campus emergency/medical numbers, logos

Later possibilities (not committed): compendium/outcomes download after the event, QR feedback poster like Jammu's.

### Hindi version (OPEN QUESTION, not decided)
- **Not a requirement.** Gurnoor likes the idea and will check with the panel. Until they answer, build English only, but keep everything Hindi-ready so adding it later is a content job, not a redesign:
  - fonts chosen as Latin + Devanagari pairs
  - no text baked into images
  - layouts with room for longer text
  - content kept in a JSON file, so a Hindi copy is a second file of the same shape
- Why it might be worth it: most invitees are government officials, and a Ministry of Education event looks right with a Hindi version.

**If the panel says yes, the plan is:**
- **Its own address:** English at `/national-wellbeing-conclave-2026/` and Hindi at `/national-wellbeing-conclave-2026/hi/`, so the Hindi page can be linked and shared directly. The header toggle switches between the same section in each language.
- **The same layout and content in both;** only the text changes. The design has to hold up with Devanagari, which runs longer and needs more line height.
- **Translation must be vetted, not machine output.** Use the Ministry's official Hindi terms (e.g. शिक्षा मंत्रालय, उच्चतर शिक्षा विभाग, Malaviya Mission's official Hindi name). Get the **official Hindi name of the conclave and the theme** from the Dean's office or MoE rather than translating them ourselves. Have IIT Ropar's Hindi cell (Rajbhasha) review it. People's names and designations need correct Hindi spellings.
- **Priority if time runs short:** hero, about, programme and plan-your-visit in Hindi by 21 Nov; the rest follows. Never leave a half-English Hindi page live.

## 6. Design direction (agreed constraints)
- Not corporate: warm, human and dignified.
- **Match the MoE campaign palette** so the portal reads as its official home: cream/off-white, coral-red → orange headings, deep navy, mustard highlights, teal/green accents, thin gold frame lines.
- **More refined than the posts:** no cartoon brains or clip-art.
- **Sense of place:** Sutlej river, Shivalik foothills. An "ascent/journey" motif suits the theme and the series story.
- **Readable for senior readers:** large type, WCAG AA contrast, mobile-first (the link opens from email on phones).
- Fonts from Google Fonts, chosen as **Latin + Devanagari pairs** (e.g. the Noto Sans/Serif Devanagari family, Mukta, Hind, Tiro Devanagari Hindi), so a Hindi version could be added later without changing the design (Hindi is still an open question).
- National emblem used unaltered.
- **Design tool:** Figma (via the Figma connector), in a separate chat. Prompt: `figma-design-prompt.md`. Frames: Desktop 1440 and Mobile 390, plus component states.

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
  "event": { "name": "", "theme": "", "tagline": "", "dates": "", "venue": "", "slug": "" },
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
  "visit": { "address": "", "air": "", "rail": "", "road": "", "accommodation": "", "mapUrl": "", "helpdesk": "" },
  "photos": { "status": "coming-soon|live", "items": [{ "src": "", "caption": "" }] },
  "feedback": { "status": "closed|open", "formUrl": "" },
  "contacts": [{ "role": "", "name": "", "email": "", "phone": "" }]
}
```

## 9. Proposed timeline (to 21 Nov)
| Date | Work |
|---|---|
| Mon 16 Nov | Research done; hosting decided; Figma design started; schedule arrives from the Dean's office |
| Tue 17 Nov | Design reviewed and approved (Gurnoor, then the Dean if needed); collect logos and speaker photos; talk to seniors/IT about the machine, port and nginx block |
| Wed 18 – Thu 19 Nov | Build the static site + content JSON + small server; fill in real content (if Hindi is approved by then, send English copy for translation and Rajbhasha review as early as possible) |
| Fri 20 Nov | Deploy behind nginx as a service; uptime monitor; mirror; test on phones and desktop; Dean's final look |
| Sat 21 Nov | Invitation mail goes out with the link |
| 21 Nov – 5 Dec | Content updates (speakers, travel, contacts) |
| 6–7 Dec | Event: live schedule |
| After | Photos carousel, feedback form open, outcomes |

## 10. Open items / waiting on
- [x] **Slug and name** final: `national-wellbeing-conclave-2026`, "Wellbeing"
- [ ] **Schedule** with talks, panels, times, speakers and moderators (due 16 Nov from the Dean's office)
- [ ] Speaker photos, designations and short bios
- [ ] Logos: MMTTP, GoI emblem / MoE DoHE lockup, IIT Ropar seal (confirm the round seal in the MoE posts is IIT Ropar's)
- [ ] Chief Guest and dignitaries
- [ ] Day themes for 6 and 7 Dec
- [ ] Travel, accommodation and helpdesk details; organiser contacts; campus emergency numbers
- [ ] Feedback Google Form URL
- [ ] UWIC checklist (does the Dean's office have it? no public copy found)
- [ ] **Open question, not a decision: Hindi version?** Not a requirement. Gurnoor will check with the panel (see §5).
- [ ] *Only if Hindi is approved:* the official Hindi name of the conclave and the theme (Dean's office / MoE), who translates, and Rajbhasha (Hindi cell) review before going live
- [ ] Hosting: machine, port, nginx block, update method (seniors/IT)

## 11. Working agreement
- **Design and plan together first; nothing is built or changed in the codebase until Gurnoor approves the plan.**
- Gurnoor is the point of contact with the Dean's office, the seniors and IT.
- Treat everything public-facing as going to the Minister's office: exact official wording, correct names and designations, no placeholder text left in production.
