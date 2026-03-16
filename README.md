# 🎮 QuestLearn

A gamified learning platform built with Django. Complete quests, earn XP, level up, and apply skills through real-world missions.

---

## Tech Stack

- Python 3.13 · Django 5.x
- SQLite (dev) · Bootstrap 5 · Chart.js
- Dark space theme with glassmorphism UI

---

## Quick Start

```bash
# 1. Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install django pillow

# 3. Run migrations
cd questlearn
python manage.py migrate

# 4. Seed data
python manage.py shell -c "exec(open('quests/seed_quests.py').read())"
python manage.py shell -c "exec(open('quests/seed_content.py').read())"
python manage.py shell -c "exec(open('quests/seed_missions.py').read())"

# 5. Create superuser
python manage.py createsuperuser

# 6. Run server
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## Features

### Core
| Feature | Description |
|---|---|
| Auth | Signup, login, logout, delete account |
| XP & Levels | Every 200 XP = 1 level |
| Leaderboard | Top 10 players by XP |
| Profile | Avatar, stats, completed quests, Skill DNA link |

### Quest System
| Feature | Description |
|---|---|
| Quest Types | Learning, Coding, Quiz, Project, Boss |
| Multi-step Quests | Sequential steps — each with its own XP reward |
| Prerequisites | Quests lock until required quests are completed |
| Hints System | Unlock hints per step for an XP cost |
| Submission | Submit code, GitHub link, or quiz answer |
| Quest Progress | Step-by-step progress bar with ✓ / current / locked states |
| Content Unlock | Full learning content unlocked after quest completion |

### Missions
| Feature | Description |
|---|---|
| Real-world Missions | Build NGO sites, fix bugs, automate workflows, etc. |
| Submission | GitHub link + file upload + notes |
| Admin Review | Approve/reject with bulk actions — XP auto-awarded on approval |

### Skill DNA
| Feature | Description |
|---|---|
| Radar Chart | Chart.js radar showing XP across 8 skill tracks |
| Contribution Graph | GitHub-style 26-week activity heatmap |
| Skill Tree | 4 milestones per track with unlock indicators |
| XP Bars | Per-skill XP breakdown with percentages |

### Sidebar Pages
| Page | URL | Description |
|---|---|---|
| Dashboard | `/dashboard/` | Stats, XP bar, available quests |
| Quests | `/quests/` | All quests with lock/unlock/progress state |
| Missions | `/missions/` | Real-world mission list |
| Leaderboard | `/leaderboard/` | Top 10 by XP |
| Profile | `/profile/` | User stats, completed quests |
| Daily Quest | `/daily-quest/` | Deterministic quest-of-the-day + streak |
| XP Wallet | `/xp-wallet/` | Full XP history timeline |
| Skill DNA | `/skill-dna/` | Radar chart + heatmap + skill tree |
| Achievements | `/achievements/` | 13 badges with unlock conditions |
| Friends | `/friends/` | Search users, send/accept/remove friend requests |
| AI Mentor | `/ai-mentor/` | Personalised tips + rule-based chatbot |
| Settings | `/settings/` | Email, password, Discord link, delete account |

### Friends System
- Search any user by username
- Send / accept / decline / remove friend requests
- Pending requests panel
- Friends list with Remove option
- Top Learners list with Add Friend buttons

### AI Mentor Chatbot
Rule-based chatbot answering questions about:
XP, levels, quests, missions, skills, achievements, hints, friends, daily quests, Discord

---

## Admin Panel

`http://127.0.0.1:8000/admin/`

- Manage quests, quest steps, hints, missions
- Approve/reject mission submissions (bulk actions auto-award XP)
- View user profiles, activity logs, skill XP

---

## Models

```
UserProfile       — xp, level, streak
Quest             — title, type, difficulty, track, prerequisites (M2M self)
QuestStep         — quest FK, order, step_type, content, correct_answer, xp_reward
QuestHint         — step FK, order, text, xp_cost
QuestProgress     — user + quest progress tracking
StepSubmission    — user answer/code/github per step
UnlockedHint      — tracks which hints a user has paid to unlock
CompletedQuest    — user + quest completion record
Mission           — title, skill, task, xp_reward
MissionSubmission — user submission with review status
SkillXP           — per-user per-skill XP totals
ActivityLog       — daily XP + action count (powers heatmap)
FriendRequest     — from_user, to_user, status (pending/accepted/rejected)
```

---

## Default Credentials (dev)

| User | Password |
|---|---|
| admin | Admin123! |
| testuser | Quest123! |

---

## Project Structure

```
questlearn/
├── manage.py
├── questlearn/          # Django project settings
│   ├── settings.py
│   └── urls.py
└── quests/              # Main app
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── forms.py
    ├── seed_quests.py
    ├── seed_content.py
    ├── seed_missions.py
    ├── migrations/
    └── templates/
        ├── base.html
        ├── home.html
        ├── dashboard.html
        ├── quests.html
        ├── quest_detail.html
        ├── quest_play.html      ← multi-step quest player
        ├── missions.html
        ├── mission_detail.html
        ├── leaderboard.html
        ├── profile.html
        ├── skill_dna.html
        ├── daily_quest.html
        ├── xp_wallet.html
        ├── achievements.html
        ├── friends.html
        ├── ai_mentor.html
        ├── settings.html
        ├── login.html
        └── signup.html
```
