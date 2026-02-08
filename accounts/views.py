from django.shortcuts import render
from .serializers import SignUpSerializer
from rest_framework.generics import CreateAPIView
from .models import CustomUser
# Create your views here.

class SignUpView(CreateAPIView):
    serializer_class = SignUpSerializer
    queryset = CustomUser
    
