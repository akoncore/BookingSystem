from typing import Any

#Django Models
from django.db.models import(
    CharField,
    EmailField,
    BooleanField
)
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password



class CustomUserManager(BaseUserManager):
    """Create User"""
    def __obtain_user_instance(
        self,
        email: str,
        full_name: str,
        password: str,
        **kwargs,
    ) -> 'CustomUser':
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
        new_user:'CustomUser' = self.model(
            email = self.normalize_email(email),
            full_name = full_name,
            password = password,
            **kwargs,
        )
        return new_user
    
    # Create regular user
    def create_user(
        self,
        email:str,
        full_name:str,
        password:str,
        **kwargs:dict[str,Any]
    )->'CustomUser':
        new_user = self.__obtain_user_instance(
            email=email,
            full_name = full_name,
            password = password,
            **kwargs,
        )
        new_user.set_password(password)
        new_user.save(using = self.db)
        return new_user
    
    
    #Create superuser
    def create_superuser(
        self,
        email:str,
        full_name:str,
        password:str,
        **kwargs:dict[str,Any]
    )->'CustomUser':
        new_user = self.__obtain_user_instance(
            email=email,
            full_name = full_name,
            password = password,
            is_superuser = True,
            is_staff = True
        )
        new_user.set_password(password)
        new_user.save(using = self.db)
        return new_user
    

class CustomUser(AbstractBaseUser,PermissionsMixin):
    """Custom User Model"""
    
    email = EmailField(
        max_length=50,
        unique=True,
        verbose_name="Email Address",
        help_text="Enter your email address",
        db_index=True
    )
    full_name = CharField(
        max_length=100,
        verbose_name="Full Name",
        help_text="Enter your full name",
    )
    password = CharField(
        max_length=100,
        verbose_name="Password",
        help_text="Enter your password",
        validators = [validate_password]
    )
    is_active = BooleanField(
        default=True,
        verbose_name="Is_active"
    )
    is_staff = BooleanField(
        default=False,
        verbose_name="Is_staff"
    )
    
    REQUIRED_FIELDS = ["full_name"]
    USERNAME_FIELD = 'email'
    objects = CustomUserManager()
    
    
    class Meta:
        """class META"""
        
        verbose_name = "Custom User"
        verbose_name_plural = "Custom Users"




