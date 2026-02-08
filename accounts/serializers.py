from rest_framework import serializers
from .models import CODE_VERIFY, CodeVerify, CustomUser, DONE, VIA_EMAIL, VIA_PHONE
from rest_framework.exceptions import ValidationError
from baseapp.utility import check_email_or_phone
from baseapp.utility import send_sms, send_email_code 

class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user_auth_type = serializers.CharField(read_only=True)
    user_status = serializers.CharField(read_only=True)
    
    email_phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'user_auth_type', 'user_status', 'email_phone_number']

    def validate(self, data):
        user_input = data.get('email_phone_number')
        check_user = check_email_or_phone(user_input=user_input)

        if check_user == 'email':
            if CustomUser.objects.filter(email=user_input).exists():
                raise ValidationError({"email_phone_number": "Bu email orqali ro'yxatdan o'tilgan."})
            data['email'] = user_input
            data['user_auth_type'] = VIA_EMAIL
        
        elif check_user == 'phone':
            if CustomUser.objects.filter(phone=user_input).exists():
                raise ValidationError({"email_phone_number": "Bu telefon raqam orqali ro'yxatdan o'tilgan."})
            data['phone'] = user_input
            data['user_auth_type'] = VIA_PHONE
        
        else:
            raise ValidationError({"email_phone_number": "Iltimos to'g'ri email yoki telefon raqam kiriting."})
        
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create(
            email=validated_data.get('email'),
            phone=validated_data.get('phone'),
            user_auth_type=validated_data.get('user_auth_type'),
            user_status=CODE_VERIFY 
        )
        
        import random
        code = str(random.randint(100000, 999999))
        
        CodeVerify.objects.create(
            user=user,
            code=code,
            auth_type=validated_data.get('user_auth_type')
        )
        
        if user.user_auth_type == VIA_EMAIL:
            print(f"EMAIL YUBORILDI: {user.email} -> Kod: {code}")
            send_email_code(user.email, code)
        else:
            print(f"SMS YUBORILDI: {user.phone} -> Kod: {code}")
            send_sms(user.phone, code)
            
        return user
    
    
    