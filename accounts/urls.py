from django.urls import path
from . import views
urlpatterns = [
    path('signup/', views.SignUpView.as_view()),
    path('codeverify/', views.CodeVerify.as_view()),

]