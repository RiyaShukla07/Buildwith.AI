from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
import json, datetime
from .models import (Quest, CompletedQuest, UserProfile, Mission, MissionSubmission,
                     SkillXP, ActivityLog, QuestStep, QuestProgress, StepSubmission,
                     QuestHint, UnlockedHint, FriendRequest)
from .forms import SignupForm, MissionSubmissionForm


def _record_activity(user, xp, skill):
    """Update SkillXP and ActivityLog for today."""
    today = timezone.now().date()
    skill_obj, _ = SkillXP.objects.get_or_create(user=user, skill=skill)
    skill_obj.xp += xp
    skill_obj.save()
    log, _ = ActivityLog.objects.get_or_create(user=user, date=today)
    log.xp_earned += xp
    log.actions   += 1
    log.save()


def home(request):
    return render(request, 'home.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to QuestLearn, {user.username}!')
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    completed_ids = CompletedQuest.objects.filter(
        user=request.user).values_list('quest_id', flat=True)
    quests = Quest.objects.exclude(id__in=completed_ids)
    xp_to_next = 200 - (profile.xp % 200)
    xp_percent = (profile.xp % 200) / 200 * 100
    return render(request, 'dashboard.html', {
        'profile': profile,
        'quests': quests,
        'xp_to_next': xp_to_next,
        'xp_percent': xp_percent,
    })

@login_required
def quest_list(request):
    completed_ids = list(CompletedQuest.objects.filter(
        user=request.user).values_list('quest_id', flat=True))
    quests = Quest.objects.prefetch_related('prerequisites', 'steps').all()
    quest_data = []
    for q in quests:
        unlocked = q.is_unlocked_for(request.user)
        completed = q.id in completed_ids
        progress = QuestProgress.objects.filter(user=request.user, quest=q).first()
        step_count = q.steps.count()
        completed_steps = 0
        if progress:
            completed_steps = StepSubmission.objects.filter(
                user=request.user, step__quest=q, is_correct=True).count()
        quest_data.append({
            'quest': q,
            'unlocked': unlocked,
            'completed': completed,
            'progress': progress,
            'step_count': step_count,
            'completed_steps': completed_steps,
        })
    return render(request, 'quests.html', {
        'quest_data': quest_data,
        'completed_ids': completed_ids,
    })


@login_required
def quest_detail(request, quest_id):
    quest = get_object_or_404(Quest, id=quest_id)
    is_completed = CompletedQuest.objects.filter(user=request.user, quest=quest).exists()
    if not is_completed:
        messages.info(request, 'Complete this quest first to unlock its content.')
        return redirect('quest_list')
    return render(request, 'quest_detail.html', {'quest': quest})


@login_required
def quest_play(request, quest_id):
    quest = get_object_or_404(Quest, id=quest_id)
    if not quest.is_unlocked_for(request.user):
        messages.warning(request, 'Complete the prerequisite quests first.')
        return redirect('quest_list')
    already_done = CompletedQuest.objects.filter(user=request.user, quest=quest).exists()
    steps = list(quest.steps.all())
    if not steps:
        if not already_done:
            CompletedQuest.objects.create(user=request.user, quest=quest)
            profile = request.user.userprofile
            profile.xp += quest.xp_reward
            profile.update_level()
            _record_activity(request.user, quest.xp_reward, quest.track)
            messages.success(request, f'Quest completed! +{quest.xp_reward} XP 🎉')
            return redirect('quest_detail', quest_id=quest.id)
        return redirect('quest_detail', quest_id=quest.id)
    progress, _ = QuestProgress.objects.get_or_create(user=request.user, quest=quest)
    completed_step_ids = set(StepSubmission.objects.filter(
        user=request.user, step__quest=quest, is_correct=True
    ).values_list('step_id', flat=True))
    current_step = None
    for step in steps:
        if step.id not in completed_step_ids:
            current_step = step
            break
    if current_step is None and not already_done:
        CompletedQuest.objects.create(user=request.user, quest=quest)
        profile = request.user.userprofile
        profile.xp += quest.xp_reward
        profile.update_level()
        _record_activity(request.user, quest.xp_reward, quest.track)
        if progress.completed_at is None:
            progress.completed_at = timezone.now()
            progress.save()
        messages.success(request, f'Quest completed! +{quest.xp_reward} XP 🎉')
        return redirect('quest_detail', quest_id=quest.id)
    if current_step is None:
        return redirect('quest_detail', quest_id=quest.id)
    hints = current_step.hints.all()
    unlocked_hint_ids = set(UnlockedHint.objects.filter(
        user=request.user, hint__step=current_step
    ).values_list('hint_id', flat=True))
    step_statuses = []
    for s in steps:
        if s.id in completed_step_ids:
            step_statuses.append({'step': s, 'status': 'done'})
        elif s.id == current_step.id:
            step_statuses.append({'step': s, 'status': 'current'})
        else:
            step_statuses.append({'step': s, 'status': 'locked'})
    prev_submission = StepSubmission.objects.filter(user=request.user, step=current_step).first()
    return render(request, 'quest_play.html', {
        'quest': quest,
        'current_step': current_step,
        'step_statuses': step_statuses,
        'hints': hints,
        'unlocked_hint_ids': list(unlocked_hint_ids),
        'completed_step_ids': list(completed_step_ids),
        'already_done': already_done,
        'prev_submission': prev_submission,
        'profile': request.user.userprofile,
    })


