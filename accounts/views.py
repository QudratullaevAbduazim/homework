from django.shortcuts import render
from .serializers import SignUpSerializer
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

