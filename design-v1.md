# Portal design (Figma): v1 16 Nov 2026, v2 17 Nov 2026, v3 17 Nov 2026 (real programme), v3.1 17 Nov 2026 (briefs), v3.2 26 Nov 2026 (Around IIT Ropar), v3.3 26 Nov 2026 (V6 speakers)
 
> **ROOT DECISION, 17 Nov 2026 (from the Office of the Union Education Minister). The Ministry's version is final and overrides anything else in this project.**
> - **Name:** समरस्यम् 2026 (no apostrophe) · Samarasyam 2026 · 3rd National Well-being Conclave
> - **Tagline:** स्वस्थ मन | समरस समाज | सशक्त राष्ट्र. Devanagari only, **no English version**.
> - **Theme:** Mental Wellness, Social Harmony and Collective Development
> - **Spelling:** "Well-being" (hyphen) in all page text, including Ministry sentences quoted on the page (words unchanged, spelling normalised). Hashtag #NationalWellbeingConclave and slug unchanged; Snehita Wellbeing Cell is a proper name.
 
> **DECISION, 17 Nov 2026 (Gurnoor): the portal shows each session's BRIEF only, not the expected outcomes.**
> - Every session card on the portal shows the **Brief** from the Dean's office Session Briefs doc (V1, 15 Nov), copied **word for word**. The only changes are the two the root decision requires: "wellbeing" → "well-being", and समरस्यम् 2026 without the apostrophe.
> - The **expected outcomes are not shown** on the portal. They stay in `content-tracker.md` for reference only.
> - All session content on the portal (titles, times, speakers, designations, briefs) is copied word for word from the Dean's office docs (V5 programme, V1 briefs) as recorded in `content-tracker.md`. **No content from any other source.** Applied in the Figma design as v3.1 (below).
 
Figma file: https://www.figma.com/design/84ACfsxiRu5u9j5rUMHtZa (Gurnoor approved the direction; build from this).
Verification doc (every Ministry line vs its source): https://claude.ai/artifact/6TpL5AL7Je1qN5Wn99cbLB
 