@login_required
def submit_step(request, quest_id, step_id):
    if request.method != 'POST':
        return redirect('quest_play', quest_id=quest_id)
    quest = get_object_or_404(Quest, id=quest_id)
    step  = get_object_or_404(QuestStep, id=step_id, quest=quest)
    answer      = request.POST.get('answer', '').strip()
    github_link = request.POST.get('github_link', '').strip()
    if step.step_type == 'quiz':
        is_correct = (answer.lower() == step.correct_answer.lower()) if step.correct_answer else bool(answer)
    elif step.step_type == 'learning':
        is_correct = True
    else:
        is_correct = bool(answer or github_link)
    sub, created = StepSubmission.objects.get_or_create(
        user=request.user, step=step,
        defaults={'answer': answer, 'github_link': github_link, 'is_correct': is_correct}
    )
    if not created:
        sub.answer = answer
        sub.github_link = github_link
        sub.is_correct = is_correct
        sub.save()
    if is_correct:
        profile = request.user.userprofile
        profile.xp += step.xp_reward
        profile.update_level()
        _record_activity(request.user, step.xp_reward, quest.track)
        messages.success(request, f'Step complete! +{step.xp_reward} XP ⚡')
    else:
        messages.error(request, 'Not quite right — check the hints and try again.')
    return redirect('quest_play', quest_id=quest.id)


@login_required
def unlock_hint(request, quest_id, step_id, hint_id):
    quest = get_object_or_404(Quest, id=quest_id)
    step  = get_object_or_404(QuestStep, id=step_id, quest=quest)
    hint  = get_object_or_404(QuestHint, id=hint_id, step=step)
    already = UnlockedHint.objects.filter(user=request.user, hint=hint).exists()
    if not already:
        profile = request.user.userprofile
        if profile.xp >= hint.xp_cost:
            profile.xp -= hint.xp_cost
            profile.save()
            UnlockedHint.objects.create(user=request.user, hint=hint)
            messages.info(request, f'Hint unlocked! -{hint.xp_cost} XP')
        else:
            messages.error(request, f'Not enough XP (costs {hint.xp_cost} XP).')
    return redirect('quest_play', quest_id=quest.id)


@login_required
def complete_quest(request, quest_id):
    """Legacy redirect."""
    return redirect('quest_play', quest_id=quest_id)


@login_required
def leaderboard(request):
    profiles = UserProfile.objects.select_related('user').order_by('-xp')[:10]
    return render(request, 'leaderboard.html', {'profiles': profiles})


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    completed_quests = CompletedQuest.objects.filter(
        user=request.user).select_related('quest').order_by('-completed_at')
    total_quests = Quest.objects.count()
    xp_to_next = 200 - (profile.xp % 200)
    xp_percent = (profile.xp % 200) / 200 * 100
    rank = UserProfile.objects.filter(xp__gt=profile.xp).count() + 1
    return render(request, 'profile.html', {
        'profile': profile,
        'completed_quests': completed_quests,
        'completed_count': completed_quests.count(),
        'total_quests': total_quests,
        'xp_to_next': xp_to_next,
        'xp_percent': xp_percent,
        'rank': rank,
    })


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('home')
    return redirect('profile')


