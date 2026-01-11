from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('series/', views.series_list, name='series_list'),
    path('series/<int:series_id>/', views.series_detail, name='series_detail'),
    path('my-watchlist/', views.my_watchlist, name='my_watchlist'),
    path('add-to-watchlist/<int:series_id>/', views.add_to_watchlist, name='add_to_watchlist'),
    path('update-plan/<int:plan_id>/', views.update_viewing_plan, name='update_plan'),
    path('delete-plan/<int:plan_id>/', views.delete_viewing_plan, name='delete_plan'),
    path('analytics/', views.analytics, name='analytics'),
]