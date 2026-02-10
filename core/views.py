from __future__ import annotations
from datetime import datetime, timezone, timedelta
import requests
import os

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone as dj_timezone
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AlertPreferenceForm, RegisterForm, UserEditForm, WeatherSearchForm
from .models import AlertPreference, WeatherSearch, AlertHistory, SavedLocation, UserSetting

# --- Helper Functions (Weather API) ---

def fetch_weather(city: str) -> tuple[dict | None, str | None]:
    """Fetches current weather with caching logic."""
    api_key = django_settings.OPENWEATHERMAP_API_KEY
    if not api_key:
        return None, "API Key is missing in settings."

    # Sanitize cache key to avoid memcached issues with special characters
    import re
    safe_city = re.sub(r'[^a-zA-Z0-9_-]', '_', city.lower().strip())
    cache_key = f"weather_{safe_city}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data, None

    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'q': city, 'appid': api_key, 'units': 'metric'}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            cache.set(cache_key, data, 600)
            return data, None
        elif response.status_code == 404:
            return None, f"City '{city}' not found."
        return None, "Weather service error."
    except requests.RequestException:
        return None, "Network error."

def fetch_forecast(city: str) -> tuple[dict | None, str | None]:
    """Fetches 5-day forecast."""
    api_key = django_settings.OPENWEATHERMAP_API_KEY
    url = 'https://api.openweathermap.org/data/2.5/forecast'
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        return None, "Forecast unavailable."
    except requests.RequestException:
        return None, "Network error."

def convert_temperature(temp_c: float | int | None, unit: str) -> float | None:
    if temp_c is None:
        return None
    if unit == 'imperial':
        return round((float(temp_c) * 9 / 5) + 32, 1)
    return round(float(temp_c), 1)

def build_five_day_forecast(
    forecast: dict | None,
    unit: str = 'metric',
    target_hours: tuple[int, ...] = (9, 15, 21),
) -> list[dict]:
    """Return 5 daily forecast snapshots with multiple times per day."""
    if not forecast:
        return []

    items = forecast.get('list', [])
    if not items:
        return []

    tz_offset = forecast.get('city', {}).get('timezone', 0)
    local_tz = timezone(timedelta(seconds=tz_offset))

    grouped: dict[str, list[tuple[datetime, dict]]] = {}
    for entry in items:
        dt = entry.get('dt')
        if not dt:
            continue
        dt_obj = datetime.fromtimestamp(dt, tz=local_tz)
        date_key = dt_obj.date().isoformat()
        grouped.setdefault(date_key, []).append((dt_obj, entry))

    results: list[dict] = []
    for date_key in sorted(grouped.keys()):
        day_entries = grouped[date_key]
        if not day_entries:
            continue
        slots: list[dict] = []
        used_indices: set[int] = set()
        for target_hour in target_hours:
            ranked = sorted(
                enumerate(day_entries),
                key=lambda pair: (abs(pair[1][0].hour - target_hour), pair[0] in used_indices),
            )
            if not ranked:
                continue
            idx, (chosen_dt, chosen) = ranked[0]
            used_indices.add(idx)
            weather = chosen.get('weather', [{}])[0]
            main = chosen.get('main', {})
            slots.append({
                'label': chosen_dt.strftime('%I %p').lstrip('0'),
                'time': chosen_dt.strftime('%I:%M %p').lstrip('0'),
                'temp': convert_temperature(main.get('temp'), unit),
                'desc': weather.get('description', ''),
                'icon': weather.get('icon', ''),
            })
        results.append({
            'date': day_entries[0][0].strftime('%a, %b %d'),
            'slots': slots,
        })
        if len(results) >= 5:
            break

    return results

# --- Helper Functions for Alerts ---

