# Auto Email Sender — Full Spec for Coding Agent

## Overview

Build a **local web app** (Python + Streamlit or Flask) that helps a user send personalized outreach emails in bulk (~10 at a time), with zero API costs. The tool orchestrates a workflow that includes profile parsing, duplicate checking against a shared Google Sheet, LLM-assisted personalization (via manual copy-paste to Claude web chat), email preview, SMTP sending, and automatic logging back to the Google Sheet.

The guiding principle: **the user should never have to think.** The tool does all the work; the user only copy-pastes when transferring between the tool and Claude web chat.

---

## Architecture

```
Local Streamlit/Flask Web App
├── Profile Parser (rule-based, from pasted directory text)
├── Google Sheets Integration (API — read for dedup, append after send)
├── Claude Prompt Generator (generates ready-to-copy prompts)
├── Email Composer (template + placeholders)
├── Email Previewer
├── SMTP Sender (Gmail with App Password)
└── Local Config Store (JSON file for persistence)
```

---

## Persistent Local Config

Save to a local JSON file (e.g., `~/.auto-email-sender/config.json`). Persists between sessions:

- **Gmail address** (sender)
- **Gmail App Password** (for SMTP)
- **Email template** (the full template text with placeholder markers)
- **Availability block** (free-text, updated weekly)
- **Sender name** (e.g., "Alex Kim")
- **Sender intro line** (e.g., "I'm on the partnerships team and would love to connect")
- **Email subject line**
- **Google Sheet ID** (the ID from the sheet URL)
- **Google Sheet column names** (sender, email, client name, company, date, notes)

The UI should have a **Settings** page/section where all of these can be viewed and edited.

---

## Workflow — Step by Step

### Step 1: Paste Raw Profiles

The user copies profiles from a directory site (Command+A, Command+C on each profile page) and pastes them into a large text box in the tool. They may paste multiple profiles in sequence, or one at a time.

**Parsing requirements:**

The directory profile pages have a consistent structure. When the user does Command+A on a profile page, the pasted text includes:

1. A **sidebar list** of other people (just name + company, one line each) — these are noise
2. The **main profile** with structured sections:
   - Header: Name with degree info (e.g., `Dr. Kallista Anne Bonawitz '02, MNG '03, PhD '08`)
   - `Work Information` section: Company, Phone, Industry, Occupation
   - `Home Information` section: Address
   - `Personal Information` section: Email
   - `MIT Information` section: Degrees, Preferred Class Year, Living Groups, Activities
3. **Footer junk**: navigation links, copyright text, etc.

**Parsing strategy — rule-based:**

1. Look for the section headers (`Work Information`, `Personal Information`, `MIT Information`) as anchors to identify the main profile block
2. Extract:
   - **Full name**: From the header line near these sections (the one with degree annotations like `'02, MNG '03`)
   - **First name**: Parse from full name (strip titles like Dr., Mr., Ms., etc.)
   - **Email**: From the `Personal Information` section (look for `Email` label, value is on the next line)
   - **Company**: From the `Work Information` section (look for `Company` label)
   - **Job title**: From the header or `Work Information` section
   - **Education details**: Degrees, living groups, activities — from `MIT Information` section. Store as raw text for personalization context.
3. Ignore everything before the first section header and after the footer markers (`600 Memorial Drive`, `Communities`, `Terms of Use`, etc.)
4. After parsing, display results in an **editable table** so the user can fix any parsing errors before proceeding.

**The table columns should be:** First Name, Full Name, Email, Company, Job Title, MIT Details (for personalization context), Personalized Sentence (empty, to be filled in Step 3)

If parsing fails on a profile, show the raw text and let the user manually fill in the fields.

### Step 2: Duplicate Check (Google Sheets)

Immediately after parsing, the tool reads the shared Google Sheet and checks if any of the parsed email addresses already appear in the configured email column.

**Google Sheet structure (default):**

| Column | Content |
|--------|---------|
| Sender Name | Which team member sent the email |
| Client Email | The recipient's email address |
| Client Name | Recipient's full name |
| Company | Recipient's company |
| Date (MM/DD) | Date the email was sent |
| Notes | Any relevant notes (job title, affiliation, etc.) |

**Behavior:**
- If a duplicate is found, flag it clearly in the UI (highlight the row red, show who already contacted them and when)
- The user can choose to remove flagged duplicates from the batch or proceed anyway
- **IMPORTANT: The tool only READS existing data and APPENDS new rows. It never modifies or deletes existing rows.** This is critical since multiple people share this sheet.

### Step 3: Generate Personalization Prompt

The tool generates a **complete, ready-to-copy prompt** for Claude web chat. The user's only job is: copy the prompt → paste into Claude → copy Claude's response → paste back into the tool.

**Generated prompt format:**

