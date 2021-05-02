from django.urls import include, path
from vaccine.views import manage_states, manage_districts, calendar_pin, calendar_district, register_user, auth

app_name = 'vaccine'


urlpatterns = [
    path('states', manage_states, name='manage_states'),
    path('districts/<state_code>', manage_districts, name='manage_districts'),
    path('calendar/pin', calendar_pin, name='calendar_pin'),
    path('calendar/district', calendar_district, name='calendar_district'),
    path('auth', auth, name='auth'),
    path('register', register_user, name='register_user'),
]
