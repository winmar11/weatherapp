from django.core.mail import send_mail
from django.conf import settings
from core.models import AlertHistory

def trigger_weather_alert(alert_pref, temperature):
    subject = f"⚠ Weather Alert: {alert_pref.city}"
    message = (
        f"Hi {alert_pref.user.username},\n\n"
        f"Weather alert triggered for {alert_pref.city}.\n"
        f"Current temperature: {temperature}°C\n\n"
        f"Please take necessary precautions.\n"
        f"- Weather forecast"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [alert_pref.user.email],
            fail_silently=False,
        )

        AlertHistory.objects.create(
            alert=alert_pref,
            temperature=temperature,
            email_sent=True
        )

        print("✅ Weather alert email sent")

    except Exception as e:
        AlertHistory.objects.create(
            alert=alert_pref,
            temperature=temperature,
            email_sent=False
        )

        print("❌ Email failed:", e)
