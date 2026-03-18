# QuestLearn

A gamified learning platform built with Django. Complete quests, earn XP, level up, and apply skills through real-world missions.

---

## Tech Stack

- Python 3.13 · Django 6.x
- SQLite · Bootstrap 5 · Chart.js
- Custom dark UI design system (Inter font, refined spacing, no frameworks beyond Bootstrap grid)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
cd questlearn
python manage.py migrate

# 3. (Optional) Seed data
python manage.py shell -c "exec(open('quests/seed_quests.py').read())"
python manage.py shell -c "exec(open('quests/seed_missions.py').read())"

# 4. Create superuser
python manage.py createsuperuser

# 5. Run server
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
| Leaderboard | Top 10 players by XP with podium |
| Profile | Avatar, stats, completed quests, Skill DNA link |

### Quest System
| Feature | Description |
|---|---|
| Quest Types | Learning, Coding, Quiz, Project, Boss |
| Multi-step Quests | Sequential steps each with their own XP reward |
| Prerequisites | Quests lock until required quests are completed |
| Hints System | Unlock hints per step for an XP cost |
| Submission | Submit code, GitHub link, or quiz answer |
| Quest Progress | Step-by-step progress bar with done / current / locked states |
| Content Unlock | Full learning content unlocked after quest completion |

### Missions
| Feature | Description |
|---|---|
| Real-world Missions | Build projects, fix bugs, automate workflows |
| Submission | GitHub link + file upload + notes |
| Admin Review | Approve/reject with bulk actions — XP auto-awarded on approval |

### Skill DNA
| Feature | Description |
|---|---|
| Radar Chart | Chart.js radar showing XP across 8 skill tracks |
| Contribution Graph | GitHub-style 26-week activity heatmap |
| Skill Tree | 4 milestones per track with unlock indicators |
| XP Bars | Per-skill XP breakdown with percentages |

### Pages
| Page | URL |
|---|---|
| Home | `/` |
| Dashboard | `/dashboard/` |
| Quests | `/quests/` |
| Missions | `/missions/` |
| Leaderboard | `/leaderboard/` |
| Profile | `/profile/` |
| Daily Quest | `/daily-quest/` |
| XP Wallet | `/xp-wallet/` |
| Skill DNA | `/skill-dna/` |
| Achievements | `/achievements/` |
| Friends | `/friends/` |
| AI Mentor | `/ai-mentor/` |
| Settings | `/settings/` |

### Friends System
- Search any user by username
- Send / accept / decline / remove friend requests
- Pending requests panel
- Top Learners list with quick Add buttons

### AI Mentor
Rule-based chatbot answering questions about XP, levels, quests, missions, skills, achievements, hints, friends, and daily quests.

---

## Admin Panel

`http://127.0.0.1:8000/admin/`

- Manage quests, steps, hints, missions
- Approve/reject mission submissions — XP auto-awarded on approval
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
FriendRequest     — from_user, to_user, status
```

---

## Project Structure

```
questlearn/
├── manage.py
├── requirements.txt
├── questlearn/
│   ├── settings.py
│   └── urls.py
└── quests/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── forms.py
    ├── migrations/
    └── templates/
```
