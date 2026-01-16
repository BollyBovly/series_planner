from django.contrib import admin
from .models import Series, Episode, UserViewingPlan, WatchingHistory, UserSeriesRating


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ['title', 'total_seasons', 'total_episodes', 'rating', 'release_year', 'created_at']
    list_filter = ['release_year', 'created_at']
    search_fields = ['title', 'description', 'genres']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ['series', 'season_number', 'episode_number', 'title', 'duration']
    list_filter = ['series', 'season_number']
    search_fields = ['title', 'series__title']
    ordering = ['series', 'season_number', 'episode_number']


@admin.register(UserViewingPlan)
class UserViewingPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'series', 'status', 'last_season_watched', 'last_episode_watched', 'episodes_per_day', 'started_at']
    list_filter = ['status', 'started_at']
    search_fields = ['user__username', 'series__title']
    readonly_fields = ['started_at', 'updated_at']


@admin.register(WatchingHistory)
class WatchingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'series', 'episode', 'watched_at', 'duration_watched']
    list_filter = ['watched_at']
    search_fields = ['user__username', 'series__title']
    readonly_fields = ['watched_at']


@admin.register(UserSeriesRating)
class UserSeriesRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'series', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'series__title']
    readonly_fields = ['created_at']
