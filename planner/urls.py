from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('my-series/', views.series_list, name='series_list'),
    path('series/<int:series_id>/', views.series_detail, name='series_detail'),
    path('add/<int:series_id>/', views.add_to_list, name='add_to_list'),
    path('remove/<int:plan_id>/', views.remove_from_list, name='remove_from_list'),
    path('update/<int:plan_id>/', views.update_progress, name='update_progress'),
    path('watch/<int:plan_id>/<int:season>/<int:episode>/', views.mark_episode_watched, name='mark_episode_watched'),
    path('rate/<int:series_id>/', views.rate_series, name='rate_series'),
    path('statistics/', views.statistics, name='statistics'),
    path('search/', views.search_series, name='search'),
]

