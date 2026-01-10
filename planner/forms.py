from django import forms
from .models import UserViewingPlan, Series
from django.core.validators import MinValueValidator, MaxValueValidator


class ViewingPlanForm(forms.ModelForm):
    
    class Meta:
        model = UserViewingPlan
        fields = ['series', 'daily_hours_available', 'last_season_watched', 'last_episode_watched', 'status']
        widgets = {
            'series': forms.Select(attrs={
                'class': 'form-select',
            }),
            'daily_hours_available': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0.1',
                'max': '24',
                'placeholder': '2.0'
            }),
            'last_season_watched': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'last_episode_watched': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'series': 'Сериал',
            'daily_hours_available': 'Часов в день для просмотра',
            'last_season_watched': 'Последний просмотренный сезон',
            'last_episode_watched': 'Последний просмотренный эпизод',
            'status': 'Статус',
        }
        help_texts = {
            'daily_hours_available': 'Сколько часов в день вы планируете смотреть сериал?',
            'last_season_watched': 'Укажите 0, если начинаете с начала',
            'last_episode_watched': 'Укажите 0, если начинаете с начала',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance.pk:
            self.fields['series'].disabled = True
        
        if user:
            existing_series_ids = UserViewingPlan.objects.filter(user=user).values_list('series_id', flat=True)
            self.fields['series'].queryset = Series.objects.exclude(id__in=existing_series_ids)


class TimeCalculatorForm(forms.Form):
    daily_hours = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.1), MaxValueValidator(24.0)],
        initial=2.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'min': '0.1',
            'max': '24',
            'id': 'timeCalculator'
        }),
        label='Часов в день',
        help_text='Сколько часов в день вы можете смотреть?'
    )
