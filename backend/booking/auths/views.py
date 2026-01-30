#django models
from django.shortcuts import render

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

class AuthViewSet(ViewSet):
    """Authentication ViewSet for user registration and login.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'],url_path='register', url_name='register')
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': "User registered successfully.",
                'user': UserProfileSerializer(user).data,
                'tokens':{
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
    @action(detail=False, methods=['post'], url_path='login', url_name='login')
    def login(self, request):
        """User login action."""
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': "User logged in successfully.",
                'user': UserProfileSerializer(user).data,
                'tokens':{
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                    }
                },
                status=status.HTTP_200_OK
            )
            
    
    def logout(self, request):
        """User logout action."""
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "User logged out successfully."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
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
    
      
class UserViewSet(ViewSet):
    """
    A simple ViewSet for registering users.
    """
    
    #permission_classes = [IsAuthenticated]

    
    def list(self,request):
        """
        List all users.
        """
        users = CustomUser.objects.all()
        serializer = UserProfileSerializer(users, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a user by ID.
        """
        try:
            user = CustomUser.objects.get(pk=pk)
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
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


    
    
        
        