def alert_should_trigger(alert: AlertPreference, temp: float | None, condition_desc: str) -> tuple[bool, str]:
    """Check if an alert should trigger based on severe weather conditions only."""
    if not alert.is_active:
        return False, "Alert is inactive"

    # Only trigger on severe weather conditions if condition_alerts is enabled
    if alert.condition_alerts and condition_desc:
        # Trigger on severe weather conditions (excluding rain as it's not severe)
        severe_conditions = ['thunderstorm', 'snow', 'mist', 'fog', 'haze', 'dust', 'sand', 'ash', 'squall', 'tornado']
        if any(cond in condition_desc.lower() for cond in severe_conditions):
            return True, f"Severe weather condition: {condition_desc}"

    return False, "No severe weather conditions met"

def send_alert_email(user, city: str, temp: float, condition: str) -> tuple[bool, str]:
    """Send alert email to user."""
    try:
        subject = f"Weather Alert for {city}"
        message = f"""
        Weather Alert Triggered!

        Location: {city}
        Temperature: {temp}°C
        Condition: {condition}

        This is an automated alert from Weather Forecast.
        """
        send_mail(
            subject,
            message,
            django_settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

# --- Navigation & Auth Views ---

def login_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Registration successful.")
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})

# --- Main Dashboard View (User UI) ---

@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """User Dashboard aligned with HTML template variables."""
    if request.user.is_staff:
        return redirect('admin_dashboard')

    form = WeatherSearchForm()
    alert_form = AlertPreferenceForm()
    weather_data = None  # Key fix: Matching HTML name
    forecast_items = []
    user_settings, _ = UserSetting.objects.get_or_create(user=request.user)
    temp_unit = user_settings.temperature_unit
    unit_symbol = '°F' if temp_unit == 'imperial' else '°C'

    # Get user history
    recent_searches = WeatherSearch.objects.filter(
        user=request.user, 
        is_deleted_by_user=False
    ).order_by('-searched_at')
    
    if request.method == 'POST':
        # 1. Weather Search Action
        if 'city' in request.POST and 'save_alert' not in request.POST:
            form = WeatherSearchForm(request.POST)
            if form.is_valid():
                city = form.cleaned_data['city']
                payload, error = fetch_weather(city)
                
                if payload:
                    weather_main = payload.get('weather', [{}])[0]
                    main_metrics = payload.get('main', {})
                    wind = payload.get('wind', {})
                    
                    # Create and save record
                    new_search = WeatherSearch.objects.create(
                        user=request.user,
                        city=payload.get('name', city),
                        country=payload.get('sys', {}).get('country', ''),
                        temperature_c=main_metrics.get('temp'),
                        humidity=main_metrics.get('humidity'),
                        wind_speed_kph=round(wind.get('speed', 0) * 3.6, 2),
                        condition_main=weather_main.get('main', ''),
                        condition_description=weather_main.get('description', ''),
                        icon_code=weather_main.get('icon', ''),
                        api_payload=payload
                    )
                    
                    # Mapping to dictionary for HTML compatibility
                    weather_data = {
                        'city': new_search.city,
                        'temperature': convert_temperature(new_search.temperature_c, temp_unit),
                        'description': new_search.condition_description,
                        'icon': new_search.icon_code,
                        'humidity': new_search.humidity,
                        'wind_speed': new_search.wind_speed_kph,
                        'feels_like': convert_temperature(main_metrics.get('feels_like'), temp_unit)
                    }
                    
                    forecast, _ = fetch_forecast(city)
                    if forecast:
                        forecast_items = build_five_day_forecast(forecast, unit=temp_unit)
                    
                    messages.success(request, f"Showing weather for {new_search.city}.")
                else:
                    messages.error(request, error)

    # --- PERSISTENCE LOGIC ---
    # Load last search if no new search made in this POST
    if not weather_data and recent_searches.exists():
        last = recent_searches.first()
        weather_data = {
            'city': last.city,
            'temperature': convert_temperature(last.temperature_c, temp_unit),
            'description': last.condition_description,
            'icon': last.icon_code,
            'humidity': last.humidity,
            'wind_speed': last.wind_speed_kph,
            'feels_like': convert_temperature(
                last.api_payload.get('main', {}).get('feels_like') if last.api_payload else None,
                temp_unit,
            )
        }
        forecast, _ = fetch_forecast(last.city)
        if forecast:
            forecast_items = build_five_day_forecast(forecast, unit=temp_unit)

    return render(request, 'dashboard/user_dashboard.html', {
        'form': form,
        'alert_form': alert_form,
        'weather_data': weather_data,      # Match: {% if weather_data %}
        'forecast_items': forecast_items,
        'recent_searches': recent_searches[:10], # Match: {% for search in recent_searches %}
        'all_alerts': AlertPreference.objects.filter(user=request.user),
        'server_time': dj_timezone.localtime(dj_timezone.now()),
        'unit_symbol': unit_symbol,
    })

