import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questlearn.settings')
django.setup()

from quests.models import Quest

quests = [
    dict(title='Build your first HTML page',
         description='Create a basic HTML page with headings, paragraphs and lists.',
         xp_reward=50, difficulty='easy', track='Web Development'),
    dict(title='Style a page with CSS',
         description='Add colors, fonts, and layout using CSS. Make it look beautiful.',
         xp_reward=100, difficulty='easy', track='Web Development'),
    dict(title='Add JavaScript interactivity',
         description='Make buttons and forms work with JS event listeners and DOM manipulation.',
         xp_reward=150, difficulty='medium', track='Web Development'),
    dict(title='Build a REST API with Django',
         description='Create endpoints that return JSON data using Django REST framework.',
         xp_reward=200, difficulty='medium', track='Backend'),
    dict(title='Connect a database',
         description='Use Django ORM to save and retrieve data efficiently.',
         xp_reward=200, difficulty='medium', track='Backend'),
    dict(title='Write unit tests',
         description='Write comprehensive tests for your application using Django test client.',
         xp_reward=150, difficulty='medium', track='Testing'),
    dict(title='Deploy to the cloud',
         description='Push your project live on Railway or Render with a production database.',
         xp_reward=300, difficulty='hard', track='DevOps'),
    dict(title='Set up CI/CD pipeline',
         description='Automate testing and deployment with GitHub Actions.',
         xp_reward=350, difficulty='hard', track='DevOps'),
    dict(title='Implement user authentication',
         description='Build a complete auth system with login, registration, and password reset.',
         xp_reward=250, difficulty='hard', track='Backend'),
    dict(title='Build a personal portfolio website',
         description='BOSS QUEST: Create a full site with projects showcase, about me, and contact form.',
         xp_reward=500, difficulty='boss', track='Web Development'),
    dict(title='Create a full-stack e-commerce app',
         description='BOSS QUEST: Build a shopping site with product catalog, cart, and payment integration.',
         xp_reward=700, difficulty='boss', track='Full Stack'),
]

for q in quests:
    obj, created = Quest.objects.get_or_create(title=q['title'], defaults=q)
    status = 'Created' if created else 'Already exists'
    print(f'{status}: {q["title"]}')

print(f'\nDone! {Quest.objects.count()} quests in database.')
