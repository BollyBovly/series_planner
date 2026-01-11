from django import forms
from .models import UserViewingPlan, Series
from django.core.validators import MinValueValidator, MaxValueValidator


class ViewingPlanForm(forms.ModelForm):
    class Meta:
        model = UserViewingPlan
        fields = ['series', 'daily_hours_available', 'last_season_watched', 'last_episode_watched', 'status']
        widgets = {
            'series': forms.Select(attrs={'class': 'form-select'}),
            'daily_hours_available': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0.1',
                'max': '24',
            }),
            'last_season_watched': forms.NumberInput(attrs={'class': 'form-control'}),
            'last_episode_watched': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
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
        }),
    )
