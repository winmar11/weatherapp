from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path('', views.login_redirect, name='home'),
    path('register/', views.register, name='register'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='auth/login.html', authentication_form=LoginForm),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # USER SEARCH ACTIONS
    path('search/<int:search_id>/delete/', views.delete_search, name='delete_search'),
    # FIX: Binago ang clear_searches -> clear_history para mag-match sa Views at HTML
    path('search/clear/', views.clear_history, name='clear_history'),
    
    # USER ALERT ACTIONS
    # FIX: Dinagdag ito para gumana ang "Save Alert" form sa dashboard
    path('alerts/create/', views.create_alert, name='create_alert'),
    path('alerts/manage/', views.manage_alerts, name='manage_alerts'),
    path('alerts/<int:alert_id>/toggle/', views.toggle_alert, name='toggle_alert'),
    path('alerts/<int:alert_id>/delete/', views.delete_alert, name='delete_alert'),

    # USER SAVED LOCATIONS
    path('locations/', views.saved_locations, name='saved_locations'),
    path('locations/add/', views.add_saved_location, name='add_saved_location'),
    path('locations/<int:location_id>/unfavorite/', views.toggle_favorite_location, name='toggle_favorite_location'),

    # USER SETTINGS
    path('settings/', views.settings, name='settings'),
    path('settings/update/', views.update_settings, name='update_settings'),

    # ADMIN PANEL ROUTES
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.manage_users, name='manage_users'),
    path('admin-panel/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('admin-panel/users/<int:user_id>/toggle/', views.toggle_user_active, name='toggle_user_active'),
    path('admin-panel/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('admin-panel/search-history/', views.search_history, name='search_history'),
    path('admin-panel/search-history/<int:search_id>/delete/', views.delete_search_admin, name='delete_search_admin'),
    path('admin-panel/search-history/clear/', views.clear_search_history, name='clear_search_history'),
]