# --- User Actions ---

@login_required
@require_POST
def delete_search(request, search_id):
    WeatherSearch.objects.filter(id=search_id, user=request.user).update(is_deleted_by_user=True)
    return redirect('dashboard')

@login_required
def clear_history(request):
    """Aligns with the {% url 'clear_history' %} in your HTML."""
    WeatherSearch.objects.filter(user=request.user).update(is_deleted_by_user=True)
    messages.info(request, "Search history cleared.")
    return redirect('dashboard')

@login_required
@require_POST
def create_alert(request):
    """Aligns with the {% url 'create_alert' %} in your HTML."""
    city = request.POST.get('city')
    threshold = request.POST.get('temperature_threshold')
    
    AlertPreference.objects.update_or_create(
        user=request.user,
        city=city,
        defaults={
            'temperature_threshold': threshold if threshold else None,
            'condition_alerts': 'condition_alerts' in request.POST,
            'email_alerts': 'email_alerts' in request.POST,
            'is_active': True,
        }
    )
    messages.success(request, f"Alert for {city} created!")
    return redirect('dashboard')

# --- Admin Views (Stubs) ---

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    # Total searches
    total_searches = WeatherSearch.objects.count()

    # Unique cities
    unique_cities = WeatherSearch.objects.values('city').distinct().count()

    # Today's searches (last 24 hours)
    today = dj_timezone.now() - timedelta(days=1)
    todays_searches = WeatherSearch.objects.filter(searched_at__gte=today).count()

    # Total users
    total_users = User.objects.count()

    # Most searched cities (top 10)
    most_searched = WeatherSearch.objects.values('city').annotate(
        total=Count('city')
    ).order_by('-total')[:10]

    # Recent searches (last 20)
    recent_searches = WeatherSearch.objects.select_related('user').order_by('-searched_at')[:20]

    # Chart data: searches per day for last 7 days
    seven_days_ago = dj_timezone.now() - timedelta(days=7)
    chart_data = WeatherSearch.objects.filter(searched_at__gte=seven_days_ago).annotate(
        date=TruncDate('searched_at')
    ).values('date').annotate(count=Count('id')).order_by('date')

    chart_labels = [entry['date'].strftime('%b %d') for entry in chart_data]
    chart_values = [entry['count'] for entry in chart_data]

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_searches': total_searches,
        'unique_cities': unique_cities,
        'todays_searches': todays_searches,
        'total_users': total_users,
        'most_searched': most_searched,
        'recent_searches': recent_searches,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    })

@user_passes_test(lambda u: u.is_staff)
def manage_users(request):
    users = User.objects.all()
    return render(request, 'dashboard/admin_manage_users.html', {'users': users})

@user_passes_test(lambda u: u.is_staff)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} has been updated.")
            return redirect('manage_users')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'dashboard/admin_edit_user.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
@require_POST
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {status}.")
    return redirect('manage_users')

@user_passes_test(lambda u: u.is_staff)
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
    else:
        user.delete()
        messages.success(request, f"User {user.username} has been deleted.")
    return redirect('manage_users')

@user_passes_test(lambda u: u.is_staff)
def search_history(request):
    searches = WeatherSearch.objects.select_related('user').filter(is_deleted_by_user=False).order_by('-searched_at')
    return render(request, 'dashboard/admin_search_history.html', {'searches': searches})

