from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from datetime import date, timedelta

from matplotlib.style import context
from .models import Series, Episode, UserViewingPlan, WatchingHistory
from .forms import ViewingPlanForm, TimeCalculatorForm
import os
from django.views.decorators.http import require_POST
from django.db.models import F
from django.conf import settings
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
from django.db import models
import matplotlib.pyplot as plt

def home(request):
    context = {
        'message': 'Добро пожаловать!',
    }
    return render(request, 'home.html', context)




def series_list(request):
    series_queryset = Series.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        series_queryset = series_queryset.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    genre_filter = request.GET.get('genre', '')
    if genre_filter:
        series_queryset = series_queryset.filter(genres__icontains=genre_filter)
    
    all_genres = set()
    for series in Series.objects.all():
        if series.genres:
            genres = [g.strip() for g in series.genres.split(',')]
            all_genres.update(genres)
    
    context = {
        'series_list': series_queryset,
        'search_query': search_query,
        'all_genres': sorted(all_genres),
        'selected_genre': genre_filter,
    }
    return render(request, 'planner/series_list.html', context)


def series_detail(request, series_id):
    series = get_object_or_404(Series, id=series_id)
    episodes = Episode.objects.filter(series=series).order_by('season_number', 'episode_number')
    
    seasons = {}
    for episode in episodes:
        if episode.season_number not in seasons:
            seasons[episode.season_number] = []
        seasons[episode.season_number].append(episode)
    
    calculator_form = TimeCalculatorForm(request.GET or None)
    calculation_result = None
    
    if calculator_form.is_valid():
        daily_hours = calculator_form.cleaned_data['daily_hours']
        total_hours = series.get_total_duration_hours()
        days_needed = round(total_hours / float(daily_hours))
        finish_date = date.today() + timedelta(days=days_needed)
        
        calculation_result = {
            'days_needed': days_needed,
            'finish_date': finish_date,
            'daily_hours': daily_hours,
        }
    
    user_has_plan = False
    if request.user.is_authenticated:
        user_has_plan = UserViewingPlan.objects.filter(user=request.user, series=series).exists()
    
    context = {
        'series': series,
        'seasons': dict(sorted(seasons.items())),
        'calculator_form': calculator_form,
        'calculation_result': calculation_result,
        'user_has_plan': user_has_plan,
    }
    return render(request, 'planner/series_detail.html', context)


@login_required
def my_watchlist(request):
    watching = UserViewingPlan.objects.filter(user=request.user, status='watching')
    completed = UserViewingPlan.objects.filter(user=request.user, status='completed')
    paused = UserViewingPlan.objects.filter(user=request.user, status='paused')
    planning = UserViewingPlan.objects.filter(user=request.user, status='planning')
    
    context = {
        'watching': watching,
        'completed': completed,
        'paused': paused,
        'planning': planning,
    }
    return render(request, 'planner/my_watchlist.html', context)


