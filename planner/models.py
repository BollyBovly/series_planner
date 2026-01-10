from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta, date


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
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='viewing_plans',
        verbose_name="Пользователь"
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name='user_plans',
        verbose_name="Сериал"
    )
    daily_hours_available = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=2.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(24.0)],
        verbose_name="Часов в день"
    )
    last_season_watched = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Последний просмотренный сезон"
    )
    last_episode_watched = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Последний просмотренный эпизод"
    )
    start_date = models.DateField(
        default=date.today,
        verbose_name="Дата начала"
    )
    estimated_completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Планируемая дата завершения"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='watching',
        verbose_name="Статус"
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
        verbose_name = "План просмотра"
        verbose_name_plural = "Планы просмотра"
        unique_together = ['user', 'series']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.series.title}"

    def calculate_remaining_episodes(self):
        total = self.series.total_episodes
        watched_count = self.series.episodes.filter(
            season_number__lt=self.last_season_watched
        ).count()
        watched_count += self.series.episodes.filter(
            season_number=self.last_season_watched,
            episode_number__lte=self.last_episode_watched
        ).count()
        return max(0, total - watched_count)

    def calculate_completion_days(self):
        remaining_episodes = self.calculate_remaining_episodes()
        if remaining_episodes == 0:
            return 0
        
        total_minutes = remaining_episodes * self.series.average_episode_duration
        total_hours = total_minutes / 60
        days_needed = total_hours / float(self.daily_hours_available)
        return round(days_needed)

    def get_progress_percentage(self):
        if self.series.total_episodes == 0:
            return 0
        watched = self.series.total_episodes - self.calculate_remaining_episodes()
        return round((watched / self.series.total_episodes) * 100)

    def save(self, *args, **kwargs):
        if self.daily_hours_available > 0:
            days = self.calculate_completion_days()
            self.estimated_completion_date = date.today() + timedelta(days=days)
        super().save(*args, **kwargs)


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
        verbose_name="Эпизод"
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
        return f"{self.user.username} - {self.episode.get_episode_code()} - {self.watched_at.strftime('%Y-%m-%d')}"
