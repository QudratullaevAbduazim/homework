from rest_framework import serializers
from .models import CODE_VERIFY, CodeVerify, CustomUser, DONE, VIA_EMAIL, VIA_PHONE, NEW, PHOTO_DONE
from rest_framework.exceptions import ValidationError
from baseapp.utility import check_email_or_phone
from baseapp.utility import send_sms, send_email_code 
from django.db.models import Q
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from baseapp.utility import check_userinputtype
from datetime import datetime, timedelta
from conf.settings import EMAIL_EXPIRATION_TIME, PHONE_EXPIRATION_TIME

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
    
    
    def validate_email_phone_number(self, data):
        user_input = data
        if user_input is None:
            data = {
                'success': False,
                'message': "Email yoki telefon raqam kiritilishi kk"
            }
            raise ValidationError(data)
        
        user = CustomUser.objects.filter(Q(phone_number=user_input)  |Q (email=user_input )).first()
        if user:
            data = {
                'success': False,
                'msg': "Email yoki telefon raqaminggiz bizda mavjud"
            }
            return data
        
        
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(instance.token())
        return data
    
    
class UserChangeSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    def validate_username(self, value):
        user = self.instance
        if CustomUser.objects.filter(username=value).exclude(id=user.id).exists():
            raise ValidationError({"username": "Bu username allaqachon mavjud."})
        if len(value) < 4:
            raise ValidationError({"username": "Username kamida 4 ta belgidan iborat bo'lishi kerak."})
        return value

    def validate_first_name(self, value):
        if len(value) < 2:
            raise ValidationError({"first_name": "Ism juda qisqa."})
        return value

    def validate_last_name(self, value):
        if len(value) < 2:
            raise ValidationError({"last_name": "Familiya juda qisqa."})
        return value

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password or confirm_password:
            if not password or not confirm_password:
                raise ValidationError({
                    "password": "Ikkala parol maydoni ham to‘ldirilishi kerak."
                })

            if password != confirm_password:
                raise ValidationError({
                    "confirm_password": "Parollar mos emas."
                })

            if len(password) < 6:
                raise ValidationError({
                    "password": "Parol kamida 6 ta belgidan iborat bo‘lishi kerak."
                })

        return data

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)

        if validated_data.get("password"):
            instance.set_password(validated_data.get("password"))

        instance.user_status = DONE
        instance.save()
        return instance

    
    
    
class USerChangePhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField()
    
    def update(self, instance, validated_data):
        photo = validated_data.get('photo')
        if photo:
            instance.photo = photo
            instance.user_status = PHOTO_DONE
            instance.save()
            return instance
        else:
            raise ValidationError({"photo": "Rasm yuklanmadi."})
        
    
    
    
class LoginSerializer(TokenObtainPairSerializer):
    
    def __init__(self, instance=None, data=..., **kwargs):
        super(LoginSerializer, self).__init__(instance, data, **kwargs)
             
        self.fields['userinput'] = serializers.CharField(write_only=True, required=True)
        self.fields['username'] = serializers.CharField(read_only=True, required=False)
        
        def auth_validate(self, data):
            userinput = data.get('userinput')
            password = data.get('password')
            
            usertype = check_userinputtype(userinput)
            if usertype == 'username':
                username = userinput
            elif usertype == 'email':
                username = CustomUser.objects.filter(email__iexact=userinput).first()
                self.get_user(user)
                username = user.username
            elif usertype == 'phone':
                username = CustomUser.objects.filter(phone_number=userinput).first()
                self.get_user(user)
                username = user.username
            else:
                raise ValidationError({"userinput": "Iltimos, email, telefon raqam yoki username kiriting."})
            
            authenticated_kwargs = {
                self.username_field: username,
                'password': password
            }
            user = authenticate(**authenticated_kwargs)
            if user and user.user_status in [NEW, CODE_VERIFY]:
                raise ValidationError({"userinput": "Siz hali tasdiqlash jarayonini yakunlamagansiz."})
            
            if not user:
                raise ValidationError({"userinput": "Noto'g'ri email, telefon raqam yoki username yoki parol."})
            self.user = user
            return data
            
            
            
            def get_user(self, user):
                if not user:
                    raise ValidationError({"userinput": "Bunday foydalanuvchi topilmadi."})
                return user
            
            def validate(self, data):
                data = self.auth_validate(data)
                data = self.user_token()
                data['user_status'] = self.user.user_status
                return data
            
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.refresh_token = attrs.get("refresh")

        if not self.refresh_token:
            raise serializers.ValidationError({
                "refresh": "Refresh token yuborilishi kerak."
            })

        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.refresh_token)
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError({
                "refresh": "Token noto‘g‘ri yoki eskirgan."
            })
          
            
class ForgotPasswordSerializer(serializers.Serializer):
    auth_type = serializers.ChoiceField(choices=[VIA_EMAIL, VIA_PHONE])
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)

    def validate(self, attrs):
        auth_type = attrs.get("auth_type")
        email = attrs.get("email")
        phone = attrs.get("phone")

        if auth_type == VIA_EMAIL:
            if not email:
                raise serializers.ValidationError("Email kiritilishi shart")
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Bunday email mavjud emas")

        elif auth_type == VIA_PHONE:
            if not phone:
                raise serializers.ValidationError("Telefon raqam kiritilishi shart")
            try:
                user = CustomUser.objects.get(phone=phone)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Bunday telefon mavjud emas")

        attrs["user"] = user
        attrs["auth_type"] = auth_type
        return attrs
    

class ResetPasswordSerializer(serializers.Serializer):
    auth_type = serializers.ChoiceField(choices=[VIA_EMAIL, VIA_PHONE])
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    code = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        auth_type = attrs.get("auth_type")
        email = attrs.get("email")
        phone = attrs.get("phone")
        code = attrs.get("code")

        if auth_type == VIA_EMAIL:
            user = CustomUser.objects.filter(email=email).first()
        else:
            user = CustomUser.objects.filter(phone=phone).first()

        if not user:
            raise serializers.ValidationError("Foydalanuvchi topilmadi")

        verify = CodeVerify.objects.filter(
            user=user,
            code=code,
            auth_type=auth_type,
            is_active=False
        ).first()

        if not verify:
            raise serializers.ValidationError("Kod noto‘g‘ri yoki eskirgan")

        attrs["user"] = user
        attrs["verify"] = verify
        return attrs


