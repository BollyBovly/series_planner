from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Series, UserViewingPlan, WatchingHistory, Episode, UserSeriesRating


def home(request):
    series_list = Series.objects.all().order_by('-rating', '-created_at')
    
    user_series_ids = []
    if request.user.is_authenticated:
        user_series_ids = UserViewingPlan.objects.filter(
            user=request.user
        ).values_list('series_id', flat=True)
    
    context = {
        'series_list': series_list,
        'user_series_ids': user_series_ids,
    }
    return render(request, 'planner/home.html', context)


@login_required
def series_list(request):
    status_filter = request.GET.get('status', 'all')
    
    viewing_plans = UserViewingPlan.objects.filter(
        user=request.user
    ).select_related('series')
    
    if status_filter != 'all':
        viewing_plans = viewing_plans.filter(status=status_filter)
    
    context = {
        'viewing_plans': viewing_plans,
        'status_filter': status_filter,
    }
    return render(request, 'planner/series_list.html', context)


@login_required
def series_detail(request, series_id):
    series = get_object_or_404(Series, id=series_id)
    
    try:
        user_plan = UserViewingPlan.objects.get(user=request.user, series=series)
    except UserViewingPlan.DoesNotExist:
        user_plan = None
    
    try:
        user_rating = UserSeriesRating.objects.get(user=request.user, series=series)
    except UserSeriesRating.DoesNotExist:
        user_rating = None
    
    episodes = Episode.objects.filter(series=series).order_by('season_number', 'episode_number')
    
    context = {
        'series': series,
        'user_plan': user_plan,
        'user_rating': user_rating,
        'episodes': episodes,
    }
    return render(request, 'planner/series_detail.html', context)


@login_required
def add_to_list(request, series_id):
    series = get_object_or_404(Series, id=series_id)
    
    user_plan, created = UserViewingPlan.objects.get_or_create(
        user=request.user,
        series=series,
        defaults={
            'status': 'planning',
            'daily_hours_available': 2.0
        }
    )
    
    if created:
        messages.success(request, f'Сериал "{series.title}" добавлен в ваш список!')
    else:
        messages.info(request, f'Сериал "{series.title}" уже в вашем списке.')
    
    return redirect('series_detail', series_id=series_id)


@login_required
def remove_from_list(request, plan_id):
    user_plan = get_object_or_404(UserViewingPlan, id=plan_id, user=request.user)
    series_title = user_plan.series.title
    user_plan.delete()
    
    messages.success(request, f'Сериал "{series_title}" удален из списка.')
    return redirect('series_list')


@login_required
def update_progress(request, plan_id):
    user_plan = get_object_or_404(UserViewingPlan, id=plan_id, user=request.user)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        last_season = int(request.POST.get('last_season', 0))
        last_episode = int(request.POST.get('last_episode', 0))
        daily_hours = float(request.POST.get('daily_hours', 2.0))
        
        user_plan.status = status
        user_plan.last_season_watched = last_season
        user_plan.last_episode_watched = last_episode
        user_plan.daily_hours_available = daily_hours
        user_plan.save()
        
        messages.success(request, 'Прогресс обновлен!')
    
    return redirect('series_detail', series_id=user_plan.series.id)


@login_required
def mark_episode_watched(request, plan_id, season, episode):
    user_plan = get_object_or_404(UserViewingPlan, id=plan_id, user=request.user)
    
    user_plan.last_season_watched = season
    user_plan.last_episode_watched = episode
    
    if user_plan.status == 'planning':
        user_plan.status = 'watching'
    
    user_plan.save()
    
    try:
        episode_obj = Episode.objects.get(
            series=user_plan.series,
            season_number=season,
            episode_number=episode
        )
        WatchingHistory.objects.create(
            user=request.user,
            series=user_plan.series,
            episode=episode_obj,
            duration_watched=episode_obj.duration
        )
    except Episode.DoesNotExist:
        WatchingHistory.objects.create(
            user=request.user,
            series=user_plan.series,
            duration_watched=user_plan.series.average_episode_duration
        )
    
    messages.success(request, f'Эпизод S{season:02d}E{episode:02d} отмечен как просмотренный!')
    return redirect('series_detail', series_id=user_plan.series.id)


@login_required
def rate_series(request, series_id):
    series = get_object_or_404(Series, id=series_id)
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        review = request.POST.get('review', '')
        
        user_rating, created = UserSeriesRating.objects.update_or_create(
            user=request.user,
            series=series,
            defaults={
                'rating': rating,
                'review': review
            }
        )
        
        messages.success(request, 'Ваша оценка сохранена!')
    
    return redirect('series_detail', series_id=series_id)


@login_required
def statistics(request):
    viewing_plans = UserViewingPlan.objects.filter(user=request.user).select_related('series')
    
    total_series = viewing_plans.count()
    watching = viewing_plans.filter(status='watching').count()
    completed = viewing_plans.filter(status='completed').count()
    paused = viewing_plans.filter(status='paused').count()
    planning = viewing_plans.filter(status='planning').count()
    dropped = viewing_plans.filter(status='dropped').count()
    
    total_hours = 0
    total_episodes = 0
    
    for plan in viewing_plans:
        episodes_watched = plan.get_episodes_watched()
        total_episodes += episodes_watched
        total_hours += (episodes_watched * plan.series.average_episode_duration) / 60
    
    genre_stats = {}
    for plan in viewing_plans:
        if plan.series.genres:
            genres = [g.strip() for g in plan.series.genres.split(',')]
            for genre in genres:
                if genre:
                    genre_stats[genre] = genre_stats.get(genre, 0) + 1
    
    sorted_genres = sorted(genre_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_history = WatchingHistory.objects.filter(
        user=request.user,
        watched_at__gte=thirty_days_ago
    ).select_related('series', 'episode').order_by('-watched_at')[:20]
    
    context = {
        'stats': {
            'total_series': total_series,
            'watching': watching,
            'completed': completed,
            'paused': paused,
            'planning': planning,
            'dropped': dropped,
            'total_hours': round(total_hours, 1),
            'total_episodes': total_episodes,
        },
        'favorite_genres': sorted_genres,
        'recent_history': recent_history,
    }
    
    return render(request, 'planner/statistics.html', context)


@login_required
def search_series(request):
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Series.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(genres__icontains=query)
        ).order_by('-rating', '-created_at')
    
    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'planner/search.html', context)
