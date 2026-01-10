from django.contrib import admin
from .models import Series, Episode, UserViewingPlan, WatchingHistory


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ['title', 'total_seasons', 'total_episodes', 'average_episode_duration', 'get_total_duration_hours', 'created_at']
    list_filter = ['genres', 'created_at']
    search_fields = ['title', 'description', 'genres']
    readonly_fields = ['created_at', 'updated_at', 'tmdb_id']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'poster_url', 'genres')
        }),
        ('Статистика', {
            'fields': ('total_seasons', 'total_episodes', 'average_episode_duration')
        }),
        ('Служебные поля', {
            'fields': ('tmdb_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ['get_episode_code', 'series', 'title', 'duration', 'air_date']
    list_filter = ['series', 'season_number', 'air_date']
    search_fields = ['title', 'series__title', 'description']
    ordering = ['series', 'season_number', 'episode_number']
    
    fieldsets = (
        ('Идентификация', {
            'fields': ('series', 'season_number', 'episode_number')
        }),
        ('Контент', {
            'fields': ('title', 'description', 'duration', 'air_date')
        }),
    )


@admin.register(UserViewingPlan)
class UserViewingPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'series', 'status', 'get_progress_percentage', 'daily_hours_available', 'estimated_completion_date', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'series__title']
    readonly_fields = ['created_at', 'updated_at', 'estimated_completion_date']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Пользователь и сериал', {
            'fields': ('user', 'series', 'status')
        }),
        ('Прогресс', {
            'fields': ('last_season_watched', 'last_episode_watched', 'daily_hours_available')
        }),
        ('Даты', {
            'fields': ('start_date', 'estimated_completion_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WatchingHistory)
class WatchingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'episode', 'series', 'duration_watched', 'watched_at']
    list_filter = ['watched_at', 'series']
    search_fields = ['user__username', 'series__title', 'episode__title']
    readonly_fields = ['watched_at']
    ordering = ['-watched_at']
    date_hierarchy = 'watched_at'
