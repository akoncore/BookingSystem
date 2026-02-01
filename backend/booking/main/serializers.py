#Rest models
from jsonschema.validators import validate
from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    SerializerMethodField,
    StringRelatedField
    )

#Project models
from .models import (
    Salon,
    Master,
    Service,

)


class MasterSerializer(ModelSerializer):
    """
    MasterSerializer
    """
    user_info = SerializerMethodField()
    salon_info = SerializerMethodField()


    class Meta:
        """
        Meta for MASTER SERIALIZER
        """
        model = Master
        fields = [
            'user_info',
            'salon_info',
            'specialization',
            'experience_years',
            'bio',
            'is_approved'
        ]
        read_only_fields = ['is_approved']


    def get_user_info(self,obj):
        user = obj.user
        if user.role == 'master':
            return {
                'id':user.id,
                'full_name':user.full_name,
                'email':user.email,
                'role':user.role,
            }


    def get_salon_info(self,obj):
        salon = obj.salon
        return {
            'name':salon.name,
        }


class ServiceSerializer(ModelSerializer):
    """
    SalonSerializer
    """
    salon_info = SerializerMethodField()
    class Meta:
        model:Service
        fields = [
            'name',
            'discription',
            'price',
            'duration',
            'salon_info',
            'is_active',
        ]


    def get_salon_info(self,obj):
        salon = obj.salon
        return {
            'name':salon.name,
            'address':salon.address,
        }



class SalonSerializer(ModelSerializer):
    """
    SalonSerializer
    """

    class Meta:
        model = Salon
        fields = [
            'salon_id',
            'name',
            'address',
            'phone',
            'description',
            'is_active'
        ]