# JobRADAR: Job Notification Agent for the Students by the Students 🚀

## Problem We Are Solving 📢
As students, we have faced significant challenges while searching for jobs. The biggest issue is not receiving interview calls, even after applying to thousands of places. One of the main reasons for this is the overwhelming volume of applications that entry-level jobs receive. Within just a few hours of posting, these jobs can have thousands of applicants, reducing the chances of skilled candidates even passing the initial ATS screening.

To address this, we created **JobRADAR**: A job notification agent that crawls major Big Tech career pages every 15 minutes and sends you an email notification whenever a new job is posted. This way, you can apply immediately before the application pool becomes saturated, improving your chances of getting noticed.

## Features ✨
- **Automated Job Crawling**: Monitors job postings every 15 minutes.
- **Personalized Notifications**: Sends an email with job details, including job ID, position, and link.
- **Customizable Searches**: Allows users to add their own crawlers for desired companies.
- **Open Source & Contributable**: Set up and run locally or contribute to the project!

## Architecture Diagram 🏗️
Below is the architecture diagram illustrating how JobRADAR works:

![JobRADAR Architecture](images/jr1.jpg)

## How to Set Up JobRADAR Locally 🛠️

### Step 1: Choose the country and the companies 🌍
1. Download the project repository.
2. Open `job_crawlers-main/urls/urls.json`. It ships tracking **Costa Rica** for **Amazon, Microsoft, Intel and P&G**:
   ```json
   {
       "country": "Costa Rica",
       "companies": {
           "Amazon":    [{ "country_code": "CRI", "categories": ["Software Development", "Solutions Architect"] }],
           "Microsoft": [{ "location": "Costa Rica", "categories": ["Software Engineering"] }],
           "Intel":     [{ "tenant": "intel.wd1", "site": "intel/External", "categories": ["Software Engineering"] }],
           "P&G":       [{ "tenant": "pg.wd5", "site": "pg/1000", "title_keywords": ["software", "data"] }]
       }
   }
   ```
   (shortened: the file itself lists every technical category of each company)
3. `country` is what every crawler filters on. Amazon needs the [ISO-3166 alpha-3 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) as well. Intel and P&G run on Workday: their location filter is resolved by name at runtime, so only `tenant` and `site` are needed.
4. `categories` keeps only the jobs a company files under those categories, using **that company's own taxonomy** (Amazon calls it a category, Microsoft a department, Workday a job family). The name has to match theirs exactly. Remove the key to receive every job in the country.
5. `title_keywords` keeps only the jobs whose title contains one of the words, matched whole so `IT` does not match `Digital`. It is the fallback for P&G, whose Workday site publishes no categories.
6. Not sure which categories exist? Run a check and read the log: every crawler prints the categories it filtered out, for example `Microsoft: ignored jobs in Digital Solution Area Specialists (1)`. Those names are the ones you can add.

### Step 2: Set Up Notifications 🔔
Alerts go out as **push notifications through [ntfy](https://ntfy.sh)**, which needs no account and no token: the topic name *is* the address. Pick one nobody can guess, install the ntfy app (Android / iOS / web) and subscribe to it.
```bash
NTFY_TOPIC=job-radar-cr-<something-random>
```

Email is an optional second channel. It is the only part of the project that needs credentials, so it stays off unless you set them (`JOB_RADAR_EMAIL_PASSWORD` must be a Gmail [app password](https://myaccount.google.com/apppasswords), never your account password):
```bash
JOB_RADAR_EMAIL=you@gmail.com
JOB_RADAR_EMAIL_PASSWORD=your_app_password
JOB_RADAR_DEFAULT_RECEIVER=you@gmail.com
```

Jobs that were already announced are remembered in `job_crawlers-main/data/seen_jobs.json`, so there is no database to run. Delete the file to be notified about every open position again.

### Step 3 (Optional): Add Your Own Crawlers 🤖
1. Navigate to `job_crawlers-main/crawlers`.
2. Each crawler queries the company's public job API and returns `company / title / number / link / location` dicts.
3. Companies hosted on Workday need no new crawler: add them to `urls.json` and reuse `workday_crawler.py`.
4. Register the new crawler in `CRAWLERS` inside `app.py`.

### Step 4: Start the Crawler 🚀
```bash
cd job_crawlers-main
python app.py
```
`POST /main` with `{"email": "you@gmail.com"}` (this is what the frontend button does) runs a first check right away and then every 15 minutes. `GET /check_new_job` runs a single check on demand.

### Step 5 (Optional): Run it in the cloud, without keeping a machine on ☁️
`job_check.py` is a single pass over every crawler, and `.github/workflows/job-radar.yml` runs it on a 15 minute cron, so there is no server, no database and **no secret** to hand over:

1. Push the project to your own GitHub repository (public or private, whichever you prefer).
2. In *Settings → Secrets and variables → Actions → Variables*, add the variable `NTFY_TOPIC` with your topic. It is a variable and not a secret on purpose: it is an address, not a credential.
3. Open the *Actions* tab, pick **Job Radar** and hit *Run workflow* to check the setup. From then on it runs on its own.

State lives in `data/seen_jobs.json`, which the workflow commits back to the repository after every run using the `GITHUB_TOKEN` that GitHub generates for the job. The frontend and `app.py` are not part of this path: the scheduler is GitHub's cron.

Two things worth knowing: GitHub queues cron runs on shared runners, so in practice checks land every 20-30 minutes rather than exactly every 15; and GitHub disables scheduled workflows after 60 days without repository activity (it emails you, and one click re-enables them).

---

## Setting Up the Project Locally 🏗️

### Prerequisites ✅
- **Node.js & npm** (for frontend)
- **Python & required packages** (for backend)

No database is needed: the jobs already announced are kept in `job_crawlers-main/data/seen_jobs.json`.

### Installation 📦
#### 1. Frontend Setup
```bash
cd job-crawler-frontend
npm install
```

#### 2. Backend Setup
```bash
cd job_crawlers-main
pip install -r requirement.txt
```

### Running the Application ▶️
#### 1. Start the Backend
```bash
python app.py
```

#### 2. Start the Frontend
```bash
cd job-crawler-frontend
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

---

## Contributing 🤝
We welcome contributions from everyone! Follow these steps:
1. **Fork** the repository.
2. **Create** a new branch for your feature or bug fix.
3. **Commit** your changes.
4. **Submit** a pull request detailing your modifications.

---

## Project Links 🔗
- **Legacy GitHub Repository**: [JobCrawler](https://github.com/DevanshuBrahmbhatt/job_crawlers)
- **Join Our Discord Server**: [Link](https://discord.gg/VCErB2jc)

## Disclaimer ⚠️
This is an **open-source student project** meant for **educational purposes**. We do **not** guarantee any job placements, interviews, or accuracy of job listings. Use this tool at your own discretion. We are not responsible for any errors or issues that arise.

---

## License 📝
This project is licensed under the **MIT License**, meaning you are free to use, modify, and distribute it without restrictions.

```plaintext
MIT License

Copyright (c) 2025 JobRADAR

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

---

🚀 **Happy Job Hunting!** 🎯

