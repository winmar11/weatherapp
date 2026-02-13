from __future__ import annotations

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand
from django.utils import timezone as dj_timezone

from core.views import fetch_weather, alert_should_trigger, send_alert_email
from core.models import AlertHistory, AlertPreference, UserSetting


class Command(BaseCommand):
    help = "Process active weather alerts for all users."

    def handle(self, *args, **options):
        alerts = AlertPreference.objects.filter(is_active=True).select_related('user')
        if not alerts.exists():
            self.stdout.write("No active alerts.")
            return

        allowed_usernames = {u.strip() for u in django_settings.ALERT_ALLOWED_USERNAMES if u.strip()}
        allowed_emails = {e.strip().lower() for e in django_settings.ALERT_ALLOWED_EMAILS if e.strip()}
        restrict_alerts = bool(allowed_usernames or allowed_emails)

        email_configured = bool(
            django_settings.EMAIL_HOST
            and django_settings.EMAIL_HOST_USER
            and django_settings.EMAIL_HOST_PASSWORD
        )
        if not email_configured:
            self.stdout.write(
                "Email is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to send Gmail alerts."
            )

        weather_cache: dict[str, dict | None] = {}
        user_settings_cache: dict[int, UserSetting] = {}
        processed = 0
        triggered = 0
        errors = 0
        skipped = 0

        for alert in alerts:
            user = alert.user
            if not user.is_active:
                skipped += 1
                continue

            if restrict_alerts:
                email = (user.email or "").strip().lower()
                if (user.username not in allowed_usernames) and (email not in allowed_emails):
                    skipped += 1
                    continue

            if user.id not in user_settings_cache:
                user_settings_cache[user.id] = UserSetting.objects.get_or_create(user=user)[0]
            if not user_settings_cache[user.id].enable_all_alerts:
                skipped += 1
                continue

            city = (alert.city or "").strip()
            if not city:
                skipped += 1
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
                skipped += 1
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
                if not email_configured:
                    errors += 1
                else:
                    if not (user.email or "").strip():
                        errors += 1
                    else:
                        sent, _note = send_alert_email(
                            user,
                            query_city,
                            temp if temp is not None else 0,
                            condition_desc,
                        )
                        if sent:
                            latest_history = AlertHistory.objects.filter(alert=alert).latest('triggered_at')
                            latest_history.email_sent = True
                            latest_history.save()
                        else:
                            errors += 1

            self.stdout.write(f"Alert triggered for {user.username} in {city}: {reason}")

        self.stdout.write(
            f"Processed {processed} alerts. Triggered {triggered}. Skipped {skipped}. Errors {errors}."
        )
