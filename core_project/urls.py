from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from laundry import views as laundry_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('laundry.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='laundry/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]