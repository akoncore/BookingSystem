#REST models
from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    CharField,
    EmailField,
    ValidationError
)

#Django Models
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

#Project Models
from auths.models import CustomUser


class RegisterSerializer(ModelSerializer):
    password = CharField(
        write_only = True,
        required = True,
        validators = [validate_password],
    )
    password1 = CharField(
        write_only = True,
        required = True,
    )
    
    class Meta:
        """Class meta
        """
        
        model = CustomUser
        fields = [
            'email','full_name','password','password1'
        ]
        extra_kwargs = {
            'email':{'required':True},
            'full_name':{'required':True},
        }
    
    
    def validate_email(self,value:str)->str:
        """Validate email uniqueness
        """
        if CustomUser.objects.filter(email=value).exists():
            raise ValueError("Email is already in use")
        return value.lower()
    
    
    def validate_full_name(self,value:str)->str:
        """Validate full name
        """
        if not value.strip():
            raise ValueError("Full name cannot be empty")
        elif len(value.strip())<2:
            raise ValueError("The full name must contain at least 2 characters")
        return value.title()
    
    
    def validate(self, attrs):
        """validate for password"""
        
        if attrs['password'] != attrs['password1']:
            raise ValueError({
                'password1':"Not correct"
            })
        return attrs
    
    
    def create(self, validated_data):
        """
        Create new user
        """
        validated_data.pop('password1')
        user = CustomUser.objects.create_user(**validated_data)
        user.save()
        return user
    
    
class LoginSerializers(Serializer):
    """
    User login Serializers
    """
    email = EmailField()
    password = CharField(write_only = True)
    
    
    def validate_email(self,value):
        """Validate email"""
        return value.lower().strip()
    
    
    def validate(self,attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            
            user = authenticate(
                request=self.context.get('request'),
                username = email,
                password = password
            )
            if not user:
                raise ValidationError({
                    'message':'There is not user'
                })
            if not user.is_active:
                raise ValidationError({
                    'message':'User is a deactivate'
                })
            attrs['user'] = user
            return attrs
        else:
            raise ValidationError({
                'message':'Error not email or not password'
            })
    

class UserProfileSerializers(ModelSerializer):
    """
    User profile serializers
    """
    
    class Meta:
        model = CustomUser
        fields = [
            'email','full_name','is_active'
        ]
        read_only_fields = ['id', 'email', 'is_active']


class UserUpdateProfileSerializers(ModelSerializer):
    """
    Update user profile serializers
    """
    
    model = CustomUser
    fields = ['full_name',]
    

    