@user_passes_test(lambda u: u.is_staff)
def delete_search_admin(request, search_id): return HttpResponse("Admin Delete Search")

@user_passes_test(lambda u: u.is_staff)
def clear_search_history(request): return HttpResponse("Admin Clear History")

# --- User Feature Views ---

@login_required
def saved_locations(request):
    """Display user's saved locations."""
    locations = SavedLocation.objects.filter(user=request.user, favorite=True).order_by('-created_at')
    return render(request, 'dashboard/saved_locations.html', {'saved_locations': locations})

@login_required
@require_POST
def add_saved_location(request):
    """Add a new saved location."""
    city = request.POST.get('city', '').strip()
    country = request.POST.get('country', '').strip()

    if not city:
        messages.error(request, "City is required.")
        return redirect('saved_locations')

    # Fetch weather to get coordinates and canonical city name
    payload, error = fetch_weather(city)
    if not payload:
        messages.error(request, f"Could not add {city}: {error}")
        return redirect('saved_locations')

    # Use the canonical city name from the API
    canonical_city = payload.get('name', city.title())
    canonical_country = payload.get('sys', {}).get('country', country)

    # Check if location already exists
    existing_location = SavedLocation.objects.filter(
        user=request.user,
        city__iexact=canonical_city
    ).first()

    if existing_location:
        if existing_location.favorite:
            messages.warning(request, f"{canonical_city} is already in your saved locations.")
            return redirect('saved_locations')
        else:
            # Re-favorite the unfavorited location
            existing_location.favorite = True
            existing_location.save()
            messages.success(request, f"{canonical_city} re-added to saved locations.")
            return redirect('saved_locations')

    # Create new saved location
    SavedLocation.objects.create(
        user=request.user,
        city=canonical_city,
        country=canonical_country,
        latitude=payload.get('coord', {}).get('lat'),
        longitude=payload.get('coord', {}).get('lon'),
    )
    messages.success(request, f"{canonical_city} added to saved locations.")
    return redirect('saved_locations')

@login_required
@require_POST
def toggle_favorite_location(request, location_id):
    """Toggle favorite status of a saved location (unfavorite instead of delete)."""
    location = get_object_or_404(SavedLocation, id=location_id, user=request.user)
    location.favorite = False
    location.save()
    messages.success(request, f"{location.city} unfavorited.")
    return redirect('saved_locations')

@login_required
def manage_alerts(request):
    """Display and manage user's weather alerts."""
    alerts = AlertPreference.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'dashboard/manage_alerts.html', {'alerts': alerts})



@login_required
@require_POST
def toggle_alert(request, alert_id):
    """Toggle alert active status."""
    alert = get_object_or_404(AlertPreference, id=alert_id, user=request.user)
    alert.is_active = not alert.is_active
    alert.save()
    status = "activated" if alert.is_active else "deactivated"
    messages.success(request, f"Alert for {alert.city} {status}.")
    return redirect('manage_alerts')



@login_required
@require_POST
def delete_alert(request, alert_id):
    """Delete an alert."""
    alert = get_object_or_404(AlertPreference, id=alert_id, user=request.user)
    city = alert.city
    alert.delete()
    messages.success(request, f"Alert for {city} deleted successfully.")
    return redirect('manage_alerts')

@login_required
def settings(request):
    """Display user settings."""
    user_settings, created = UserSetting.objects.get_or_create(user=request.user)
    return render(request, 'dashboard/settings.html', {'user_settings': user_settings})

@login_required
@require_POST
def update_settings(request):
    """Update user settings."""
    user_settings, created = UserSetting.objects.get_or_create(user=request.user)

    user_settings.temperature_unit = request.POST.get('temperature_unit', 'metric')
    user_settings.dark_mode = 'dark_mode' in request.POST
    user_settings.enable_all_alerts = 'enable_all_alerts' in request.POST
    user_settings.save()

    messages.success(request, "Settings updated successfully.")
    return redirect('settings')
