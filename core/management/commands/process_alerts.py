from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone as dj_timezone

from core.views import fetch_weather, alert_should_trigger, send_alert_email
from core.models import AlertHistory, AlertPreference


class Command(BaseCommand):
    help = "Process active weather alerts for all users."

    def handle(self, *args, **options):
        # Auto-activate any alert that opted into email alerts
        AlertPreference.objects.filter(email_alerts=True, is_active=False).update(is_active=True)

        total_alerts = AlertPreference.objects.count()
        total_active = AlertPreference.objects.filter(is_active=True).count()
        self.stdout.write(f"Total alerts: {total_alerts}. Active alerts: {total_active}.")
        self.stdout.write(
            f"Allowlist usernames: {settings.ALERT_ALLOWED_USERNAMES or 'ALL'}. "
            f"Allowlist emails: {settings.ALERT_ALLOWED_EMAILS or 'ALL'}."
        )

        alerts = AlertPreference.objects.filter(is_active=True).select_related('user')
        if settings.ALERT_ALLOWED_USERNAMES:
            alerts = alerts.filter(user__username__in=settings.ALERT_ALLOWED_USERNAMES)
        if settings.ALERT_ALLOWED_EMAILS:
            alerts = alerts.filter(user__email__in=settings.ALERT_ALLOWED_EMAILS)
        if not alerts.exists():
            self.stdout.write("No active alerts after allowlist filtering.")
            return

        weather_cache: dict[str, dict | None] = {}
        processed = 0
        triggered = 0
        errors = 0

        for alert in alerts:
            city = (alert.city or "").strip()
            if not city:
                continue
            query_city = city
            if alert.country:
                query_city = f"{city},{alert.country}"

            if query_city not in weather_cache:
                payload, error = fetch_weather(query_city)
                if error:
                    weather_cache[query_city] = None
                    errors += 1
                else:
                    weather_cache[query_city] = payload

            payload = weather_cache.get(query_city)
            if not payload:
                continue

            weather = payload.get('weather', [{}])[0] or {}
            main = payload.get('main', {}) or {}
            temp = main.get('temp')
            condition_desc = weather.get('description') or weather.get('main') or ""

            should_trigger, reason = alert_should_trigger(alert, temp, condition_desc)
            processed += 1
            if not should_trigger:
                continue

            alert.last_triggered = dj_timezone.now()
            alert.save(update_fields=['last_triggered'])
            AlertHistory.objects.create(
                alert=alert,
                temperature=temp if temp is not None else 0,
                email_sent=False,
            )
            triggered += 1

            if alert.email_alerts:
                sent, _note = send_alert_email(
                    alert.user,
                    query_city,
                    temp if temp is not None else 0,
                    condition_desc,
                )
                if sent:
                    latest_history = AlertHistory.objects.filter(alert=alert).latest('triggered_at')
                    latest_history.email_sent = True
                    latest_history.save()

            self.stdout.write(f"Alert triggered for {alert.user.username} in {city}: {reason}")

        self.stdout.write(
            f"Processed {processed} alerts. Triggered {triggered}. Errors {errors}."
        )