@login_required
def mission_list(request):
    missions = Mission.objects.filter(status='open')
    submitted_ids = MissionSubmission.objects.filter(
        user=request.user).values_list('mission_id', flat=True)
    submissions = {s.mission_id: s for s in MissionSubmission.objects.filter(user=request.user)}
    return render(request, 'missions.html', {
        'missions': missions,
        'submitted_ids': list(submitted_ids),
        'submissions': submissions,
    })


@login_required
def mission_detail(request, mission_id):
    mission = get_object_or_404(Mission, id=mission_id)
    existing = MissionSubmission.objects.filter(user=request.user, mission=mission).first()
    if request.method == 'POST' and not existing:
        form = MissionSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.user = request.user
            sub.mission = mission
            sub.save()
            messages.success(request, 'Mission submitted! XP will be awarded after admin review. 🚀')
            return redirect('mission_detail', mission_id=mission.id)
    else:
        form = MissionSubmissionForm()
    return render(request, 'mission_detail.html', {
        'mission': mission,
        'form': form,
        'existing': existing,
    })


@login_required
def skill_dna(request):
    user = request.user
    skill_data = list(SkillXP.objects.filter(user=user).order_by('-xp').values('skill', 'xp'))
    if not skill_data:
        qs = (CompletedQuest.objects.filter(user=user)
              .values('quest__track')
              .annotate(total=Sum('quest__xp_reward'))
              .order_by('-total'))
        skill_data = [{'skill': r['quest__track'], 'xp': r['total']} for r in qs]
    total_skill_xp = sum(s['xp'] for s in skill_data) or 1
    for s in skill_data:
        s['pct'] = round(s['xp'] / total_skill_xp * 100)
    today = timezone.now().date()
    start = today - datetime.timedelta(days=181)
    logs  = {log.date: log for log in ActivityLog.objects.filter(user=user, date__gte=start)}
    graph_days = []
    for i in range(182):
        d = start + datetime.timedelta(days=i)
        log = logs.get(d)
        xp  = log.xp_earned if log else 0
        graph_days.append({'date': d.isoformat(), 'xp': xp, 'actions': log.actions if log else 0})
    max_xp = max((d['xp'] for d in graph_days), default=1) or 1
    for d in graph_days:
        if d['xp'] == 0: d['level'] = 0
        elif d['xp'] <= max_xp * 0.25: d['level'] = 1
        elif d['xp'] <= max_xp * 0.5:  d['level'] = 2
        elif d['xp'] <= max_xp * 0.75: d['level'] = 3
        else: d['level'] = 4
    SKILL_TREE = [
        {'name': 'Web Development', 'icon': '🌐', 'milestones': [50, 200, 500, 1000]},
        {'name': 'Backend',         'icon': '⚙️',  'milestones': [50, 200, 500, 1000]},
        {'name': 'Frontend',        'icon': '🎨',  'milestones': [50, 200, 500, 1000]},
        {'name': 'Data Science',    'icon': '📊',  'milestones': [50, 200, 500, 1000]},
        {'name': 'DevOps',          'icon': '🚀',  'milestones': [50, 200, 500, 1000]},
        {'name': 'Testing',         'icon': '🧪',  'milestones': [50, 200, 500, 1000]},
        {'name': 'Full Stack',      'icon': '💡',  'milestones': [50, 200, 500, 1000]},
        {'name': 'General',         'icon': '📚',  'milestones': [50, 200, 500, 1000]},
    ]
    skill_xp_map = {s['skill']: s['xp'] for s in skill_data}
    for node in SKILL_TREE:
        xp = skill_xp_map.get(node['name'], 0)
        node['xp'] = xp
        node['unlocked'] = [xp >= m for m in node['milestones']]
        node['next_milestone'] = next((m for m in node['milestones'] if xp < m), None)
    radar_labels = [n['name'] for n in SKILL_TREE]
    radar_values = [min(skill_xp_map.get(n['name'], 0), 1000) for n in SKILL_TREE]
    recent = sorted([d for d in graph_days if d['xp'] > 0], key=lambda x: x['date'], reverse=True)[:10]
    return render(request, 'skill_dna.html', {
        'skill_data': skill_data,
        'graph_days': json.dumps(graph_days),
        'skill_tree': SKILL_TREE,
        'radar_labels': json.dumps(radar_labels),
        'radar_values': json.dumps(radar_values),
        'recent': recent,
        'total_skill_xp': total_skill_xp,
    })

