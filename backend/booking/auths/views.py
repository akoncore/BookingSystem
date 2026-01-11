#django models
from django.shortcuts import render

#rest framework imports
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
 
#project models
from .models import CustomUser
from .serializers import (
    RegisterSerializer,
    UserProfileSerializers,
)

class AuthViewSet(ViewSet):
    """Authentication ViewSet for user registration and login.
    """
    @action(detail=False, methods=['post'],url_path='register', url_name='register')
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': "User registered successfully.",
                'user': UserProfileSerializers(user).data,
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

class UserViewSet(ViewSet):
    """
    A simple ViewSet for registering users.
    """
    
    permission_classes = [IsAuthenticated]

    
    def list(self,request):
        """
        List all users.
        """
        users = CustomUser.objects.all()
        serializer = UserProfileSerializers(users, many=True)
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
            serializer = UserProfileSerializers(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    
        
