from tokenize import TokenError
from django.shortcuts import render
from baseapp.utility import check_email_or_phone, send_email_code
from .models import CustomUser, CodeVerify
from baseapp.utility import send_sms
from .serializers import LoginSerializer, SignUpSerializer, USerChangePhotoSerializer, UserChangeSerializer
from rest_framework.generics import CreateAPIView
from .models import CustomUser, CodeVerify
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from datetime import datetime
from rest_framework import status
from .models import NEW, CODE_VERIFY, VIA_EMAIL, VIA_PHONE
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework.generics import UpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
# Create your views here.

class SignUpView(CreateAPIView):
    serializer_class = SignUpSerializer
    queryset = CustomUser
    
    
    
    
class VerifyView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    
    
    def post(self, request):
        code = self.request.data.get('code')
        user = request.user
        self.check_code(user, code)

        
        
        data = {
            'status': status.HTTP_200_OK, 
            'user_status': user.user_status,
            'refresh': user.token()['refresh'],
            'accsess': user.token()['accsess']
        }
        
        return Response(data)
                
        
    
    @staticmethod
    def check_code(user, code, self):
        code = CodeVerify.objects.filter(user=user, code=code, is_active=False, expiration_time__gte=datetime.now()).exists()
        
        if not code :
            data = {
                'success': False,
                "msg": "Kod xato "
            }
            raise ValidationError(data)
        
        code.update(is_active=True)
        
        code['is_active'] = True
        if user.user_status == NEW:
            user.user_status = CODE_VERIFY
            user.save()
            
            
        return True
    
    
    


class GetNewCode(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user

        self.check_active_code(user)

        code = user.create_verify_code(user.user_auth_type)

        if user.user_auth_type == VIA_EMAIL:

            send_mail(
                subject="Tasdiqlash kodi",
                message=f"Sizning tasdiqlash kodingiz: {code}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False
            )

        elif user.user_auth_type == VIA_PHONE:
            print(f"SMS kod {user.phone_number} ga yuborildi: {code}")

        return Response({
            'success': True,
            'message': 'Kod yuborildi'
        })

    
    
    
        
    @staticmethod
    def check_active_code(user):
        code = CodeVerify.objects.filter(user=user, code=code, is_active=False, expiration_time__gte=datetime.now()).exists()
        if not code.exists() :
            data = {
                'success': False,
                "msg": "Sizda hali aktiv kod bor "
            }
            raise ValidationError(data)
        
        return True


class UserChangeInfoView(UpdateAPIView):
    serializer_class = UserChangeSerializer
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAuthenticated, ]
    
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': "Ma'lumotlar muvaffaqiyatli yangilandi",
            'user': UserChangeSerializer(self.get_object()).data
        }
        return Response(data)
    
    
    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': "Ma'lumotlar muvaffaqiyatli yangilandi",
            'user': UserChangeSerializer(self.get_object()).data
        }
        return Response(data)
    
    
    
class UserChangePhotoView(APIView):
    serializer_class = USerChangePhotoSerializer
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAuthenticated, ]
    
    def get_object(self):
        return self.request.user
    
    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': "Rasm muvaffaqiyatli yangilandi",
            'user': USerChangePhotoSerializer(self.get_object()).data
        }
        return Response(data)
    
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    

class LogoutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                'success': True,
                'message': "Muvaffaqiyatli logout qilindi"
            }
            return Response(data, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            data = {
                'success': False,
                'message': "Token xato"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            data = {
                'success': False,
                'message': f"Xatolik yuz berdi: {str(e)}"
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LoginRefreshView(APIView):
    permission_classes = [permissions.AllowAny, ]
    def post(self, request):
        refresh_token = self.request.data.get('refresh')
        try:
            token = RefreshToken(refresh_token)
            data = {
                'access': str(token.access_token)
            }
            
            return Response(data, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            data = {
                'success': False,
                'message': "Token xato"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            data = {
                'success': False,
                'message': f"Xatolik yuz berdi: {str(e)}"
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        auth_type = serializer.validated_data["auth_type"]

        import random
        code = str(random.randint(100000, 999999))

        CodeVerify.objects.create(
            user=user,
            code=code,
            auth_type=auth_type
        )

        if auth_type == VIA_EMAIL:
            send_email_code(user.email, code)
        elif auth_type == VIA_PHONE:
            send_sms(user.phone, code)

        return Response({
            "success": True,
            "message": "Tasdiqlash kodi yuborildi"
        })


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        verify = serializer.validated_data["verify"]
        password = serializer.validated_data["password"]

        user.set_password(password)
        user.save()

        verify.is_active = True
        verify.save()

        return Response({
            "success": True,
            "message": "Parol muvaffaqiyatli yangilandi"
        })