@login_required
def daily_quest(request):
    import hashlib
    today = timezone.now().date()
    quests = list(Quest.objects.all())
    if quests:
        seed = int(hashlib.md5(f"{today}{request.user.id}".encode()).hexdigest(), 16)
        quest = quests[seed % len(quests)]
        already = CompletedQuest.objects.filter(user=request.user, quest=quest).exists()
    else:
        quest, already = None, False
    profile = request.user.userprofile
    log_today = ActivityLog.objects.filter(user=request.user, date=today).first()
    yesterday = today - datetime.timedelta(days=1)
    log_yesterday = ActivityLog.objects.filter(user=request.user, date=yesterday).first()
    return render(request, 'daily_quest.html', {
        'quest': quest, 'already': already, 'profile': profile,
        'log_today': log_today, 'log_yesterday': log_yesterday,
    })


@login_required
def xp_wallet(request):
    profile = request.user.userprofile
    completed_quests = CompletedQuest.objects.filter(
        user=request.user).select_related('quest').order_by('-completed_at')
    approved_missions = MissionSubmission.objects.filter(
        user=request.user, status='approved').select_related('mission').order_by('-reviewed_at')
    xp_to_next = 200 - (profile.xp % 200)
    xp_percent = (profile.xp % 200) / 200 * 100
    history = []
    for cq in completed_quests:
        history.append({'label': cq.quest.title, 'xp': cq.quest.xp_reward,
                        'date': cq.completed_at, 'type': 'quest', 'track': cq.quest.track})
    for ms in approved_missions:
        history.append({'label': ms.mission.title, 'xp': ms.mission.xp_reward,
                        'date': ms.reviewed_at, 'type': 'mission', 'track': ms.mission.skill})
    history.sort(key=lambda x: x['date'], reverse=True)
    total_from_quests   = sum(cq.quest.xp_reward for cq in completed_quests)
    total_from_missions = sum(ms.mission.xp_reward for ms in approved_missions)
    return render(request, 'xp_wallet.html', {
        'profile': profile, 'history': history,
        'xp_to_next': xp_to_next, 'xp_percent': xp_percent,
        'total_from_quests': total_from_quests, 'total_from_missions': total_from_missions,
    })


