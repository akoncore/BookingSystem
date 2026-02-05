from typing import Any
from django.db import models
from django.db.models import CharField, EmailField, BooleanField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError


# User Roles
ROLE = {
    'CLIENT': 'client',
    'ADMIN': 'admin',
    'MASTER': 'master',
}


class CustomUserManager(BaseUserManager):
    """User Manager - handles user creation"""
    
    def __obtain_user_instance(
        self,
        email: str,
        full_name: str,
        role: str = 'client',
        **kwargs,
    ) -> 'CustomUser':
        """Private method to create user instance"""
        if not email:
            raise ValidationError(
                message="The Email must be set",
                code="email_not_set"
            )
        if not full_name:
            raise ValidationError(
                message="The Full Name must be set",
                code="full_name_not_set"
            )
        
        new_user: 'CustomUser' = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            role=role,
            **kwargs,
        )
        return new_user
    
    def create_user(
        self,
        email: str,
        full_name: str,
        password: str,
        role: str = 'client',
        **kwargs: dict[str, Any]
    ) -> 'CustomUser':
        """Create and save regular user"""
        new_user = self.__obtain_user_instance(
            email=email,
            full_name=full_name,
            role=role,
            **kwargs,
        )
        new_user.set_password(password)
        new_user.save(using=self._db)
        return new_user
    
    def create_superuser(
        self,
        email: str,
        full_name: str,
        password: str,
        **kwargs: dict[str, Any]
    ) -> 'CustomUser':
        """Create and save superuser (Admin)"""
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('role', ROLE['ADMIN'])
        
        if kwargs.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if kwargs.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(
            email=email,
            full_name=full_name,
            password=password,
            **kwargs
        )


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model
    
    Roles:
    - CLIENT: Regular customers
    - ADMIN: Barbershop owners (тиркелгенде таңдайды)
    - MASTER: Barbers (admin бекітеді main app-та)
    """
    
    email = EmailField(
        max_length=255,
        unique=True,
        verbose_name="Email Address",
        help_text="User email address",
        db_index=True
    )
    full_name = CharField(
        max_length=150,
        verbose_name="Full Name",
        help_text="User full name",
    )
    phone = CharField(
        max_length=20,
        verbose_name="Phone Number",
        help_text="Contact phone number",
        blank=True,
        null=True
    )
    is_active = BooleanField(
        default=True,
        verbose_name="Is Active"
    )
    is_staff = BooleanField(
        default=False,
        verbose_name="Is Staff"
    )
    role = CharField(
        max_length=20,
        choices=[
            (ROLE['CLIENT'], 'Client'),
            (ROLE['ADMIN'], 'Admin'),
            (ROLE['MASTER'], 'Master')
        ],
        default=ROLE['CLIENT'],
        verbose_name="Role",
        help_text="User role in the system"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    REQUIRED_FIELDS = ["full_name"]
    USERNAME_FIELD = 'email'
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == ROLE['ADMIN']
    
    @property
    def is_master(self):
        """Check if user is master"""
        return self.role == ROLE['MASTER']
    
    @property
    def is_client(self):
        """Check if user is client"""
        return self.role == ROLE['CLIENT']