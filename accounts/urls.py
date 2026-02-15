from django.urls import path
from . import views
urlpatterns = [
    path('signup/', views.SignUpView.as_view()),
    path('codeverify/', views.VerifyView.as_view()),
    path('getnewcode/', views.GetNewCode.as_view()),
    path('changeinfo/', views.UserChangeInfoView.as_view()),
    path('changephoto/', views.UserChangePhotoView.as_view()),
    path('forgotpassword/', views.ForgotPasswordView.as_view()),
    path('resetpassword/', views.ResetPasswordView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('loginrefresh/', views.LoginRefreshView.as_view()),
    path('login/', views.LoginView.as_view()),


]