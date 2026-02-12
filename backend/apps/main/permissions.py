# apps/main/permissions.py
"""
Custom permissions for booking system
"""

from rest_framework.permissions import BasePermission


class IsClient(BasePermission):
    """
    Тек CLIENT роліндегі пайдаланушыларға рұқсат
    """
    message = "Only clients can perform this action"
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_client
        )


class IsAdmin(BasePermission):
    """
    Тек ADMIN роліндегі пайдаланушыларға рұқсат
    """
    message = "Only admins can perform this action"
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )


class IsMaster(BasePermission):
    """
    Тек MASTER роліндегі пайдаланушыларға рұқсат
    """
    message = "Only masters can perform this action"
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_master
        )


class IsAdminOrMaster(BasePermission):
    """
    ADMIN немесе MASTER роліндегі пайдаланушыларға рұқсат
    """
    message = "Only admins or masters can perform this action"
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_master)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-тің иесі немесе admin-ге рұқсат
    """
    message = "You don't have permission to access this resource"
    
    def has_object_permission(self, request, view, obj):
        # Admin-ге барлығына рұқсат
        if request.user.is_admin:
            return True
        
        # Объектінің owner атрибуты бар ма тексеру
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        # Объектінің user атрибуты бар ма тексеру
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Объектінің client атрибуты бар ма тексеру (Booking үшін)
        if hasattr(obj, 'client'):
            return obj.client == request.user
        
        # Объектінің master атрибуты бар ма тексеру (Booking үшін)
        if hasattr(obj, 'master'):
            return obj.master == request.user
        
        return False


class IsBookingParticipant(BasePermission):
    """
    Booking-тың клиенті, мастері немесе admin-ге рұқсат
    """
    message = "Only booking participants can access this booking"
    
    def has_object_permission(self, request, view, obj):
        # Admin-ге барлығына рұқсат
        if request.user.is_admin:
            return True
        
        # Booking объекті ма тексеру
        if hasattr(obj, 'client') and hasattr(obj, 'master'):
            return obj.client == request.user or obj.master == request.user
        
        return False


class CanManageWorkSchedule(BasePermission):
    """
    Жұмыс кестесін басқару үшін рұқсат:
    - Admin: барлық кестелерді басқара алады
    - Master: тек өзінің кестесін басқара алады
    """
    message = "You don't have permission to manage this work schedule"
    
    def has_permission(self, request, view):
        # Аутентификацияланған және admin/master болу керек
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_master)
        )
    
    def has_object_permission(self, request, view, obj):
        # Admin барлығына қол жеткізе алады
        if request.user.is_admin:
            return True
        
        # Master тек өзінің кестесін басқара алады
        if request.user.is_master:
            return obj.master == request.user
        
        return False


class ReadOnly(BasePermission):
    """
    Тек оқуға рұқсат (GET, HEAD, OPTIONS)
    """
    
    def has_permission(self, request, view):
        return request.method in ['GET', 'HEAD', 'OPTIONS']