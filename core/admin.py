from django.contrib import admin

from .models import WeatherSearch


@admin.register(WeatherSearch)
class WeatherSearchAdmin(admin.ModelAdmin):
    list_display = (
        'city',
        'country',
        'user',
        'condition_main',
        'temperature_c',
        'humidity',
        'wind_speed_kph',
        'searched_at',
        'is_deleted_by_user',
    )
    list_filter = ('condition_main', 'is_deleted_by_user', 'searched_at')
    search_fields = ('city', 'country', 'user__username', 'user__email')

