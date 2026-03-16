from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user    = models.OneToOneField(User, on_delete=models.CASCADE)
    xp      = models.IntegerField(default=0)
    level   = models.IntegerField(default=1)
    streak  = models.IntegerField(default=0)

    def update_level(self):
        self.level = self.xp // 200 + 1
        self.save()

    def __str__(self):
        return f'{self.user.username} — Level {self.level} ({self.xp} XP)'


class Quest(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy',   'Easy'),
        ('medium', 'Medium'),
        ('hard',   'Hard'),
        ('boss',   'Boss'),
    ]
    TYPE_CHOICES = [
        ('learning', 'Learning Quest'),
        ('coding',   'Coding Quest'),
        ('quiz',     'Quiz Quest'),
        ('project',  'Project Quest'),
        ('boss',     'Boss Quest'),
    ]
    title         = models.CharField(max_length=200)
    description   = models.TextField()
    content       = models.TextField(blank=True, default='',
                        help_text='Full learning content shown after quest completion.')
    xp_reward     = models.IntegerField(default=50)
    difficulty    = models.CharField(max_length=10,
                        choices=DIFFICULTY_CHOICES, default='easy')
    track         = models.CharField(max_length=100, default='General')
    quest_type    = models.CharField(max_length=10, choices=TYPE_CHOICES, default='learning')
    prerequisites = models.ManyToManyField('self', symmetrical=False,
                        blank=True, related_name='unlocks')

    def is_unlocked_for(self, user):
        """Returns True if all prerequisites are completed by this user."""
        prereq_ids = self.prerequisites.values_list('id', flat=True)
        if not prereq_ids:
            return True
        completed_ids = CompletedQuest.objects.filter(
            user=user).values_list('quest_id', flat=True)
        return all(pid in completed_ids for pid in prereq_ids)

    def __str__(self):
        return self.title


class QuestStep(models.Model):
    STEP_TYPE_CHOICES = [
        ('learning', 'Learning'),
        ('coding',   'Coding'),
        ('quiz',     'Quiz'),
    ]
    quest          = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='steps')
    order          = models.PositiveIntegerField(default=1)
    step_type      = models.CharField(max_length=10, choices=STEP_TYPE_CHOICES, default='learning')
    title          = models.CharField(max_length=200)
    content        = models.TextField(help_text='Learning text, code prompt, or quiz question.')
    correct_answer = models.TextField(blank=True,
                        help_text='For quiz steps: the expected answer (case-insensitive match).')
    xp_reward      = models.IntegerField(default=20)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.quest.title} — Step {self.order}: {self.title}'


class QuestHint(models.Model):
    step     = models.ForeignKey(QuestStep, on_delete=models.CASCADE, related_name='hints')
    order    = models.PositiveIntegerField(default=1)
    text     = models.TextField()
    xp_cost  = models.IntegerField(default=5)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Hint {self.order} for {self.step}'


class QuestProgress(models.Model):
    """Tracks which step a user is on for a given quest."""
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quest_progress')
    quest        = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='progress')
    current_step = models.ForeignKey(QuestStep, on_delete=models.SET_NULL,
                       null=True, blank=True, related_name='+')
    started_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'quest')

    def __str__(self):
        return f'{self.user.username} → {self.quest.title}'


class StepSubmission(models.Model):
    """Records a user's submission for a single quest step."""
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='step_submissions')
    step        = models.ForeignKey(QuestStep, on_delete=models.CASCADE, related_name='submissions')
    answer      = models.TextField(blank=True)
    github_link = models.URLField(blank=True)
    is_correct  = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'step')

    def __str__(self):
        return f'{self.user.username} — {self.step} [{"✓" if self.is_correct else "✗"}]'


class UnlockedHint(models.Model):
    """Records which hints a user has already paid to unlock."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_hints')
    hint = models.ForeignKey(QuestHint, on_delete=models.CASCADE, related_name='unlocked_by')

    class Meta:
        unique_together = ('user', 'hint')

    def __str__(self):
        return f'{self.user.username} unlocked hint {self.hint.id}'


class CompletedQuest(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    quest        = models.ForeignKey(Quest, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'quest')

    def __str__(self):
        return f'{self.user.username} completed {self.quest.title}'


class Mission(models.Model):
    SKILL_CHOICES = [
        ('Web Dev',      'Web Dev'),
        ('Data Science', 'Data Science'),
        ('Frontend',     'Frontend'),
        ('Backend',      'Backend'),
        ('DevOps',       'DevOps'),
        ('Other',        'Other'),
    ]
    STATUS_CHOICES = [
        ('open',   'Open'),
        ('closed', 'Closed'),
    ]
    title       = models.CharField(max_length=200)
    description = models.TextField()
    task        = models.TextField(help_text='Detailed task instructions for the user.')
    skill       = models.CharField(max_length=50, choices=SKILL_CHOICES, default='Other')
    xp_reward   = models.IntegerField(default=150)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MissionSubmission(models.Model):
    REVIEW_STATUS = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    mission      = models.ForeignKey(Mission, on_delete=models.CASCADE)
    github_link  = models.URLField(blank=True)
    project_file = models.FileField(upload_to='mission_uploads/', blank=True, null=True)
    notes        = models.TextField(blank=True, help_text='Describe what you built.')
    status       = models.CharField(max_length=10, choices=REVIEW_STATUS, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'mission')

    def __str__(self):
        return f'{self.user.username} → {self.mission.title} [{self.status}]'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


class SkillXP(models.Model):
    """Tracks XP earned per skill/track for a user."""
    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_xp')
    skill = models.CharField(max_length=100)
    xp    = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'skill')

    def __str__(self):
        return f'{self.user.username} — {self.skill}: {self.xp} XP'


class ActivityLog(models.Model):
    """One row per day per user — powers the contribution graph."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    date = models.DateField()
    xp_earned = models.IntegerField(default=0)
    actions   = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f'{self.user.username} — {self.date}: {self.xp_earned} XP'


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    from_user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f'{self.from_user.username} → {self.to_user.username} [{self.status}]'
