from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RampImage
from .serializers import RampCalculationSerializer, RampImageSerializer
from .services import RampGeometryError, calculate_ramp_configuration


class RampCalculationView(APIView):
    def post(self, request):
        serializer = RampCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = calculate_ramp_configuration(**serializer.validated_data)
        except RampGeometryError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class RampImageListCreateView(ListCreateAPIView):
    queryset = RampImage.objects.all()
    serializer_class = RampImageSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        queryset = super().get_queryset()
        kind = self.request.query_params.get("kind")
        return queryset.filter(kind=kind) if kind else queryset


class RampImageDetailView(RetrieveUpdateDestroyAPIView):
    queryset = RampImage.objects.all()
    serializer_class = RampImageSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def perform_destroy(self, instance):
        storage, name = instance.file.storage, instance.file.name
        instance.delete()
        storage.delete(name)

