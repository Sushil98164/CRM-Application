
from django.contrib import admin
from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

app_name = 'user_auth'

urlpatterns = [
    path('register/',RegisterView.as_view(), name='register'),
    path('logout/',Logout.as_view(),name = "logout"),
    # path('login/<str:company_code>/', LoginView.as_view(), name='login'),
    # path('', LoginView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    #reset password urls
    path('password-reset/', RestPasswordEmailView.as_view(), name="forget_password"),
    path('reset/<uidb64>/<token>/', NewPasswordView.as_view(template_name="userauth/reset_password.html"), name="password_reset_confirm"),
    path('reset/done/', RestPasswordDoneView.as_view(), name="landing_website_password_reset_complete"),

]