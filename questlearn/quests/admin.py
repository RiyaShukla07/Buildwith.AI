from django.contrib import admin
from django.utils import timezone
from .models import (UserProfile, Quest, CompletedQuest, Mission, MissionSubmission,
                     SkillXP, ActivityLog, QuestStep, QuestHint, QuestProgress,
                     StepSubmission, UnlockedHint, FriendRequest)


class QuestStepInline(admin.TabularInline):
    model = QuestStep
    extra = 1


class QuestHintInline(admin.TabularInline):
    model = QuestHint
    extra = 1


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display  = ['title', 'difficulty', 'quest_type', 'xp_reward', 'track']
    list_filter   = ['difficulty', 'track', 'quest_type']
    search_fields = ['title']
    filter_horizontal = ['prerequisites']
    inlines       = [QuestStepInline]


@admin.register(QuestStep)
class QuestStepAdmin(admin.ModelAdmin):
    list_display  = ['quest', 'order', 'step_type', 'title', 'xp_reward']
    list_filter   = ['step_type', 'quest']
    inlines       = [QuestHintInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'xp', 'level', 'streak']


@admin.register(CompletedQuest)
class CompletedQuestAdmin(admin.ModelAdmin):
    list_display = ['user', 'quest', 'completed_at']


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display  = ['title', 'skill', 'xp_reward', 'status']
    list_filter   = ['skill', 'status']
    search_fields = ['title']


@admin.register(MissionSubmission)
class MissionSubmissionAdmin(admin.ModelAdmin):
    list_display  = ['user', 'mission', 'status', 'submitted_at']
    list_filter   = ['status']
    actions       = ['approve', 'reject']

    def approve(self, request, queryset):
        for sub in queryset.filter(status='pending'):
            sub.status = 'approved'
            sub.reviewed_at = timezone.now()
            sub.save()
            profile = sub.user.userprofile
            profile.xp += sub.mission.xp_reward
            profile.update_level()
            # record skill XP + activity
            from .models import SkillXP, ActivityLog
            skill_obj, _ = SkillXP.objects.get_or_create(user=sub.user, skill=sub.mission.skill)
            skill_obj.xp += sub.mission.xp_reward
            skill_obj.save()
            today = timezone.now().date()
            log, _ = ActivityLog.objects.get_or_create(user=sub.user, date=today)
            log.xp_earned += sub.mission.xp_reward
            log.actions   += 1
            log.save()
        self.message_user(request, f'{queryset.count()} submission(s) approved and XP awarded.')
    approve.short_description = '✅ Approve & award XP'

    def reject(self, request, queryset):
        queryset.filter(status='pending').update(
            status='rejected', reviewed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} submission(s) rejected.')
    reject.short_description = '❌ Reject submissions'


admin.site.register(SkillXP)
admin.site.register(ActivityLog)
admin.site.register(QuestProgress)
admin.site.register(StepSubmission)
admin.site.register(UnlockedHint)
admin.site.register(FriendRequest)