@login_required
def achievements(request):
    profile = request.user.userprofile
    completed_count = CompletedQuest.objects.filter(user=request.user).count()
    mission_count   = MissionSubmission.objects.filter(user=request.user, status='approved').count()
    skill_xp_list   = SkillXP.objects.filter(user=request.user)
    def badge(title, icon, desc, condition, color='#6366f1'):
        return {'title': title, 'icon': icon, 'desc': desc, 'unlocked': condition, 'color': color}
    all_badges = [
        badge('First Step',      '🎯', 'Complete your first quest',     completed_count >= 1,  '#34d399'),
        badge('Quest Seeker',    '⚔️',  'Complete 5 quests',             completed_count >= 5,  '#6366f1'),
        badge('Quest Master',    '🏆', 'Complete 10 quests',            completed_count >= 10, '#fbbf24'),
        badge('Legend',          '👑', 'Complete all quests',           completed_count >= Quest.objects.count() and Quest.objects.count() > 0, '#f87171'),
        badge('XP Rookie',       '⚡', 'Earn 100 XP',                   profile.xp >= 100,     '#fbbf24'),
        badge('XP Hunter',       '💥', 'Earn 500 XP',                   profile.xp >= 500,     '#f97316'),
        badge('XP God',          '🌟', 'Earn 1000 XP',                  profile.xp >= 1000,    '#a78bfa'),
        badge('Level 5',         '🔥', 'Reach Level 5',                 profile.level >= 5,    '#f87171'),
        badge('Level 10',        '🚀', 'Reach Level 10',                profile.level >= 10,   '#6366f1'),
        badge('Mission Ready',   '🌍', 'Submit your first mission',     MissionSubmission.objects.filter(user=request.user).exists(), '#34d399'),
        badge('Mission Hero',    '🦸', 'Get 3 missions approved',       mission_count >= 3,    '#fbbf24'),
        badge('Skill Starter',   '🧬', 'Earn XP in 3 different skills', skill_xp_list.count() >= 3, '#a78bfa'),
        badge('Full Stack Hero', '💡', 'Earn XP in 5 different skills', skill_xp_list.count() >= 5, '#6366f1'),
    ]
    unlocked = [b for b in all_badges if b['unlocked']]
    locked   = [b for b in all_badges if not b['unlocked']]
    return render(request, 'achievements.html', {
        'unlocked': unlocked, 'locked': locked, 'profile': profile, 'total': len(all_badges),
    })


@login_required
def friends(request):
    query = request.GET.get('q', '').strip()
    search_results = []
    if query:
        search_results = User.objects.filter(username__icontains=query).exclude(id=request.user.id)[:10]

    # Accepted friends
    sent_accepted = FriendRequest.objects.filter(from_user=request.user, status='accepted').select_related('to_user')
    recv_accepted = FriendRequest.objects.filter(to_user=request.user, status='accepted').select_related('from_user')
    friends_list = [r.to_user for r in sent_accepted] + [r.from_user for r in recv_accepted]

    # Pending received requests
    pending_received = FriendRequest.objects.filter(to_user=request.user, status='pending').select_related('from_user')

    # IDs of users already requested or friends with
    sent_ids = set(FriendRequest.objects.filter(from_user=request.user).values_list('to_user_id', flat=True))

    top_users = UserProfile.objects.select_related('user').order_by('-xp')[:8]
    return render(request, 'friends.html', {
        'top_users': top_users,
        'query': query,
        'search_results': search_results,
        'friends_list': friends_list,
        'pending_received': pending_received,
        'sent_ids': sent_ids,
    })


@login_required
def friend_request_action(request, action, user_id):
    target = get_object_or_404(User, id=user_id)
    if action == 'send':
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=target)
        messages.success(request, f'Friend request sent to {target.username}.')
    elif action == 'accept':
        req = get_object_or_404(FriendRequest, from_user=target, to_user=request.user)
        req.status = 'accepted'
        req.save()
        messages.success(request, f'You are now friends with {target.username}!')
    elif action == 'reject':
        FriendRequest.objects.filter(from_user=target, to_user=request.user).delete()
        messages.info(request, 'Request declined.')
    elif action == 'remove':
        FriendRequest.objects.filter(
            from_user=request.user, to_user=target
        ).delete()
        FriendRequest.objects.filter(
            from_user=target, to_user=request.user
        ).delete()
        messages.info(request, f'Removed {target.username} from friends.')
    return redirect('friends')


@login_required
def ai_mentor(request):
    profile = request.user.userprofile
    completed_count = CompletedQuest.objects.filter(user=request.user).count()
    skill_xp_list   = SkillXP.objects.filter(user=request.user).order_by('-xp')
    top_skill  = skill_xp_list.first()
    weak_skill = skill_xp_list.last() if skill_xp_list.count() > 1 else None
    next_quests = Quest.objects.exclude(
        id__in=CompletedQuest.objects.filter(user=request.user).values('quest_id')
    ).order_by('xp_reward')[:3]
    return render(request, 'ai_mentor.html', {
        'profile': profile,
        'top_skill': top_skill,
        'weak_skill': weak_skill,
        'next_quests': next_quests,
        'completed_count': completed_count,
        'tips': [
            {'icon': '🔥', 'title': 'Stay consistent', 'body': 'Even one quest a day compounds fast. Streaks build momentum.'},
            {'icon': '🎯', 'title': 'Focus on weak skills', 'body': 'Check your Skill DNA and deliberately practice your lowest-XP track.'},
            {'icon': '🌍', 'title': 'Do real-world missions', 'body': 'Missions give 2–4× more XP than quests and build a portfolio.'},
            {'icon': '🏆', 'title': 'Chase the leaderboard', 'body': 'Competing with others is one of the strongest learning motivators.'},
        ],
    })