@login_required
def add_to_watchlist(request, series_id):
    series = get_object_or_404(Series, id=series_id)
    
    if UserViewingPlan.objects.filter(user=request.user, series=series).exists():
        messages.warning(request, 'Этот сериал уже есть в вашем списке.')
        return redirect('series_detail', series_id=series_id)
    
    if request.method == 'POST':
        form = ViewingPlanForm(request.POST, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.series = series
            plan.save()
            messages.success(request, f'Сериал "{series.title}" добавлен в ваш список!')
            return redirect('my_watchlist')
    else:
        form = ViewingPlanForm(initial={'series': series}, user=request.user)
    
    context = {
        'form': form,
        'series': series,
    }
    return render(request, 'planner/add_to_watchlist.html', context)


@login_required
def update_viewing_plan(request, plan_id):
    plan = get_object_or_404(UserViewingPlan, id=plan_id, user=request.user)
    
    if request.method == 'POST':
        form = ViewingPlanForm(request.POST, instance=plan, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'План просмотра обновлен!')
            return redirect('my_watchlist')
    else:
        form = ViewingPlanForm(instance=plan, user=request.user)
    
    context = {
        'form': form,
        'plan': plan,
    }
    return render(request, 'planner/update_plan.html', context)


@login_required
def delete_viewing_plan(request, plan_id):
    plan = get_object_or_404(UserViewingPlan, id=plan_id, user=request.user)
    
    if request.method == 'POST':
        series_title = plan.series.title
        plan.delete()
        messages.success(request, f'Сериал "{series_title}" удален из вашего списка.')
        return redirect('my_watchlist')
    
    context = {
        'plan': plan,
    }
    return render(request, 'planner/delete_plan.html', context)

@login_required
def analytics(request):
    history_qs = WatchingHistory.objects.filter(user=request.user).select_related('series')

    total_minutes = history_qs.aggregate(total=models.Sum('duration_watched'))['total'] or 0
    total_hours = round(total_minutes / 60, 1)

    chart_url = None
    per_day = []
    per_series = []

    if history_qs.exists():
        data = []
        for item in history_qs:
            data.append({
                'date': item.watched_at.date(),
                'minutes': item.duration_watched,
                'series': item.series.title,
            })
        df = pd.DataFrame(data)

        per_day_df = (
            df.groupby('date')['minutes']
            .sum()
            .reset_index()
        )
        per_day_df['hours'] = per_day_df['minutes'] / 60.0
        per_day = per_day_df.to_dict(orient='records')

        per_series_df = (
            df.groupby('series')['minutes']
            .sum()
            .reset_index()
            .sort_values('minutes', ascending=False)
        )
        per_series_df['hours'] = per_series_df['minutes'] / 60.0
        per_series = per_series_df.head(3).to_dict(orient='records')

        plt.figure(figsize=(8, 4))
        plt.plot(per_day_df['date'], per_day_df['hours'], marker='o')
        plt.title('Часы просмотра по дням')
        plt.xlabel('Дата')
        plt.ylabel('Часы')
        plt.grid(True)
        plt.tight_layout()

        charts_dir = os.path.join(settings.MEDIA_ROOT, 'charts')
        os.makedirs(charts_dir, exist_ok=True)

        chart_path = os.path.join(charts_dir, f'user_{request.user.id}_daily_hours.png')
        plt.savefig(chart_path)
        plt.close()

        chart_url = settings.MEDIA_URL + f'charts/user_{request.user.id}_daily_hours.png'

    context = {
        'total_hours': total_hours,
        'total_entries': history_qs.count(),
        'per_day': per_day,
        'per_series': per_series,
        'chart_url': chart_url,
    }
    return render(request, 'planner/analytics.html', context)

@login_required
@require_POST
def add_watching_session(request, plan_id):
    plan = get_object_or_404(UserViewingPlan, id=plan_id, user=request.user)

    episodes_str = request.POST.get('episodes')
    if not episodes_str:
        messages.error(request, 'Укажите, сколько эпизодов вы посмотрели.')
        return redirect('my_watchlist')

    try:
        episodes_count = int(episodes_str)
    except ValueError:
        messages.error(request, 'Нужно ввести целое число эпизодов.')
        return redirect('my_watchlist')

    if episodes_count <= 0:
        messages.error(request, 'Количество эпизодов должно быть больше нуля.')
        return redirect('my_watchlist')

    old_episode = plan.last_episode_watched
    new_episode = old_episode + episodes_count

    if new_episode >= plan.series.total_episodes:
        new_episode = plan.series.total_episodes
        plan.status = 'completed'
    plan.last_episode_watched = new_episode
    plan.save()

    avg_duration = plan.series.average_episode_duration or 45
    total_minutes = episodes_count * avg_duration

    WatchingHistory.objects.create(
        user=request.user,
        series=plan.series,
        episode=None,
        duration_watched=total_minutes,
    )

    messages.success(
        request,
        f'Добавлено {episodes_count} эпизодов ({total_minutes} мин) для "{plan.series.title}". '
        f'Прогресс: {old_episode} → {new_episode}/{plan.series.total_episodes}'
    )
    return redirect('my_watchlist')
