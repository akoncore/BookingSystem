#Python modules
from logging import getLogger

#django imports
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.core.mail import send_mail

#rest framework imports
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
 
#project models
from .models import CustomUser
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    LoginSerializer
)


logger = getLogger(__name__)

#helper function
def get_user_lang(user)->str:
    return getattr(user,'preferred_language','en')

def translated_language(user, message_key:str)->str:

    user_lang = get_user_lang(user)
    with translation.override(user_lang):
        return _(message_key)


class AuthViewSet(ViewSet):
    """Authentication ViewSet for user registration and login.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'],url_path='register', url_name='register')
    def register(self, request):
        """
        Register a new user.
        """
        email = request.data.get('email')
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            user_lang = request.data.get('language','en')
            if user_lang not in ['en','kk','ru']:
                user_lang = 'en'

            user.preferred_language = user_lang
            user.save(update_fields = ["preferred_language"])

            with translation.override(user_lang):

                try:

                    body = render_to_string(
                        'emails/welcome/body.html',
                        {
                            'full_name':user.full_name,
                            'lang':user_lang
                        }
                    )
                    send_mail(
                        subject=_("Welcome to Booking System"),
                        message="",
                        from_email='admin@salon.com',
                        recipient_list=[user.email],
                        html_message=body,
                        fail_silently=True
                    )

                    logger.info('Welcome email sent to: %s (lang=%s)', user.email, user_lang)

                except Exception as e:

                    logger.error('Welcome email failed: %s', e)

                message = _('User registered successfully.')
                logger.info('Translated message: "%s" (lang=%s)', message, user_lang)

            logger.info('User registered: %s (lang=%s)', user.email, user_lang)
            return Response({
                'message': message,
                'user': UserProfileSerializer(user).data,
                'tokens':{
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                    }
                },
                status=status.HTTP_201_CREATED
            )
        logger.warning(f'Registeration failed: {email}: {serializer.errors}')
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
    @action(detail=False, methods=['post'], url_path='login', url_name='login')
    def login(self, request):
        """User login action."""
        email = request.data.get('email')
        serializer = LoginSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            user_lang = get_user_lang(user)

            with translation.override(user_lang):
                message = _('User logged in successfully')

            logger.info(f"User logged in: {user.email} (Id={user.id}, Role: {user.role})")

            return Response({
                'message':message,
                'user': UserProfileSerializer(user).data,
                'tokens':{
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                    }
                },
                status=status.HTTP_200_OK
            )
        logger.warning(f'Login failed: {email}: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    
    def logout(self, request):
        """User logout action."""
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"User logged out: {refresh_token}")

            return Response(
                {"message": "User logged out successfully."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            logger.warning(f'Logout failed: {request.data["refresh"]}')
            return Response(
                {"error": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    
    def refresh_token(self, request):
        """Refresh JWT token action."""
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            return Response(
                {
                    "access": new_access_token
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(
        detail=False,
        methods=['patch'],
        url_name='language'
    )
    def set_language(self,request):

        from django.conf import settings as django_settings

        lang = request.data.get('language')
        supportted = getattr(django_settings,'SUPPORTED_LANGUAGES',['en','ru','kk'])

        if lang not in supportted:
            return Response(
                {'error': _('Invalid language. Choose from: en, ru, kk')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        request.user.preferred_language = lang
        request.user.save(update_fields = ['preferred_language'])

        with translation.override(lang):
            message = _('Language updated successfully.')


        logger.info('Language updated: user=%s, lang=%s', request.user.id, lang)
        return Response(
            {'message': message, 'language': lang},
            status=status.HTTP_200_OK,
        )
    

    @action(
        detail=False,
        methods=['patch'],
        url_path='timezone',
        url_name='timezone',
        permission_classes=[IsAuthenticated],
    )
    def set_timezone(self, request):
        """
        Пайдаланушының timezone-ын өзгерту.
        PATCH /api/v1/auth/timezone/
        Body: { "timezone": "Asia/Almaty" }
        """
        import pytz
 
        tz_name = request.data.get('timezone')
 
        if not tz_name:
            return Response(
                {'error': _('Timezone is required')},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        # pytz арқылы timezone жарамдылығын тексеру
        try:
            pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            return Response(
                {'error': _('Invalid timezone. Example: Asia/Almaty, Europe/Moscow, UTC')},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        request.user.timezone = tz_name
        request.user.save(update_fields=['timezone'])
 
        logger.info('Timezone updated: user=%s, tz=%s', request.user.id, tz_name)
        return Response(
            {'message': _('Timezone updated successfully.'), 'timezone': tz_name},
            status=status.HTTP_200_OK,
        )
 
      
class UserViewSet(ViewSet):
    """
    A simple ViewSet for registering users.
    """
    
    #permission_classes = [IsAuthenticated]

    
    def list(self,request):
        """
        List all users.
        """
        try:
            users = CustomUser.objects.all()
            serializer = UserProfileSerializer(users, many=True)

            logger.info(f'User list: {serializer.data}')

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f'User list failed: {e}')
            return Response(
                {"error": "User list failed."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a user by ID.
        """
        try:
            user = CustomUser.objects.get(pk=pk)
            serializer = UserProfileSerializer(user)

            logger.info(f"User retrieved: {serializer.data}")

            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            logger.error(f'User does not exist: {pk}')
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    
    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def current_user(self,request):
        """Current logged in user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    
    @action(detail=False,methods=['get'],url_path='admin')
    def admin(self,requset):
        """There list of admin"""
        admines = CustomUser.objects.filter(role='admin')
        serializer = UserProfileSerializer(admines,many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    @action(detail=False,methods=['get'],url_path='masters')
    def masters(self,request):
        """
        There list of masters
        """
        masters = CustomUser.objects.filter(role='master')
        serializer = UserProfileSerializer(masters,many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    
    
        
        