@login_required
def ai_chat(request):
    """Simple rule-based chatbot for QuestLearn questions."""
    import json as _json
    if request.method != 'POST':
        return redirect('ai_mentor')
    try:
        data = _json.loads(request.body)
        msg = data.get('message', '').lower().strip()
    except Exception:
        msg = ''

    profile = request.user.userprofile
    completed_count = CompletedQuest.objects.filter(user=request.user).count()

    # Rule-based responses
    reply = None
    if any(w in msg for w in ['xp', 'experience', 'points']):
        reply = f"You currently have {profile.xp} XP and are Level {profile.level}. You earn XP by completing quests and getting missions approved!"
    elif any(w in msg for w in ['quest', 'quests']):
        reply = f"You've completed {completed_count} quests so far. Head to the Quests page to find new ones. Each quest has steps — learning, coding, and quiz!"
    elif any(w in msg for w in ['mission', 'missions']):
        reply = "Missions are real-world challenges where you build something and submit a GitHub link or file. Approved missions award 150+ XP!"
    elif any(w in msg for w in ['level', 'levels']):
        reply = f"You're Level {profile.level}. Every 200 XP = 1 level. Keep completing quests and missions to level up!"
    elif any(w in msg for w in ['skill', 'skills', 'dna']):
        reply = "Your Skill DNA shows XP earned per skill track. Check the Skill DNA page for your radar chart and contribution graph!"
    elif any(w in msg for w in ['leaderboard', 'rank', 'ranking']):
        reply = "The leaderboard shows the top 10 learners by XP. Complete more quests and missions to climb the ranks!"
    elif any(w in msg for w in ['achievement', 'badge', 'badges']):
        reply = "There are 13 badges to unlock — from First Step to Full Stack Hero. Check the Achievements page to see your progress!"
    elif any(w in msg for w in ['friend', 'friends']):
        reply = "You can search for friends by username on the Friends page and send them a friend request!"
    elif any(w in msg for w in ['daily', 'streak']):
        reply = "Your daily quest changes every day. Complete it to build your streak and earn bonus XP!"
    elif any(w in msg for w in ['hint', 'hints']):
        reply = "Hints cost a small amount of XP to unlock. They appear on the quest play page when you're stuck on a step."
    elif any(w in msg for w in ['hello', 'hi', 'hey', 'hii']):
        reply = f"Hey {request.user.username}! 👋 I'm your QuestLearn AI Mentor. Ask me anything about quests, XP, missions, or skills!"
    elif any(w in msg for w in ['help', 'how', 'what']):
        reply = "I can help with: XP & levels, quests & steps, missions, skills, achievements, friends, and daily quests. Just ask!"
    elif any(w in msg for w in ['discord']):
        reply = "Join our Discord community from the Settings page! Connect with other learners, share progress, and get help."
    else:
        reply = f"Great question! I'm still learning, but I can help with XP, quests, missions, skills, achievements, and more. Try asking about any of those!"

    from django.http import JsonResponse
    return JsonResponse({'reply': reply})


@login_required
def settings_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_email':
            new_email = request.POST.get('email', '').strip()
            if new_email:
                request.user.email = new_email
                request.user.save()
                messages.success(request, 'Email updated successfully.')
        elif action == 'update_password':
            from django.contrib.auth import update_session_auth_hash
            p1 = request.POST.get('password1', '')
            p2 = request.POST.get('password2', '')
            if p1 and p1 == p2:
                request.user.set_password(p1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password updated successfully.')
            else:
                messages.error(request, 'Passwords do not match.')
        return redirect('settings')
    return render(request, 'settings.html', {'user': request.user})
