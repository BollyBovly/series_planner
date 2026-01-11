from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from datetime import date, timedelta
from .models import Series, Episode, UserViewingPlan, WatchingHistory
from .forms import ViewingPlanForm, TimeCalculatorForm


def home(request):
    recent_series = Series.objects.all()[:6]
    context = {
        'recent_series': recent_series,
    }
    return render(request, 'planner/home.html', context)


def series_list(request):
    series_queryset = Series.objects.all()
    
    # Поиск
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
