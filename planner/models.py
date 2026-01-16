from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Series(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    total_seasons = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Количество сезонов"
    )
    total_episodes = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Всего эпизодов"
    )
    average_episode_duration = models.IntegerField(
        default=45,
        validators=[MinValueValidator(1)],
        verbose_name="Средняя длительность эпизода (мин)"
    )
    genres = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Жанры"
    )
    poster_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL постера"
    )
    tmdb_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="TMDB ID"
    )
    rating = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Рейтинг TMDB"
    )
    release_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Год выхода"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Сериал"
        verbose_name_plural = "Сериалы"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_total_duration_minutes(self):
        return self.total_episodes * self.average_episode_duration

    def get_total_duration_hours(self):
        return round(self.get_total_duration_minutes() / 60, 1)


class Episode(models.Model):
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name='episodes',
        verbose_name="Сериал"
    )
    season_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Номер сезона"
    )
    episode_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Номер эпизода"
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Название эпизода"
    )
    duration = models.IntegerField(
        default=45,
        validators=[MinValueValidator(1)],
        verbose_name="Длительность (мин)"
    )
    air_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата выхода"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )

    class Meta:
        verbose_name = "Эпизод"
        verbose_name_plural = "Эпизоды"
        ordering = ['series', 'season_number', 'episode_number']
        unique_together = ['series', 'season_number', 'episode_number']

    def __str__(self):
        return f"{self.series.title} - S{self.season_number:02d}E{self.episode_number:02d}"

    def get_episode_code(self):
        return f"S{self.season_number:02d}E{self.episode_number:02d}"


class UserViewingPlan(models.Model):
    STATUS_CHOICES = [
        ('watching', 'Смотрю'),
        ('completed', 'Завершено'),
        ('paused', 'На паузе'),
        ('planning', 'В планах'),
        ('dropped', 'Брошено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewing_plans')
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='user_plans')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    last_season_watched = models.IntegerField(default=0)
    last_episode_watched = models.IntegerField(default=0)
    
    episodes_per_day = models.IntegerField(default=2, help_text="Сколько эпизодов смотрите в день")
    
    daily_hours_available = models.DecimalField(max_digits=4, decimal_places=1, default=2.0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'series')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.series.title} ({self.get_status_display()})"
    
    def get_episodes_watched(self):
        has_episodes = Episode.objects.filter(series=self.series).exists()
        
        if has_episodes:
            episodes = Episode.objects.filter(
                series=self.series,
                season_number__lt=self.last_season_watched
            ).count()
            
            episodes += Episode.objects.filter(
                series=self.series,
                season_number=self.last_season_watched,
                episode_number__lte=self.last_episode_watched
            ).count()
            
            return episodes
        else:
            if self.series.total_seasons > 0 and self.last_season_watched > 0:
                episodes_per_season = self.series.total_episodes / self.series.total_seasons
                
                watched = (self.last_season_watched - 1) * episodes_per_season
                watched += self.last_episode_watched
                return int(watched)
            else:
                return self.last_episode_watched if self.last_episode_watched > 0 else 0

    
    def calculate_remaining_episodes(self):
        watched = self.get_episodes_watched()
        total = self.series.total_episodes
        return max(0, total - watched)
    
    def calculate_completion_days(self):
        remaining = self.calculate_remaining_episodes()
        if self.episodes_per_day > 0:
            return int(remaining / self.episodes_per_day) + (1 if remaining % self.episodes_per_day > 0 else 0)
        return 0
    
    @property
    def estimated_completion_date(self):
        from datetime import timedelta
        days = self.calculate_completion_days()
        return timezone.now() + timedelta(days=days)
    
    def get_progress_percentage(self):
        watched = self.get_episodes_watched()
        total = self.series.total_episodes
        if total > 0:
            return int((watched / total) * 100)
        return 0
    
    def get_recommended_episodes_today(self):
        return self.episodes_per_day



class WatchingHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='watching_history',
        verbose_name="Пользователь"
    )
    episode = models.ForeignKey(
        Episode,
        on_delete=models.CASCADE,
        related_name='watch_records',
        verbose_name="Эпизод",
        blank=True,
        null=True
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name='watch_history',
        verbose_name="Сериал"
    )
    watched_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата просмотра"
    )
    duration_watched = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Минут просмотрено"
    )

    class Meta:
        verbose_name = "Запись просмотра"
        verbose_name_plural = "История просмотра"
        ordering = ['-watched_at']

    def __str__(self):
        ep_code = self.episode.get_episode_code() if self.episode else "N/A"
        return f"{self.user.username} - {ep_code} - {self.watched_at.strftime('%Y-%m-%d')}"


class UserSeriesRating(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='series_ratings',
        verbose_name="Пользователь"
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name='user_ratings',
        verbose_name="Сериал"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Оценка (1-10)"
    )
    review = models.TextField(
        blank=True,
        verbose_name="Отзыв"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата оценки"
    )
    
    class Meta:
        verbose_name = "Оценка пользователя"
        verbose_name_plural = "Оценки пользователей"
        unique_together = ['user', 'series']
    
    def __str__(self):
        return f"{self.user.username} - {self.series.title}: {self.rating}/10"