```
For each person below, write a SHORT phrase (max 1-2 sentences) that I can insert into an outreach email after the sentence "I'm also serving as [your role] this year."

Rules:
- The phrase should feel natural and warm, like something a real person would say
- It could be a very light personal connection IF one exists naturally (e.g., same field of study, same living group)
- If there's no natural connection, just write a warm generic sentence (e.g., "and I've been particularly inspired by the innovative work happening in [their industry]")
- Do NOT force connections. Do NOT reference obscure activities or hobbies from their profile — that comes across as stalkerish
- Do NOT make it sound like a college admissions essay trying to force a quote into an argument
- Keep it brief and understated. Less is more.
- Start each phrase with a lowercase word (it follows a comma after "...this year, " )
- Return ONLY a numbered list matching the order below. No extra commentary.

1. [First Name] [Last Name] — [Company], [Job Title]. MIT details: [MIT Details]
2. [First Name] [Last Name] — [Company], [Job Title]. MIT details: [MIT Details]
...
```

**After the user pastes Claude's response back:**
- The tool parses the numbered list and matches each sentence to the corresponding person
- Populates the "Personalized Sentence" column in the table
- Shows the result for quick review

### Step 4: Preview All Emails

Display all emails fully rendered with real content. The template with all placeholders filled in.

**Example template (stored in config, editable):**

```
Hi {first_name},

I'm reaching out regarding a potential collaboration.

My name is {sender_name}, and {sender_intro}, {personalized_sentence}

We partner with organizations on short, high-impact projects and would love to explore whether a conversation makes sense for {company}.

I'd love to schedule a short, 30-minute chat to share more details and answer any questions you may have. What do you think? Let me know which of these would work best for you (EST):

{availability}

However, I am very flexible so please let me know what works best for you!

All the best,
{sender_first_name}
```

**Placeholders:**

| Placeholder | Source |
|-------------|--------|
| `{first_name}` | Parsed from profile |
| `{sender_name}` | From config |
| `{sender_intro}` | From config |
| `{personalized_sentence}` | From Claude's response (Step 3) |
| `{company}` | Parsed from profile |
| `{availability}` | From config (updated weekly) |
| `{sender_first_name}` | Derived from sender_name |

Each email should be shown in a card/expandable section. The user can edit any individual email before sending.

### Step 5: Send

One-click "Send All" button. Sends via Gmail SMTP.

**SMTP Configuration:**
- Server: `smtp.gmail.com`
- Port: 587 (TLS)
- Auth: Gmail address + App Password (from config)
- Plain text emails (no HTML)
- Send with a small delay between emails (e.g., 2-3 seconds) to avoid rate limiting

**Subject line:** Should be configurable in settings. Default: `Potential Collaboration`

Show a progress indicator as emails send. After completion, show success/failure status for each email.

### Step 6: Log to Google Sheet

After successful sends, automatically append one row per email to the Google Sheet:

| Sender Name | Client Email | Client Name | Company | Date (MM/DD) | Notes |
|-------------|--------------|------------|---------|--------------|-------|
| Alex Kim | person@example.com | Sam Lee | Example Co. | 04/06 | Title, MIT details |

- **Sender Name**: From config
- **Date**: Today's date in MM/DD format
- **Notes**: Job title + any notable details, kept brief

---

## Google Sheets API Setup

### One-Time Setup Instructions (show in app on first run)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable the Google Sheets API
4. Create a Service Account, download the JSON key file
5. Share the Google Sheet with the service account email (as Editor)
6. In the tool's Settings, upload/point to the JSON key file and enter the Sheet ID

### Implementation Notes

- Use `gspread` library with service account auth
- Read: Fetch all rows to check for duplicate emails
- Write: Append rows only — never modify existing data
- Cache the sheet data at the start of each session to minimize API calls
- The Sheet ID is the long string in the Google Sheets URL between `/d/` and `/edit`

---

## UI Layout (Streamlit Recommended)

### Sidebar / Settings Page
- Gmail address + App Password fields
- Google Sheet ID + Service Account key path
- Sender name + intro line
- Email subject line
- Availability text area (multi-line, for the time slots)
- Email template text area (with placeholder syntax reference shown)
- Sheet column name inputs

### Main Workflow Page
1. **Paste Profiles** — Large text area + "Parse" button
2. **Review Parsed Data** — Editable table showing parsed fields + duplicate flags
3. **Generate Personalization** — Button that generates the Claude prompt + text area to paste Claude's response
4. **Preview Emails** — Expandable cards for each email
5. **Send** — "Send All" button with confirmation dialog
6. **Log** — Status showing what was written to the Google Sheet

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** (recommended for fast UI) or Flask
- **smtplib** (built-in, for SMTP sending)
- **gspread** + **google-auth** (for Google Sheets API)
- **re** (for profile parsing)
- **json** (for local config persistence)
- No paid APIs. No LLM API calls.

### Install dependencies:
```bash
pip install streamlit gspread google-auth
```

---

## Error Handling

- **Profile parsing failure**: Show raw text, let user fill fields manually
- **SMTP failure**: Show specific error per email (auth failure, rate limit, invalid address), allow retry
- **Google Sheets read failure**: Show warning but allow user to proceed without dedup check
- **Google Sheets write failure**: Show the rows that need to be added manually (as copyable text) so no data is lost
- **Claude response parsing failure**: If the numbered list doesn't match expected count, show raw response and let the user manually assign sentences

---

## Security Notes

- The Gmail App Password is stored locally in the config JSON. Warn the user not to share this file.
- The Google Service Account key file should be stored securely on disk.
- No data leaves the machine except via SMTP (to Gmail) and Google Sheets API.
- No LLM API calls are made by the tool.