## v3.3 changes (26 Nov 2026): programme V6 speakers
Source: `V6_NWC_2026_Tentative_Programme_Schedule_18.11.2026.docx`. V6 changes only three speakers; times, titles, session numbers and notes are the same as V5. Applied on **04 Desktop 1440 (Day 1)** only (Day 2, Components and Mobile carry none of these names). Wording copied from V6. Supersedes the V5 names listed under v3.1.
- **S5 card + speaker grid slot 3:** Dr. Ram Manohar Singh → **Dr. Tony Thomas**, Assistant Professor, Department of Humanities and Social Sciences, IIT Roorkee (Verbally Confirmed).
- **S6 card + speaker grid slot 7:** Dr. Nancy Sahni is now Confirmed, so "(Awaiting confirmation)" is removed. Card line: "PGIMER, Chandigarh (Speaker on Nutrition)"; grid: "Speaker on Nutrition" / "PGIMER, Chandigarh". S6 alternates are no longer listed in V6.
- **S9 card + speaker grid slot 14:** Dr. Jyoti Mishra → **Dr. Palak Upadhyay**, Department of Clinical Psychology, Dayanand Medical College & Hospital (DMC&H), Ludhiana (Confirmed, so no status label).
- Grid frames renamed "Speaker 3 · Dr. Tony Thomas" and "Speaker 14 · Dr. Palak Upadhyay". The S5 card grew by one line; the programme column reflows (auto-layout), nothing overlaps.
- Not changed: other designations still use the short forms from the tracker (e.g. "IIM Amritsar", "TISS Mumbai", "Dept. of Neurology") where V6 spells them out.
## v3.2 changes (26 Nov 2026): "Around IIT Ropar" band (Dean's office request)
Content and build rules: `content-tracker.md` §11.
- **New band directly above the footer** (after 07 Contact) on **04 Desktop 1440**, **04b Desktop 1440 · Day 2** and **05 Mobile 390**. Frame name "Around IIT Ropar (places nearby)". Unnumbered: folio "Beyond the conclave" (phulkari star + UI/Label, madder), heading "Around IIT Ropar" (Heading/H2 on desktop, Heading/H1 (mobile) on mobile), subline "For a free hour, an afternoon, or a day after the conclave." Background paper/khaddar with a 1px line/gold top rule, so it reads as separate from Contact (khaddar-deep) and leads into the footer.
- **Route key (desktop):** the saffron running-stitch path reused as a key: IIT Ropar (phulkari star, "You are here") → Close by · under 30 min (Sutlej diamond) → Half day · 45 min – 1¼ hr (Haldi diamond) → Day trip · 1½ – 2 hr (Madder diamond).
- **Cards:** new component set **"Card / Nearby place"** on 03 Components (Group = Close by / Half day / Day trip sets the accent rule and the drive-chip wash: Sutlej / Haldi / Madder). Text properties: Title, Drive, Blurb, Note. Each card: accent rule, drive chip (road icon + "≈ 15 MIN"), title (Heading/Session), blurb (Body/S, ink/soft), note with clock icon (Body/S, indigo), hairline, and **one link: "Open in Google Maps" + external icon (madder)**. No embedded maps, no directions.
- **Desktop layout:** 8 cards in a 4 × 2 grid ordered by drive time (Harappan Site, Ropar Wetland, Anandpur Sahib, Capitol Complex / Rock Garden, Sector 17 & 22, Khatkar Kalan, Morni Hills); cards in a row share one height. Footnote: "Drive times are approximate, from the IIT Ropar main gate. Opening hours can change, so please check before you set out."
- **Mobile layout:** 16px page margin; "Swipe each row for more →" hint; one row per group (diamond + group name + range), each row a sideways-scrolling strip of 292px cards with the next card peeking; same footnote.
- **Footer:** "Around IIT Ropar" added to the on-this-page links after "Contact" (desktop Day 1, Day 2 and mobile).
## v3.1 changes (17 Nov 2026): session briefs, word-for-word content
- **Every numbered session card is shown expanded** on both desktop pages, with its **Brief** (verbatim from V1) and its people from V5. No expected outcomes anywhere.
- **Session 10** is two rows in V5 (16.00 breakaways, 16.45 presentation of stakeholder deliberations). Its brief has two paragraphs: paragraph 1 is on the 16.00 card, paragraph 2 ("Each group will then present…") on the 16.45 card. The 16.45 card has no session number, because the schedule leaves it unnumbered.
- **Cultural Programme** has no brief in V1, so it stays a plain card without an expanded section.
- **Titles are copied from the V5 table** ("Session: theme" as written there), e.g. "Panel Discussion I: Transforming social connectedness…", "Ice-breaking Session (followed by a briefing on the breakaway sessions)", "Student Presentations: Student presentations from the Life Skills Workshop". Apostrophes as in the docs.
- **Times as written in V5:** "08.30", "to 10.15", "19.00 onwards", "06.30 / 07.00".
- **People exactly as V5**, including the status where it isn't Confirmed: "(TBC)" for the Minister and the Secretary, "(Verbally Confirmed)" for Dr. Ram Manohar Singh and Dr. Jyoti Mishra, "(Awaiting confirmation)" for Dr. Nancy Sahni. Roles on the moderator chip as V5 labels them: "Moderator", "Speaker and Moderator" (Dr. Jitendra Nagpal, S6), "Vote of Thanks" (Dr. Surya Kant Sahdeo, S1; Dr. Suryasnata Tripathy, S15). Session 3 shows "Dean, Student Affairs, IIT Ropar"; Session 4 shows both names V5 gives (either/or); Session 11 shows "Clinical Psychologist from IIT Ropar or a participating institution"; Session 14 shows no people (CFIs not named). S6 alternates are not shown. *(S5, S6 and S9 people updated to V6 in v3.3.)*
- **Minister's name is "Shri Prahlad Joshi", as in V5** (the v3 "Pralhad" spelling came from outside the docs and was reverted).
- **Day tabs:** theme line hidden, because the docs give no day themes (the v3 summaries were not from the docs).
- **Footnote:** "Programme is tentative and subject to change." (tracker wording). **At-a-glance registration line:** "Registration | Welcome of Guests | Tea".
- **Dignitaries (Day 1):** eyebrow "Inaugural Ceremony"; designations carry "(TBC)" as in V5. **Speaker grid (Day 1):** statuses added as above; apostrophes as in the docs.
## v3 changes (17 Nov 2026): real programme V5 and speakers in the design
- **"04 · Desktop 1440" = Day 1 selected.** Programme rebuilt from V5 (tentative, 16 Nov): 17 rows, Registration | Welcome of Guests | Tea → Gala Dinner. Each session card shows its V5 session number in the meta slot; venue pins hidden because no venues are confirmed.
- **New page "04b · Desktop 1440 · Day 2"**: copy of the desktop frame with the Day 2 tab active and the Day 2 programme (Yoga | Campus Walk → Lunch and Networking).
- **New tag variants** on "Tag / Session type" (03 Components): Presentation, Symposium, Ice-breaker, Breakaway. Keynote is no longer used in the programme.
- **03 Dignitaries & speakers:** no "Chief Guest / Guest of Honour" labels (V5 doesn't assign them); eyebrows name the session instead.
  - Day 1: Shri Prahlad Joshi, Minister of Education, Government of India (TBC); Ms. Deepti Gaur Mukherjee, Secretary, Department of Higher Education (TBC); Prof. Rajeev Ahuja, Director, IIT Ropar. Speaker grid: 16 Day 1 resource persons in session order.
  - Day 2: Valedictory Session: Shri Devendra Kumar Sharma, Prof. Rajeev Ahuja, Dr. Jitendra Nagpal. Speaker grid: Dr. Sidharth Sood, Dr. Mayuri Duggirala, Dr. Krishan Kumar Soni, Ms. Geeta Mehrotra and Team.
- **Not yet done:** Mobile 390 still shows the sample programme and placeholder speakers. TBC / Verbally Confirmed / Awaiting names are in the design and must be held back before going live unless the Dean's office clears them (Q11 in `content-tracker.md`).
## v2 changes (17 Nov 2026, Dean's feedback)
- **Hero lockup:** "समरस्यम् 2026" (Eczar SemiBold, madder + indigo "2026"), then "Samarasyam 2026", then "3rd National Well-being Conclave", then the tagline "स्वस्थ मन | समरस समाज | सशक्त राष्ट्र" (Tiro Devanagari Hindi Regular), then the theme "Mental Wellness, Social Harmony and Collective Development", then the CTA. Nav wordmark "Samarasyam 2026". Footer, mobile menu and the Figma cover page match.
- **"From awareness to action"** (MoE 13 Nov caption) moved from the hero tagline slot to the About heading, as the full caption sentence.
- **Wording fixed to the Ministry's exact text:** About quote credit "Ministry of Education, Government of India"; all three Who-benefits cards use the full Ministry sentences; Journey intro uses "built considerable momentum since May 2024".
- **Spelling:** every "wellbeing" in page text is now "well-being" (desktop, mobile, components, foundations, frame names).
- **"Key speakers" → "Speakers".**
- **"05 Plan your visit / Getting to IIT Ropar" removed** (desktop, mobile, nav link, footer link, mobile menu). Sections renumbered: 05 Moments, 06 Feedback, 07 Contact. Venue stays in the at-a-glance strip; helpdesk number stays in the footer.
- **IIT Ropar gate pillars** in the hero, bottom-left (desktop, mobile, cover): component "Art / IIT Ropar gate pillars" on 02 Assets. Four sandstone frustums with carved Indus-seal bands and the steel wire-frame cube on top, set on a **square** (2×2) in 3/4 view: front pair low, back pair higher, smaller and offset. Each pillar has its own low stone step and a soft shadow; no shared base. They stand on the hill line where the ascent path starts.
- **07 Contact ("Who to write to") redesigned (17 Nov, applied on desktop and mobile):** the three placeholder cards (Organising office, Snehita Wellbeing Cell, DoHE) are replaced by **one panel**. On the left: gold-topped madder accent, "Organising Team", "3rd National Well-being Conclave", "Indian Institute of Technology Ropar", a line on what to write about, and **nwc@iitrpr.ac.in** in madder with the mail icon. A thin gold divider separates the two sides. On the right: the label "On behalf of the organising team", then **Dr. Surya Kant Sahdeo** (Nodal Officer, NWC 2026, +91 1881 231181) and **Dr. Suryasnata Tripathy** (Coordinator, NWC 2026, +91 1881 232505) as rows separated by a gold hairline, with the phone numbers aligned right. Mobile stacks it all in one card (email block, gold rule, label, then the two people). The intro copy now reads "…the organising team at IIT Ropar is your first point of contact." **Snehita and the DoHE card are gone.**
- **Footer "On campus, if you need help" (17 Nov, desktop and mobile):** Medical Centre (24×7) +91 1881 235193 · Ambulance (24×7) +91 90410 53926 (Medical Centre mobile) · Campus Security +91 1881 235901 (Main Gate) · Tele-MANAS counselling (24×7) 1800 89 14416 · Conclave Helpdesk **+91 00000 00000 (placeholder, number still needed)**.
## Pages
00 Cover · 01 Foundations (variables + type) · 02 Assets (logos, landscape, pillars, motifs, icons, placeholders, all components) · 03 Components (incl. Card / Nearby place) · 04 Desktop 1440 (Day 1 selected; + state frames: Moments carousel, Feedback open) · 04b Desktop 1440 · Day 2 · 05 Mobile 390 (+ menu-open state)
 
## Direction: "Khaddar & Phulkari"
- Palette from Punjab's phulkari + place, in the MoE campaign family: khaddar #F6EFE2 / deep #EDE2CC / card #FFFBF3; indigo #1E2A44, soft #4A5672; madder #B23A2B (headings, primary); saffron #DC7A2C (stitch only, not text); haldi #E8B44A (highlights on indigo); gold line #B88A3B; Sutlej teal #1F6B66; Shivalik green #5E7F55; washes for tags. Pillars use sandstone tints between haldi and khaddar.
- Signature: a saffron running-stitch "ascent" path. Hero landscape (Shivalik foothills, Sutlej, sun) starts at the gate pillars on the left and climbs past Hyderabad, Bombay and the regional workshops to a phulkari star summit (Ropar). Reused as the programme timeline thread, the Journey ascent profile and the Around IIT Ropar route key.
- Type (Google Fonts): Eczar (headings, incl. the Devanagari name), Mukta (body/UI), Tiro Devanagari Hindi (tagline/accents), Mukta Mahee (Gurmukhi, footer). All Devanagari-capable.
- No gradients, glassmorphism or stock photos. Landscape and pillars are flat SVG.
## Decisions made with Gurnoor
- Attendees are confirmed, not invited: hero eyebrow "Welcome to IIT Ropar"; only one hero CTA ("View programme"); "Plan your arrival" removed.
- Desktop session cards: hover previews (gold border, fanned avatars, "View speakers"), click expands. Mobile: tap expands.
- **Expanded session = brief (verbatim) + moderator + speakers. No expected outcomes** (17 Nov).
- Formal footer modelled on iitrpr.ac.in: organiser logo strip on light ground (emblem never recoloured), phulkari band, conclave identity (Samarasyam 2026, Devanagari name line, tagline, theme), on-this-page links, campus emergency numbers, IIT Ropar seal with Punjabi/Hindi/English name, address, socials, iitrpr.ac.in, "© 2026 Indian Institute of Technology Ropar" and "Designed and developed by SAC Team".
- Contact section lists the organising team only (no Snehita, no DoHE card).
- **Around IIT Ropar (26 Nov):** slim unnumbered band above the footer; places grouped by drive time; each card has only a Google Maps link (no embedded map, no directions).
## Section order (v3.2)
Header (band, logos, sticky nav with optional EN|हिन्दी) · Hero · At-a-glance strip (dates, venue, registration, countdown) · 01 Why this conclave + Who benefits · 02 Programme · 03 Dignitaries & speakers · 04 Journey (From Conversation to Movement, MoE stats) · 05 Moments · 06 Feedback · 07 Contact · Around IIT Ropar (unnumbered) · Footer
 
## Still placeholder (needs real content)
Logos (MMTTP, GoI emblem + MoE/DoHE lockup, IIT Ropar seal incl. white version), venues, Conclave Helpdesk number (footer), speaker photos and bios, social links, Google Form URL, Mobile 390 programme and speakers, verified drive times and Google Maps links for the Around IIT Ropar cards.