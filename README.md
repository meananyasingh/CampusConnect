# CampusConnect

CampusConnect is a student career and placement management platform for students, recruiters, and college placement teams. It uses Django REST Framework for the backend and React for the frontend.

## Live demo

**https://campusconnectapp.pythonanywhere.com**

| Portal | Link |
|---|---|
| Student | [Sign up](https://campusconnectapp.pythonanywhere.com/student/signup) · [Sign in](https://campusconnectapp.pythonanywhere.com/student/login) |
| Recruiter | [Sign up](https://campusconnectapp.pythonanywhere.com/recruiter/signup) · [Sign in](https://campusconnectapp.pythonanywhere.com/recruiter/login) |
| College admin | [Sign in](https://campusconnectapp.pythonanywhere.com/admin-login) |
| API documentation | [Swagger UI](https://campusconnectapp.pythonanywhere.com/api/docs/) |

The demo runs on PythonAnywhere's free plan, so emails are not delivered; password-reset and activation links are written to the server log. See the [User Manual](USER_MANUAL.md) for a complete guide to every feature and [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md) for how the demo is deployed.

## Current status

- Modular Django project structure
- Custom email-based user model with student, recruiter, and college-admin roles
- Initial college model
- Public health-check API and OpenAPI documentation foundation
- React/Vite application with three portal entry routes
- SQLite for foundation development; MySQL credentials prepared for a later phase
- Student and recruiter registration with backend password validation
- Role-specific JWT login, token refresh, logout, and protected dashboard routes
- College and academic-program directory for student onboarding
- Automatic college-scoped student profiles with protected profile APIs
- Editable student personal/academic profile with validated profile-picture upload
- Student career portfolio with skills, projects, certifications, experience, and professional links
- Versioned PDF resume management with primary-resume selection and profile-completion scoring
- Recruiter/company onboarding with college-scoped verification and owner-managed company profiles
- College-targeted jobs and internships with publishing controls and student eligibility evaluation
- Student applications with resume selection, duplicate prevention, withdrawal, status history, and recruiter review
- Opportunity-specific recruitment rounds with interview scheduling, candidate instructions, outcomes, and private feedback
- College-scoped placement dashboards, recruitment oversight, verified offer records, and student offer decisions
- Persistent role-scoped notifications with unread tracking and workflow deep links
- College student account administration, visual placement analytics, and scoped CSV exports
- Live student and recruiter dashboards with role-scoped metrics, recent activity, interview schedules, and hiring performance
- College placement drives with opportunity grouping, scheduling, lifecycle controls, monitoring metrics, and student/recruiter visibility
- Targeted placement announcements with scheduling, expiry, priorities, read receipts, recruiter submissions, and college approval
- Explainable student opportunity recommendations, advanced discovery filters, and private saved-opportunity lists
- Recruiter candidate discovery across verified colleges with student privacy controls and company-private talent pools
- College-reviewed opportunity delivery with independent approvals, rejection notes, resubmission, withdrawal, and change reapproval
- Secure academic-document submission and college verification with readiness tracking and resubmission history
- College-configurable placement participation policies with student readiness guidance and server-enforced application controls
- CSV-based bulk student onboarding with validation previews, import history, and secure password-creation invitations
- Immutable college-scoped audit events for successful platform changes with searchable activity history and safe CSV export
- Branded workflow emails with per-user category preferences and college-managed student activation tracking/resends

## Prerequisites

- Python 3.10+
- Node.js and npm
- MySQL 8 (required when the project switches from SQLite)

## Backend setup

macOS/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Windows (PowerShell):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and activate again. Use `deactivate` to leave the virtual environment.

The API health check is available at `http://127.0.0.1:8000/api/health/` and interactive API documentation at `http://127.0.0.1:8000/api/docs/`.

## Frontend setup

```bash
cd frontend
npm ci
npm run dev
```

`npm ci` installs the exact versions recorded in `package-lock.json`. The frontend is available at `http://localhost:5173/`. Keep the backend and frontend running in separate terminals.

Virtual environments and `node_modules` are tied to the operating system they were created on. When moving the project between Windows and Linux/WSL, delete `backend/.venv` and `frontend/node_modules` and repeat the setup steps instead of copying them.

## Configuration

Copy `.env.example` to `.env` when environment-specific settings are needed. Never commit `.env`, passwords, secret keys, access tokens, private resumes, or generated dependency folders.

## Current development rule

Features are implemented incrementally and backed by real Django APIs. New workflows are added with role-scoped permissions and automated tests rather than placeholder data.

## Authentication API

Student and recruiter registration are public. Administrators have no public signup endpoint and must be created with Django's `createsuperuser` command.

```text
POST /api/auth/student/register/
POST /api/auth/student/login/
POST /api/auth/recruiter/register/
POST /api/auth/recruiter/login/
POST /api/auth/admin/login/
POST /api/auth/token/refresh/
GET  /api/auth/me/
POST /api/auth/logout/
POST /api/auth/password-reset/
POST /api/auth/password-reset/confirm/
```

During local development, password-reset emails and links are printed in the Django terminal. Production email delivery will be configured during deployment.

Recruiter signup creates only a company and recruiter-owner account. When the company wants to hire, the recruiter selects one or more colleges and sends recruitment requests through the portal. Each college reviews and responds to its own request independently. Changing approved company identity details sends the company back for review.

## Company API

```text
GET/PATCH /api/companies/recruiter/profile/
GET/PATCH /api/companies/recruiter/company/
GET/POST  /api/companies/recruiter/partnerships/
DELETE    /api/companies/recruiter/partnerships/<id>/  # pending requests only
GET       /api/companies/admin/partnerships/
GET/PATCH /api/companies/admin/partnerships/<id>/
```

## Opportunity API

```text
GET/POST        /api/opportunities/recruiter/
GET/PATCH/DELETE /api/opportunities/recruiter/<id>/
POST            /api/opportunities/recruiter/<id>/colleges/
DELETE          /api/opportunities/recruiter/invitations/<id>/
GET             /api/opportunities/admin/invitations/
PATCH           /api/opportunities/admin/invitations/<id>/
GET             /api/opportunities/student/
GET             /api/opportunities/student/recommended/
POST/DELETE     /api/opportunities/student/<id>/save/
GET             /api/opportunities/student/<id>/
```

Recruiters first create a reusable opportunity draft, then send it to one or more verified partner colleges. Company verification permits submission but does not automatically publish the opportunity. Each college placement office independently approves or rejects it with a review note. Only approved college audiences can see and apply. Recruiters can track responses, resubmit rejected requests, and withdraw pending requests. Material edits return active invitations to review before students can see the changed posting.

Student discovery supports search plus type, work mode, company, required skill, minimum compensation, deadline, eligibility, saved-only, and ordering filters. The recommendation endpoint ranks only eligible opportunities using an explainable score based on skill overlap, preferred role, preferred location or remote work, academic-program targeting, and available compensation details. Saved opportunities are private to each student.

## Student onboarding API

```text
GET  /api/colleges/
GET  /api/colleges/programs/?college=<id>
GET  /api/students/profile/
GET  /api/students/profile-completion/
GET  /api/students/                 # college admin only
GET  /api/students/admin/imports/template/
GET/POST /api/students/admin/imports/
POST /api/students/admin/imports/<id>/confirm/
POST /api/students/<id>/resend-activation/
GET/POST /api/students/resumes/
GET/PATCH/DELETE /api/students/resumes/<id>/
GET/POST /api/students/portfolio/skills/
GET/POST /api/students/portfolio/projects/
GET/POST /api/students/portfolio/certifications/
GET/POST /api/students/portfolio/experiences/
```

Students edit their personal and academic details at `/student/profile`, manage their career portfolio at `/student/portfolio`, and maintain PDF resume versions at `/student/resumes`. Each detail endpoint supports only its authenticated owner. College, program, enrollment number, and graduation year remain protected identity fields.

Students can disable recruiter discovery from their profile. When enabled, only recruiters whose company has an active, verified relationship with the student's college can view the student's professional profile or securely download the primary resume.

College administrators can onboard up to 500 students from one UTF-8 CSV file. The server validates account emails, enrollment numbers, academic programs, graduation years, CGPA, backlogs, duplicates, and college ownership before showing a row-by-row preview. Confirmation imports only valid rows and emails each student a single-user activation link so no temporary passwords are exposed to administrators. The student directory distinguishes active, suspended, activated, and invitation-pending states. Administrators can resend a pending invitation after a five-minute cooldown, but cannot generate activation links for another college or an already activated account. Recent preview and completed-import history remains available to the college.

## Student document verification API

```text
GET/POST  /api/documents/student/
GET       /api/documents/student/summary/
DELETE    /api/documents/student/<id>/
GET       /api/documents/student/<id>/download/
GET       /api/documents/admin/
PATCH     /api/documents/admin/<id>/
GET       /api/documents/admin/<id>/download/
```

Students can submit PDF, JPEG, or PNG academic documents up to 5 MB and track missing, pending, verified, or rejected requirements. College administrators only see documents belonging to their college and must provide a reason when rejecting a submission. Downloads require authentication, verified records cannot be deleted by students, and rejected documents remain in the audit history while allowing a corrected resubmission.

## Recruiter talent API

```text
GET       /api/talent/recruiter/candidates/
GET       /api/talent/recruiter/candidates/<id>/
GET       /api/talent/recruiter/candidates/<id>/resume/
GET/POST  /api/talent/recruiter/pools/
GET/PATCH/DELETE /api/talent/recruiter/pools/<id>/
POST      /api/talent/recruiter/pools/<pool-id>/members/
PATCH/DELETE /api/talent/recruiter/pools/<pool-id>/members/<member-id>/
```

Candidate discovery supports name, college, skill, graduation year, minimum CGPA, maximum backlog, primary-resume, and ordering filters. Recruiters can create talent pools, save candidates, and maintain private notes. Pools are shared only within the recruiter's company, and candidates stop appearing when their visibility or the relevant college partnership is no longer active.

## Application API

```text
GET/POST /api/applications/student/
GET      /api/applications/student/<id>/
POST     /api/applications/student/<id>/withdraw/
GET      /api/applications/recruiter/
GET/PATCH /api/applications/recruiter/<id>/
```

Only eligible students from a targeted college can apply, using one of their own uploaded resumes. Duplicate applications are blocked. Students can track their complete status timeline and withdraw while the application is still active. Recruiters can only review candidates who applied to their own company's opportunities.

## Interview and round API

```text
GET/POST   /api/applications/recruiter/rounds/
GET/PATCH/DELETE /api/applications/recruiter/rounds/<id>/
GET/POST   /api/applications/recruiter/interviews/
GET/PATCH  /api/applications/recruiter/interviews/<id>/
GET        /api/applications/student/interviews/
GET        /api/applications/student/interviews/<id>/
```

Recruiters configure ordered rounds for each published opportunity and schedule only shortlisted candidates. Scheduling automatically moves a candidate into the interview stage. Students see schedule, venue or meeting link, instructions, and released result; recruiter feedback and ratings remain private.

## College placement API

```text
GET       /api/placements/admin/dashboard/
GET/PATCH /api/placements/admin/policy/
GET       /api/placements/admin/drive-opportunities/
GET/POST  /api/placements/admin/drives/
GET/PATCH/DELETE /api/placements/admin/drives/<id>/
GET       /api/placements/admin/applications/
GET       /api/placements/admin/interviews/
GET/POST  /api/placements/admin/records/
GET/PATCH /api/placements/admin/records/<id>/
GET       /api/placements/student/
GET       /api/placements/student/readiness/
GET       /api/placements/student/drives/
PATCH     /api/placements/student/<id>/decision/
GET       /api/placements/recruiter/drives/
```

College administrators only see students, applications, interviews, companies, and placement records belonging to their assigned college. A placement record can only be created from a selected application. Students can accept or decline their own verified offers, while private placement-office notes remain hidden.

Placement drives group one or more published, college-approved opportunities into a scheduled campus event. College administrators control the draft, upcoming, ongoing, completed, and cancelled lifecycle and see application, interview, and selection totals. Students see published drives from their own college, while recruiters see drives containing their company's opportunities.

Each college can configure whether applications are open, require verified core documents, and set common profile-completion, CGPA, or active-backlog limits. These college rules are combined with each opportunity's eligibility criteria and enforced by Django when a student applies. Students can review all blockers and document progress at `/student/readiness`; they may continue browsing opportunities while resolving them.

## Notification API

```text
GET  /api/notifications/
GET  /api/notifications/unread-count/
POST /api/notifications/<id>/read/
POST /api/notifications/read-all/
GET/PATCH /api/notifications/preferences/
```

Notifications are created synchronously in Django for company-request responses, new or withdrawn applications, application status changes, interview schedules and updates, placement offers, announcements, document reviews, and student offer decisions. Each account only sees its own notifications. Branded text and HTML emails follow user-controlled category preferences; disabling email never removes the corresponding in-app notification. Redis and Celery are not required for this workflow.

## Audit API

```text
GET /api/audit/admin/
GET /api/audit/admin/export/
```

Successful authenticated create, update, and delete requests generate audit events without storing passwords, authentication tokens, or uploaded file contents. Events preserve an actor snapshot, role, category, affected record, changed field names, timestamp, and request IP. College administrators can search and filter only their own college's records at `/admin/audit-log`; recruiter activity is copied to the relevant connected college scopes. Audit exports protect spreadsheet applications from formula injection. Logging begins when this feature is installed and does not reconstruct older historical actions.

## Announcement API

```text
GET/POST        /api/announcements/admin/
GET/PATCH/DELETE /api/announcements/admin/<id>/
POST            /api/announcements/admin/<id>/review/
GET/POST         /api/announcements/recruiter/
GET/PATCH/DELETE /api/announcements/recruiter/<id>/
GET              /api/announcements/student/
POST             /api/announcements/student/<id>/read/
```

College announcements can target selected academic programs and graduation years, link to an opportunity or placement drive, be scheduled or expired, and carry normal, important, or urgent priority. College notices are approved immediately. Recruiter notices require a verified college relationship and remain pending until that college approves or rejects them. Students only see current approved notices matching their academic profile, with persistent read status and in-app notifications.

## Analytics and report API

```text
GET   /api/analytics/student/dashboard/
GET   /api/analytics/recruiter/dashboard/
GET   /api/analytics/admin/overview/
GET   /api/analytics/admin/reports/students/
GET   /api/analytics/admin/reports/applications/
GET   /api/analytics/admin/reports/placements/
GET   /api/students/                         # searchable college directory
PATCH /api/students/<id>/                    # college-scoped account management
```

The student dashboard shows profile readiness, application progress, upcoming interviews, placement selections, and eligible skill-matched opportunities. The recruiter dashboard shows company hiring metrics, recent candidates, interview schedules, approved-college count, and opportunity performance. The admin analytics screen shows the application pipeline, monthly application activity, branch-wise placement performance, and company package statistics. All dashboard data is scoped by the authenticated role, company, or college. Student, application, and placement CSV reports contain only the authenticated administrator's college data.

Before testing student signup, create at least one active college and academic program through Django Admin at `http://127.0.0.1:8000/django-admin/`. The `/admin/...` paths belong to the React college-admin portal.
