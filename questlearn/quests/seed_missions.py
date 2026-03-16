import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questlearn.settings')
import django; django.setup()

from quests.models import Mission

missions = [
    dict(
        title='Build an NGO Landing Page',
        skill='Web Dev',
        xp_reward=200,
        description='Create a simple, clean landing page for a fictional non-profit organization to help them reach donors online.',
        task=(
            "Your mission is to build a responsive landing page for a fictional NGO called 'GreenFuture'.\n\n"
            "Requirements:\n"
            "- Hero section with a compelling headline and CTA button\n"
            "- About section describing the NGO's mission\n"
            "- 3 impact stats (e.g. trees planted, volunteers, countries)\n"
            "- A simple contact/donate form\n"
            "- Fully responsive (mobile + desktop)\n\n"
            "Tech: HTML, CSS, Bootstrap (or any framework)\n\n"
            "Deliverable: GitHub repo link or zipped project file."
        ),
    ),
    dict(
        title='Climate Data Analysis',
        skill='Data Science',
        xp_reward=250,
        description='Analyze a real temperature dataset to identify climate trends and visualize your findings.',
        task=(
            "Download the NASA GISS Surface Temperature dataset (or use any public climate CSV).\n\n"
            "Requirements:\n"
            "- Load and clean the dataset using pandas\n"
            "- Calculate average temperature per decade\n"
            "- Plot a line chart showing temperature change over time\n"
            "- Write a short summary (3-5 sentences) of what the data shows\n\n"
            "Tech: Python, pandas, matplotlib or seaborn\n\n"
            "Deliverable: Jupyter notebook (.ipynb) or Python script + chart image."
        ),
    ),
    dict(
        title='Accessibility Fix Challenge',
        skill='Frontend',
        xp_reward=180,
        description='Take a poorly accessible webpage and improve it to meet WCAG 2.1 AA standards.',
        task=(
            "You are given a sample HTML page with multiple accessibility issues.\n\n"
            "Issues to fix:\n"
            "- Images missing alt text\n"
            "- Buttons with no labels\n"
            "- Poor color contrast (below 4.5:1 ratio)\n"
            "- Form inputs missing associated labels\n"
            "- No keyboard navigation support\n\n"
            "Create the broken page yourself, then fix all issues.\n"
            "Use a tool like axe DevTools or WAVE to verify your fixes.\n\n"
            "Deliverable: GitHub repo with before/after HTML files + a short report."
        ),
    ),
    dict(
        title='Bug Bounty Quest',
        skill='Backend',
        xp_reward=220,
        description='Find and fix bugs in a sample Django application. Document each bug and your fix.',
        task=(
            "Clone or recreate a simple Django app with the following intentional bugs:\n\n"
            "1. A view that doesn't check if the user is authenticated before showing data\n"
            "2. A form that accepts negative XP values\n"
            "3. A database query that causes an N+1 problem\n"
            "4. A missing CSRF token on a POST form\n\n"
            "For each bug:\n"
            "- Describe the bug and its security/performance impact\n"
            "- Show the broken code\n"
            "- Show your fix\n\n"
            "Deliverable: GitHub repo with a BUGS.md file documenting all 4 fixes."
        ),
    ),
    dict(
        title='Automation Quest',
        skill='DevOps',
        xp_reward=300,
        description='Automate a repetitive workflow using a shell script or Python automation tool.',
        task=(
            "Choose one of the following automation tasks:\n\n"
            "Option A — File Organizer:\n"
            "Write a script that scans a folder and sorts files into subfolders by extension "
            "(e.g. images/, docs/, code/).\n\n"
            "Option B — Daily Backup Script:\n"
            "Write a script that zips a target folder with a timestamp and saves it to a backup directory. "
            "Schedule it to run daily using cron (Linux/Mac) or Task Scheduler (Windows).\n\n"
            "Option C — GitHub Actions CI:\n"
            "Set up a GitHub Actions workflow that runs tests automatically on every push to main.\n\n"
            "Deliverable: GitHub repo with your script/workflow + a README explaining how to run it."
        ),
    ),
]

for m in missions:
    obj, created = Mission.objects.get_or_create(title=m['title'], defaults=m)
    print(f"{'Created' if created else 'Exists'}: {m['title']}")

print(f'\nDone. {Mission.objects.count()} missions in database.')
