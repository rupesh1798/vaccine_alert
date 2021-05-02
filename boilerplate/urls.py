'''care URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
'''
from django.urls import include, path, re_path

urlpatterns = [
    path('vaccine/', include('vaccine.urls')),
]

handler400 = 'commons.views.http_bad_request_view'
handler403 = 'commons.views.http_forbidden_view'
handler404 = 'commons.views.http_not_found_view'
handler500 = 'commons.views.http_server_error_view'
