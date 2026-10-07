from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RampCalculationSerializer
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

