from django.conf import settings
from django.db import models
from django.utils import timezone

class WeatherSearch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weather_searches'
    )
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=80, blank=True)
    temperature_c = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    humidity = models.PositiveIntegerField(null=True, blank=True)
    wind_speed_kph = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    condition_main = models.CharField(max_length=80, blank=True)
    condition_description = models.CharField(max_length=160, blank=True)
    icon_code = models.CharField(max_length=10, blank=True)
    searched_at = models.DateTimeField(auto_now_add=True)
    is_deleted_by_user = models.BooleanField(default=False)
    api_payload = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-searched_at']

    def __str__(self) -> str:
        return f"{self.city} ({self.user})"


class AlertPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alert_preferences'
    )
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=80, blank=True)
    temperature_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    condition_alerts = models.BooleanField(default=True)
    email_alerts = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'city', 'country']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.city}"


class AlertHistory(models.Model):
    alert = models.ForeignKey(
        AlertPreference, on_delete=models.CASCADE, related_name='trigger_history'
    )
    temperature = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Added default
    triggered_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-triggered_at']

    def __str__(self) -> str:
        return f"Alert triggered for {self.alert.city} at {self.triggered_at}"


class SavedLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_locations'
    )
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=80, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    favorite = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'city']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.city}"


class UserSetting(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settings'
    )
    temperature_unit = models.CharField(
        max_length=10,
        choices=[('metric', 'Celsius (C)'), ('imperial', 'Fahrenheit (F)')],
        default='metric'
    )
    dark_mode = models.BooleanField(default=True)
    enable_all_alerts = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.user.username} Settings"
