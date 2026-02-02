#Django Models
from django.shortcuts import get_object_or_404

#REST Models
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
)

from .models import Master
#from rest_framework.permissions import IsAuthenticated

#Project Models
from .models import (
    Master
)
from .serializers import (
    MasterSerializer,
    MasterRejectSerializer,
    MasterApproveSerializer,
    MasterRequestSerializer
)


class MasterViewSet(ViewSet):
    """
    Master viewset
    """
    def list(self, request):
        queryset = Master.objects.all()
        serializer = MasterSerializer(queryset, many=True)
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )


    def retrieve(self, request, pk=None):
        queryset = Master.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = MasterSerializer(user)
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )


    @action(detail=False, methods=['post'], url_path='request-job')
    def request_job(self,request):
        serializer = MasterRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        master = serializer.save()

        return Response({
            'status':'success',
            'message':'Request job has been requested',
            'data':MasterSerializer(master).data
            },status=HTTP_200_OK
        )
