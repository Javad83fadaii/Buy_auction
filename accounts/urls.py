from django.urls import path

from .views import UserLoginView, UserLogoutView, UserPasswordChangeDoneView, UserPasswordChangeView

app_name = 'accounts'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('change-password/', UserPasswordChangeView.as_view(), name='change_password'),
    path(
        'change-password/done/',
        UserPasswordChangeDoneView.as_view(),
        name='change_password_done',
    ),
]
