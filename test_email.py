#!/usr/bin/env python
import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_management.settings')
django.setup()

try:
    send_mail(
        'Weather Alert Test',
        'This is a test email to verify Gmail SMTP configuration works.',
        settings.DEFAULT_FROM_EMAIL,
        ['delrosariomarwin06@gmail.com'],
        fail_silently=False,
    )
    print("Test email sent successfully!")
except Exception as e:
    print(f"Failed to send test email: {e}")
