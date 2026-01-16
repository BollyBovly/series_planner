from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm
from planner.models import UserViewingPlan, WatchingHistory

def register(request):
    if request.user.is_authenticated:
        return redirect('series_list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Аккаунт {username} успешно создан!')
                return redirect('series_list')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    viewing_plans = UserViewingPlan.objects.filter(user=request.user).select_related('series')
    
    total_series = viewing_plans.count()
    watching = viewing_plans.filter(status='watching').count()
    completed = viewing_plans.filter(status='completed').count()
    paused = viewing_plans.filter(status='paused').count()
    planning = viewing_plans.filter(status='planning').count()
    
    total_hours = 0
    for plan in viewing_plans:
        episodes_watched = plan.get_episodes_watched()
        total_hours += (episodes_watched * plan.series.average_episode_duration) / 60
    
    context = {
        'viewing_plans': viewing_plans,
        'stats': {
            'total_series': total_series,
            'watching': watching,
            'completed': completed,
            'paused': paused,
            'planning': planning,
            'total_hours': round(total_hours, 1),
        }
    }
    
    return render(request, 'accounts/profile.html', context)
