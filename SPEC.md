# College App App - Context & Specification

## Summary

The College App App is an open-source Django web application that replaces the cobbled-together workflow of spreadsheets, Google Docs, and application portals with an integrated platform for managing college applications. Built by Jacob Cohen (originally conceived in a [blog post](https://beautifulthorns.wixsite.com/home/post/college-app-app)), it stores everything in one place with purpose-built views: a college list manager, activities/honors editors for UC, Common App, and MIT formats (with proper character/word limits and cross-format linking via an "Activity Hub"), and a supplemental essay tracker. The tech stack is Django 5.x + SQLite + Bulma CSS + htmx + Alpine.js, requiring no build step — just `python manage.py runserver`.

---

## Implementation Plan

### Technology Stack

- **Backend**: Django 5.x, Python 3.12+, SQLite
- **Interactivity**: htmx (server-driven reactivity), Alpine.js (client-side character counters, toggles)
- **Styling**: Bulma CSS v1 via CDN (no build step, rich color helpers for conditional formatting)
- **No build step required** - everything runs with `python manage.py runserver`

### Project Structure

```
college-app-app/
├── manage.py
├── requirements.txt
├── college_app/                  # Django project package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                         # Shared: base templates, static files, home page
│   ├── models.py                 # CoreActivity (the activity hub)
│   ├── views.py                  # Home/dashboard
│   ├── urls.py
│   ├── templates/
│   │   └── base.html             # Base template with nav, Bulma, htmx, Alpine
│   └── static/
│       └── css/
│           └── app.css           # Custom styles (conditional formatting colors, etc.)
├── colleges/                     # College list management
│   ├── models.py                 # College
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── management/commands/
│   │   └── import_colleges.py    # CSV import
│   └── templates/colleges/
├── activities/                   # Activities & honors (all 4 formats)
│   ├── models.py                 # UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
│   ├── views.py
│   ├── forms.py                  # Category-polymorphic forms for UC
│   ├── urls.py
│   ├── management/commands/
│   │   └── import_activities.py  # CSV import
│   └── templates/activities/
└── supplements/                  # Supplemental essays
    ├── models.py                 # EssayCategory, SupplementEssay
    ├── views.py
    ├── forms.py
    ├── urls.py
    └── templates/supplements/
```

### Data Models

#### core/models.py - The Activity Hub

```python
class CoreActivity(models.Model):
    """The 'hub' representing a real-world activity, job, or honor.
    Format-specific entries (UC, Common App, MIT) link back here.
    This lets users see one activity across all application formats."""
    name = models.CharField(max_length=300)
    full_description = models.TextField(blank=True)
    personal_notes = models.TextField(blank=True)
    order = models.IntegerField(default=0)
```

The key insight: a single activity like "NYT Puzzle Creator" appears in UC, Common App, and MIT formats with different character limits and fields. CoreActivity is the canonical source. Each format-specific entry has an **optional** FK to CoreActivity.

#### colleges/models.py

College model with 30+ fields including: name, apply_status (with choices: applying, likely, considering, unlikely, not_applying, applied, accepted, waitlisted, deferred, rejected, enrolled), tier, acceptance_rate, collegevine_chance, location, lat/lng (future map view), app_platform, terms, financial fields (cost_of_attendance, estimated_financial_aid, estimated_net_cost, financial_aid_deadline, fafsa_required, css_profile_required), deadline fields (ea, ed1, ed2, rd, other), requirements_style, restrictive_ea, self_report_sat, interview, known_students, known_faculty, intended/2nd/3rd choice major, toured, portal_info, applicant/parent/random notes, order.

#### activities/models.py

- **UCEntry** (up to 20): 6 categories (award, edu_prep, extracurricular, volunteer, work, coursework), name, background (250 chars), description (350 chars), grades 9-12, hours/week, weeks/year, recognition_level, is_academic, earnings_usage, still_working, personal_notes. Optional FK to CoreActivity.

- **CommonAppActivity** (up to 10): 27 activity types, position (50 chars), organization (100 chars), description (150 chars), grades 9-12, timing checkboxes (school/breaks/all_year), hours/week, weeks/year, similar_in_college, personal_notes. Optional FK to CoreActivity.

- **CommonAppHonor** (up to 5): title, grades 9-12, level checkboxes (school/state_regional/national/international), personal_notes. Optional FK to CoreActivity.

- **MITEntry** (category limits: 5 jobs, 4 activities, 6 summer, 5 scholastic, 5 non-scholastic): category, org_name, role_award, participation_period, hours/week, weeks/year, description (40 word limit), personal_notes. Optional FK to CoreActivity.

#### supplements/models.py

- **EssayCategory**: name, sort_order
- **SupplementEssay**: FK to College, FK to EssayCategory, prompt, word_limit, char_limit, response, status (WIP/DONE/Maybe), notes, sort_order

### Build Phases

**Phase 1: Project Scaffolding + All Models** - COMPLETE
- Django project, all 4 apps, all models, migrations, base template, CSV import commands
- Data imported: 119 colleges, 6 UC entries, 7 CA activities, 3 honors, 10 MIT entries, 18 essays

**Phase 2: College List Manager** - COMPLETE (MVP)
- Table view, color-coded rows, sort/filter, inline editing, add/delete
- Known issues: status dropdown glitchy, dates should be native pickers, color coding needs work

**Phase 3: Activities & Honors Manager** - COMPLETE (MVP)
- 4-tab interface (UC/Common App/Honors/MIT), forms with char/word counters, cross-format linking, CRUD for all formats
- Next: DATA and AESTHETICS improvements

**Phase 4: Supplementals Tracker** - DEFERRED
- Matrix view, per-college view, essay editor, category management

**Phase 5: Dashboard & Polish** - DEFERRED
- Home page progress overview, college-centric view, visual polish

### Future Feature Accommodation

| Future Feature | How Architecture Supports It |
|---|---|
| Essay cross-linking | Add SharedTextBlock model with M2M to SupplementEssay |
| Export to Common App | All Common App fields match the actual application exactly |
| Word processor / rich text | Replace response TextField with rich text widget |
| Financial aid management | New financial/ app with FK to College |
| Sharing / collaboration | Add Django auth, FK from all models to User |
| Map view | latitude/longitude fields already on College |
| Gamification | New achievements/ app querying existing models |
| Portal organizer | portal_info on College, expandable to PortalAccount model |
| Warning flags | Validation layer scanning essays for college names |
| College data scraping | College fields match public data sources (IPEDS, College Scorecard) |

---

## Original Blog Post

### The College App App & My Ultimate College App Spreadsheet [WIP Week]

*Jul 27, 2024 - by Jacob Cohen on Chromatic Conflux*

It's WIP Week on Chromatic Conflux! I searched through my metaphorical blog post vault and found seven projects that I'm proud of — but may never "finish." So I thought, why not just publish them? Yesterday's post was "Jacob's College Application FAQ."

Today's post (the grand finale) has the same topic but a different spin. In December, as I was finally finishing college apps, I had an idea for the College App App (working title): a product that would make the college app process feel less horrible.

This could be a startup idea, I realized! The motto of Y Combinator, the preeminent startup funder, is "Make something people want." This product is something people would want. I know because I would've wanted it, and many of my friends say they'd have wanted it. It could make a lot of money, although I would be horrified if it was used to make a profit (god knows the process is already pay-to-win enough); my plan was to make it open-source and accessible to all. (Although I bet you could make a lot of money off donations from Patreon!)

The problem: I don't know how to code webapps. I could fix this, I thought. I could use the College App App as a way to learn how to code webapps. I did start learning Svelte a few months ago, actually, but sadly not enough to be useful on this.

I wanted to have the product ready by June, for the Class of 2025 applicants, but ... the reality is that, coming out of college apps, I wanted a break from thinking about them. I spent most of my project energy in February working on [insert puzzle hunt party here], and once it was March, and the message of the world was that I should have senioritis and slack off, the project kind of lost momentum.

But I do have something to show!

In February, I made a spreadsheet prototype / spec for the College App App. Like with my Ravniconlang post, I packed a lot into a humble spreadsheet. But before posting, I revised the spreadsheet further to be a product I'm proud of! It contains a detailed skeleton for organizing and formatting most of what you need in a college application:

- a college list,
- a Common App activities list,
- a Common App honors list,
- a UC activities & awards list,
- an MIT jobs & activities & awards section,
- and an at-a-glance outline of supplemental essays.

You can make a copy of it, and I promise it's better than any similar, publicly available spreadsheet that anyone told me about. I swear, my friends and I all rolled our own.

But first, I want to give my original elevator pitch for the College App App: the more ambitious version of this idea. If this feels like a project you would be interested in, that would be awesome! I would be so happy if this existed.

Compared to yesterday's FAQ, I'm targeting today's post even harder at people with direct involvement in the American college app process, or people potentially interested in helping make the College App App. If this isn't you, you might be bored.

But if it is, or you're curious about the project, read on!


#### the mission

I'm Jacob, and college apps crushed my soul and chopped it into pieces.*

I think I handled it worse than many, but the college application industrial complex looms large for everyone.

I feel like there's something uniquely cruel about a world where ambitious American high school seniors are essentially forced to spend so much time advertising themselves instead of spending their time doing fun things that contribute to the world.

I want to do something to help, something that would've made it easier on me and will help future applicants. Unfortunately, a lot of the problems with college apps feel systemic and intractable.

But not all of them.

*sorry this line is a bit much but maybe it's the right kind of a bit much.


#### the problem

College apps have a lot of subtasks that require managing. And there's not a good platform that does it.

I made an Ultimate College Application Spreadsheet. Many of my friends also rolled their own spreadsheets. One friend used Scrivener and Ulysses, which are more aimed at novel writing, to track supplements, and I think that had pros and cons maybe?

My spreadsheet did a lot of things:

- Managing a list of colleges, and keeping track of many stats about them (lots of which are publicly available).
- Organizing my activities and awards according to the complicated (and varying) specifications in the Common App, UC App, and MIT App. (I didn't apply to foreign universities, CSUs, Georgetown, etc., but many people do.)
- Categorizing my supplemental essays by topic, so I could see them all at a glance.

And that's in addition to the docs where I had to copy-paste my prompts, copy-paste tons of things into wordcounter.io because Google Drive counts words differently from the Common App. (Seriously. On the application, words are just strings separated by spaces - so "puzzlesforprogress.net—my blog/site" is two words, while Google Docs considers it four. Meanwhile, a section separator like" ~ " is a word in the application but not Docs. Em-dashes, by the way, look ugly in the UC app. I spent too much time thinking about this...)

I'm lucky enough that I didn't worry that much about financial aid, but those forms are also a big deal to manage.

It required a lot of copying, figuring out what went where, headaches of managing everything.

Why did we have to make our own spreadsheets with all this information? To keep track of everything in different places, to have all these different tasks floating around?


#### the solution

The vision of the College App App is to be an integrated platform for writing and managing college apps that is actually designed to be a good interface.

Currently, there are all the writing platforms that are not specialized at all toward the needs of college apps, and the actual applications themselves which are not designed to be writing platforms (and aren't really designed to be user-friendly — CollegeVine is maybe the closest thing, but it just tackles the list management and probability assignment).

There is tons of low-hanging fruit: stuff that's not complicated technically, but could make the interface a lot nicer.

My vision is essentially for a "CRUD" (create/read/update/delete) app. It would have some sort of database that stores a bunch of user-inputted data about college, including their essays/activities/etc, and presents it in a variety of beautiful, editable views/widgets.

Example: You could transition between viewing an individual supplemental essay, all of that college's essays (as they would be formatted in the Common App!), a table of all your essays for all your colleges (or those that aren't "done"), a comparison between the original essay and a similar essay you're submitting to a different college...and be able to edit the essay in all of those views, and have the database update.


#### the mvp features

I have so many feature ideas. I can feel the scope of this project increasing.

But what has to happen for this to be superior to nothing? To form the Minimum Viable Product, or MVP?

Well, I think this spreadsheet is already the MVP of sorts (if I make it editable by anyone) but for the webapplication.

1. I think it's imperative to store the data well in order to accommodate a variety of future widgets with read/write access to the database. Therefore, I need to find a database structure. I don't have much experience with databases and would welcome suggestions from those who do.

2. A college list manager (see "College List") that has a bunch of publicly accessible data about colleges, as well as user-inputted data, and allows the user to specify which colleges they are considering applying to.

3. One of the following (ideally both, but not necessarily for the MVP):

(a) An activities/honors list manager (see "Activities" and "Honors" for Common App, "UC A&A" for UC, "MIT J&A&D" for MIT), that enforces all the word counts and stores everything in a nice table. This is an area where what's available now is pretty bad; editing this stuff in the application itself is kind of ridiculous, and Docs/Sheets doesn't have any of the requirements by default. [We're probably going to try to build this first, because we think it will be easier.]

(b) A supplement spreadsheet/manager (see "Supplementals: At A Glance"), with multiple different views like I was talking about in the example. A place to see what is being submitted to each of these colleges. It would be great if this was compatible with a word processor.


#### the nice-to-have features

- Obviously both 3a and 3b together would be good. Would be cool to have the College App App approach a complete place to see college app info: a place to rely on, to take away the mental energy of looking at everything else (this is like the Getting Things Done philosophy).
- "Export to Common App" might also be a cool feature; I think the Common App has an API, but does it actually support an operation like this?
- Ideally this would also be a word processor / writing platform. I think the "writing platform" thing is difficult, because Google Docs / Microsoft Word / etc are already quite established, and we probably won't be able to match them on features — thereby not being "strictly better." What open-source writing platforms are out there? (I guess a starting point might be something like "Manifold comment box + word counter + color highlighting + customizable font"). Could there be some way to embed Docs or something? (Could also brand as a stripped-back "focus mode.")
- A fun feature (maybe a marketable flagship feature) could be that you'd have a block of text that's embedded into multiple essays for different colleges, and if you edited it in one place, it would automatically edit in the other place. (Other sorts of supplement cross-linking would be nice.) Some kinks to work out though, since often you want to modify the block of text differently for different colleges. This could also be helpful for activities lists.
- Warning flag for common mistakes (mentioning the name of a different college in one's supplemental essay; "did you mean to apply to Cornell University instead of Cornell College," etc)
- Map view for colleges.
- Brainstorming boxes: e.g. like a notes box on each college, on each supplement, etc.
- Financial aid application management. Not an area I know a ton about but a person I was talking to about this idea thinks it's pretty important.
- Sharing functionality! Smooth for counselors / friends / other people to comment on or feedback your essays; you can choose how much of your app to share.
- Integration with cc6's Manifold x College Admissions project.
- I'm not sure if this is really a feature, but: aesthetics. I want this to look nice and inviting, a place people want to come to!
- Gamification. Perhaps different aspects of your applications are "achievements," and you get "college points" for doing different things, or something. I think this should be a setting, so it's not forced on everyone, but I think it might have helped me if college applications was just a little more like a video game. However, would have to make sure that the video game achievements are very aligned with the college app goals, or else we're just helping people waste their time. ("the a2c effect")
- Application portal organizer (suggested by Audrey). Keeping track of which portals you've made accounts for, what's in the portals, etc. With links. The Coalition App does this but not the Common App
- Managing art/music/etc portfolios (SlideRoom also does some of this apparently)
- I will think of more. I perpetually think of more.


#### the path forward

Building things is hard, and I have other ways of spending my time. But I do think this is probably a good idea that will positively impact the world?

I think it would depend on assembling a good team of people. Especially someone with experience coding similar webapps; also Class of '25 (edit: or Class of '26, or younger!) high schoolers who might use the technology. I'd also love to have people who have free time and are just enthusiastic about making this a good product, and have an aesthetic vision that's aligned with mine. Please let me know if you have any ideas!

I'd also love ideas for technologies (database, frontend, word processor) that would be good for making this a reality! Considering something like JS/React or Electron/React, but I would be learning said tool on the fly, which is a little worrying. See "Technology Options."

I think this idea could end up very financially successful if it was done well and sold at a high price point. Anxious parents will pay a lot for something that would help even a small amount toward college. But that doesn't feel right — it would only make college more pay-to-win in the long term. So I hope to make this resource open source and free. I think this means it wouldn't have negative side effects?

Anyway, I'm hoping to make some progress soon — some of February 12 will be set aside for this purpose. However, I want to figure out the right tools first.

In the other tabs, check out my spreadsheet prototype! It contains some examples, adapted from my own spreadsheet, to give a fuller picture of how this would be used in real life.

Thanks for reading!


#### Addendum

If you feel like you're the sort of person who could do this, that sounds awesome! As long as you're not planning to sell your product — if it's to publish freely, or for personal use — I'd love to hear about your efforts, and I'd be happy to help where I can.

So, no app. But what do I have?

A prototype of the College App App. My Ultimate College Application Spreadsheet!

If you're interested in it, head to tinyurl.com/jacobscollegespreadsheet and make a copy!

Let me give you a tour! First stop: tab 1, the college list.


#### Tab One: The College List

The first thing you might notice is that the spreadsheet is very colorful. Indeed, it has a ton of conditional formatting! Change "Yes" to "Maybe" and the color goes from cyan to yellow.

It's also in the default font. And it has a lot of fields which aren't filled in (and this increases as you scroll down). But ... this is WIP Week, you know. Hey, it's healthy to do your own college research! (I'm just lazy; if anyone wants to add data, let me know and I might give you edit access.)

There are also a ton of comments. Please read the comments! They help clarify some of the idiosyncratic Jacob-style choices that I made. I'll copy most of them below.

**Comments:**

- **College Name**: The colleges are organized in a deeply ad-hoc way, in rough proportion to how much I thought about them, with a few arbitrary changes thrown in to anonymize. Please reorder, rename, add details, etc!
- **Apply?**: I used the labels Yes > Probably > Maybe > Imaginably > Doubtful to indicate my likelihood of applying, because they support the Z -> A sort nicely! But if you want to be boring, you can use numbers from 5 to 1 and they have the same conditional formatting.
- **Tier**: If you'd like to give a rough ranking of the colleges in the list (which can help with sorting), here's a good place for that. I used the "1a / 1b / 1c / 2a / etc" style of tiers.
- **Acc.**: Acceptance rate. I forget which year this is from - probably 2022-23. I expected my "real chance" to be 2-4x this number, based on my background; your mileage may vary.
- **CVine**: There's a handy website called CollegeVine where you can input your stats and it'll give you a well-calibrated percentage chance of getting into the college.
- **Location**: Sorry these are super inconsistent ... feel free to improve them with whatever system works for you
- **App**: You'll probably submit a Common App and a UC application! The UC app is literally just a checkbox to add more schools, while Common App schools typically have supplemental essays.
- **Terms**: When a college is "on the quarter system," they're usually including the summer quarter so it's secretly trimesters
- **Cost**: I never put this into my spreadsheet, but it's an important factor to keep in mind. Stanford can be cheaper than a state school.
- **Reqs**: Colleges vary widely in how much class freedom you get, from Brown's Open Curriculum to Harvey Mudd's Core.
- **R?**: Restrictive Early Action (R) means they won't let you EA to any other schools. Non-restrictive (N).
- **EA**: Early Action = apply early, get decision earlier, nonbinding
- **ED I**: Early Decision = if you ED and get in, you have to go
- **ED II**: Second ED deadline for some schools
- **RD**: Regular Decision = normal application
- **Other**: For some colleges, to have a chance at some scholarships, you have to apply earlier
- **SR SAT**: Most colleges allow self-reporting SAT, but some require official CollegeBoard scores.
- **Interview?**: Interviews are almost a joke sadly. Do them when optional. Except MIT, they care! Also foreign universities.
- **Students**: Populate with other students you know at the college.
- **Int. Major**: Beware of putting CS; it will meaningfully reduce your admissions chances at most schools.
- **Toured?**: Tours aren't very useful in my opinion. More helpful to talk to people you know at the college.
- **Portal?**: Keep track of whether you've made an account on their portal.


#### Tab Two: UC Activities & Awards

The University of California applications are mostly less involved than the Common App. Recommendation letters are ignored. But they give you more space to describe your activities and awards! You can put 20 (in contrast to the Common App's 10 + 5), and you have around double the character count. (Note: character count, not word count.)

For this reason, I've put it before the Common App activities list. In my personal experience, it's easier to write more and edit down then edit something down and try to expand it.

**Comments:**

- **Name**: The UC has a bunch of different categories for activities/awards, and they all have different follow-up questions.
- **9 10 11 12**: If something is during the summer, you're supposed to select the grade you were in before that summer
- **Hrs/week**: I always found these stressful, but you can ballpark these. They say, "It's ok to estimate, but try to be as accurate as possible."


#### Tab Three: Common App Activities

**Comments:**

- **Activity type**: I found the categories a bit weird, but they actually appear pretty large on the PDF that colleges see.
- **Timing of participation**: Bafflingly, these are checkboxes, so you can select multiple if you want.
- **Hrs/week**: Don't sweat it, just approximate something reasonable and the colleges are fine with it.
- **Similar activity in college?**: "I intend to participate in a similar activity in college" - yes or no. Not worth worrying about; you won't be held to it.


#### Tab Four: Common App Honors

**Comments:**

- **Honors title**: You literally get no description for these. Keep that in mind! (It's in the "Education" section.)
- **Level(s) of recognition**: One of those weird college app things where you just have to make something up and put it down and colleges don't really care ... as long as it has the right vibe


#### Tab Five: MIT Jobs & Activities & Distinctions

Compared to the rest of the "college application industrial complex," MIT's application always filled me with a strange sense of calm.

**Comments:**

- **Category**: You get up to: five jobs, four activities, six "summer activities", five "scholastic distinctions", five "non-scholastic distinctions." They also have a special spot for AMC/AIME, and tutoring with schoolhouse.world.
- **Participation period**: For jobs and summer activities, they want a timespan. For non-summer activities, a set of grades. For awards, a set of years.
- **Description (40 words)**: You get descriptions for jobs and activities. Not other things! Also, note that here it's by word count, instead of character count.


#### Tab Six: Supplementals At A Glance

I'm not gonna lie, this might need the College App App to be good. Still, this spreadsheet can help you make sense of the overlaps in the set of all questions you need to answer, see what the themes are in your application, and prioritize your work.

---

## Spreadsheet Prototype Data

The CSV source files are at `/Users/jmc/Downloads/Ultimate College Application Spreadsheet (created by Jacob Cohen) - *.csv`.

### College List (119 colleges)

Headers: College Name, Apply?, Tier, Acc., CVine, Location, App, Terms, Cost, Reqs, R?, EA, ED I, ED II, RD, Other, SR SAT, Interview?, Students, Faculty, Int. Major, 2nd Choice, 3rd Choice, Toured?, Portal?, Applicant Notes, Parent Notes, Jacob Random Notes

Jacob's Apply? labels mapped to standardized statuses:
- Yes → applying
- Probably → likely
- Maybe → considering
- Imaginably → unlikely
- Doubtful → not_applying
- DONE → applied
- (delete these) → not_applying
- Accepted/Waitlisted/Rejected → accepted/waitlisted/rejected

Sample colleges with full data: UCSB, UC Berkeley, UCLA, UC Davis, UCSD, UCSC, MIT, Brown, Yale, Harvard, Princeton, Stanford, CMU, Columbia, UChicago, Reed, Carleton, UIUC, Tufts, BU, Minerva, plus ~90 more with partial data.

### UC Activities & Awards (6 entries)

Categories: Award or honor, Educational preparation program, Extracurricular activity, Volunteer/Community Service, Work experience, Other coursework

Character limits: Background 0-250 chars, Description 0-350 chars

Sample entries:
1. The New York Times // Freelance Puzzle Creator (Work experience) - grades 11, 3 hrs/wk, 32 wks/yr
2. Student Teaching: Computer Science (Other coursework) - grade 12, 8 hrs/wk, 30 wks/yr
3. International Linguistics Olympiad US Team first alternate (Award) - grade 11
4. puzzlesforprogress.net (Extracurricular) - grades 9-12, 12 hrs/wk, 35 wks/yr
5. Camp Lemma / Proof School (Volunteer) - grades 11-12, 38 hrs/wk, 2 wks/yr
6. Internet content creator (Extracurricular) - grades 9-12, 7 hrs/wk, 26 wks/yr

Overflow: Caroline D. Bradley Scholarship (Award, grades 9-12, may not count since before HS)

### Common App Activities (2 entries + plans)

Character limits: Position 50 chars, Organization 100 chars, Description 150 chars

1. Journalism/Publication - Puzzle creator at The New York Times - grade 11, all year, 4 hrs/wk, 16 wks/yr
2. Community Service - Counselor at Camp Lemma (Proof School); Strategy & Puzzles Camp (Helios School) - grades 11-12, school year, 38 hrs/wk, 2 wks/yr

Also includes "Plans for Coming Year" section with future activity ideas.

### Common App Honors (3 entries)

No description field - just title + grades + recognition levels.

1. IOL US Team first alternate - grade 11, International
2. AIME qualifier - grades 10, 12, National
3. National Latin Exam medal (overflow) - grades 9-10, National

### MIT Jobs & Activities & Distinctions (10 entries)

Word limit: Description 40 words. Category limits: Jobs (5), Activities (4), Summer (6), Scholastic distinctions (5), Non-scholastic distinctions (5).

Jobs:
1. New York Times - Freelance puzzle constructor - Sep 2022-May 2023, 3 hrs/wk

Activities:
1. puzzlesforprogress.net - Sole creator - grades 10-12, 12 hrs/wk, 35 wks/yr

Summer Activities:
1. Camp Lemma (counselor) - June 2023, June 2022, 38 hrs/wk
2. MoMath MOVES conference 2022 - August 2022, 24 hrs/wk
3. Self-studying Python via Project Euler - Dec 2020-June 2022, 10 hrs/wk

Scholastic Distinctions:
1. IOL US team - First alternate - 2023, International

Non-scholastic Distinctions:
1. Wordle speedrunning community - 7 Wordles in 17 seconds; Crosscord/community record - 2022, National

### Supplementals (3 colleges: MIT, Stanford, Reed)

Matrix format: Essay categories (rows) x Colleges (columns)

Categories: Personal Essay, Major/Academics, Learning/Semi-Why Us, Lived Experience/World/Diversity, Activities, Community/Diversity, Why Us, Personal Challenge, Inspiration/Joy/Philosophical, Future/Global Challenge, Quirky/Misc, Hypothetical, Catchall, Other

MIT essays: Field of study at MIT (100 words), World you come from (200 words), Something for pleasure (150 words), Collaborated with others (200 words), Unexpected challenge (200 words), Additional Info
Stanford essays: Curiosity/Learning (250 words), Lived experience (250 words), Last two summers (50 words), Elaborate on extracurricular (50 words), Five important things (50 words), Significant challenge (50 words), Historical moment (50 words), Roommate letter (250 words)
Reed essays: How identity influences community (500 words), What class would I teach (500 words)
