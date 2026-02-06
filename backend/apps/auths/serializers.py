# REST Framework
from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    CharField,
    EmailField,
    ValidationError
)

# Django
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

# Project Models
from .models import CustomUser, ROLE


class RegisterSerializer(ModelSerializer):
    """User Registration Serializer"""
    
    password = CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'email',
            'full_name',
            'phone',
            'role',
            'password',
            'password_confirm'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'full_name': {'required': True},
            'phone': {'required': False},
            'role': {
                'required': False,
                'default': ROLE['CLIENT']
            }
        }
    
    def validate_email(self, value: str) -> str:
        """Validate email uniqueness"""
        email = value.lower().strip()
        
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        
        return email
    
    def validate_full_name(self, value: str) -> str:
        """Validate full name"""
        full_name = value.strip()
        
        if not full_name:
            raise ValidationError(
                "Full name cannot be empty"
            )
        
        if len(full_name) < 2:
            raise ValidationError(
                "Full name must contain at least 2 characters"
            )
        return full_name.title()
    
    def validate_phone(self, value: str) -> str:
        """Validate phone number"""
        if value:
            phone = value.strip()
            if len(phone) < 10:
                raise ValidationError("Phone number must be at least 10 digits")
            return phone
        return value
    
    def validate_role(self, value: str) -> str:
        """
        Validate role based on who is registering:
        - CLIENT and ADMIN can self-register
        - MASTER can only be created by ADMIN
        """
        request = self.context.get('request')
        
        
        if value == ROLE['MASTER']:
            # Check if request exists and user is authenticated
            if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
                raise ValidationError(
                    "Only Admin can create Master accounts. Please login as Admin."
                )
            
            # Check if authenticated user is admin
            if not request.user.is_admin:
                raise ValidationError(
                    "Only Admin can create Master accounts. Your role is insufficient."
                )
        
        
        allowed_roles = [ROLE['CLIENT'], ROLE['ADMIN'], ROLE['MASTER']]
        if value not in allowed_roles:
            raise ValidationError(
                f"Invalid role. Allowed roles: {', '.join(allowed_roles)}"
            )
        
        return value
    
    def validate(self, attrs):
        """Validate passwords match"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise ValidationError({
                'password_confirm': "Passwords do not match"
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        
        user = CustomUser.objects.create_user(**validated_data)
        return user


class LoginSerializer(Serializer):
    """User Login Serializer"""
    
    email = EmailField(required=True)
    password = CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    # Read-only fields (returned after successful login)
    role = CharField(read_only=True)
    full_name = CharField(read_only=True)
    
    def validate_email(self, value: str) -> str:
        """Normalize email"""
        return value.lower().strip()
    
    def validate(self, attrs):
        """Validate user credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise ValidationError("Email and password are required")
        
        # Authenticate user
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        
        if not user:
            raise ValidationError({
                'detail': 'Invalid email or password'
            })
        
        if not user.is_active:
            raise ValidationError({
                'detail': 'User account is deactivated'
            })
        
        # Add user to validated data
        attrs['user'] = user
        attrs['role'] = user.role
        attrs['full_name'] = user.full_name
        
        return attrs


class UserProfileSerializer(ModelSerializer):
    """User Profile Serializer (Read)"""
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'full_name',
            'phone',
            'role',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'email',
            'role',
            'is_active',
            'created_at',
            'updated_at'
        ]


class UserUpdateSerializer(ModelSerializer):
    """User Profile Update Serializer"""
    
    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'phone'
        ]
    
    def validate_full_name(self, value: str) -> str:
        """Validate full name"""
        full_name = value.strip()
        
        if not full_name:
            raise ValidationError("Full name cannot be empty")
        
        if len(full_name) < 2:
            raise ValidationError("Full name must contain at least 2 characters")
        
        return full_name.title()
    
    def validate_phone(self, value: str) -> str:
        """Validate phone number"""
        if value:
            phone = value.strip()
            if len(phone) < 10:
                raise ValidationError("Phone number must be at least 10 digits")
            return phone
        return value


class ChangePasswordSerializer(Serializer):
    """Change Password Serializer"""
    
    old_password = CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        
        if not user.check_password(value):
            raise ValidationError("Old password is incorrect")
        
        return value
    
    def validate(self, attrs):
        """Validate new passwords match"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        if new_password != new_password_confirm:
            raise ValidationError({
                'new_password_confirm': "New passwords do not match"
            })
        
        return attrs
    
    def save(self, **kwargs):
        """Update user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    


    