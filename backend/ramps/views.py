from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets

from .accounts import customer_from_request, deliver_brief, digest, issue_session, normalize_phone, send_sms_code
from .models import AdminContactSettings, Customer, PhoneVerification, RampImage, TechnicalBrief
from .serializers import AdminContactSettingsSerializer, CustomerSerializer, RampCalculationSerializer, RampImageSerializer, TechnicalBriefSerializer
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


class RequestPhoneCodeView(APIView):
    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        email = str(request.data.get("email", "")).strip()
        try:
            phone = normalize_phone(request.data.get("phone", ""))
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        if not name or "@" not in email:
            return Response({"detail": "Укажите имя и корректную электронную почту."}, status=status.HTTP_400_BAD_REQUEST)
        code = f"{secrets.randbelow(1_000_000):06d}"
        PhoneVerification.objects.filter(phone=phone).delete()
        PhoneVerification.objects.create(phone=phone, name=name, email=email, code_digest=digest(code), expires_at=timezone.now() + timedelta(minutes=10))
        delivered = send_sms_code(phone, code)
        payload = {"detail": "Код подтверждения отправлен.", "sms_configured": delivered}
        if settings.DEBUG:
            payload["dev_code"] = code
        elif not delivered:
            return Response({"detail": "Сервис SMS пока не настроен."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(payload)


class VerifyPhoneCodeView(APIView):
    def post(self, request):
        try:
            phone = normalize_phone(request.data.get("phone", ""))
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        challenge = PhoneVerification.objects.filter(phone=phone, expires_at__gt=timezone.now()).order_by("-created_at").first()
        if not challenge or challenge.attempts >= 5 or challenge.code_digest != digest(str(request.data.get("code", ""))):
            if challenge:
                challenge.attempts += 1
                challenge.save(update_fields=("attempts",))
            return Response({"detail": "Неверный или просроченный код."}, status=status.HTTP_400_BAD_REQUEST)
        customer, _ = Customer.objects.update_or_create(phone=phone, defaults={"name": challenge.name, "email": challenge.email, "phone_verified": True})
        challenge.delete()
        return Response({"token": issue_session(customer), "customer": CustomerSerializer(customer).data})


class CustomerAccountView(APIView):
    def get(self, request):
        return Response(CustomerSerializer(customer_from_request(request)).data)


class TechnicalBriefListCreateView(APIView):
    def get(self, request):
        customer = customer_from_request(request)
        return Response(TechnicalBriefSerializer(customer.technical_briefs.all(), many=True).data)

    def post(self, request):
        customer = customer_from_request(request)
        serializer = TechnicalBriefSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        brief = serializer.save(customer=customer)
        deliver_brief(brief)
        return Response(TechnicalBriefSerializer(brief).data, status=status.HTTP_201_CREATED)


class AdminSettingsView(APIView):
    def get(self, request):
        instance = AdminContactSettings.objects.first() or AdminContactSettings.objects.create()
        return Response(AdminContactSettingsSerializer(instance).data)

    def put(self, request):
        if request.headers.get("X-Admin-Key") != settings.RAMP_ADMIN_KEY:
            return Response({"detail": "Неверный ключ администратора."}, status=status.HTTP_403_FORBIDDEN)
        instance = AdminContactSettings.objects.first() or AdminContactSettings.objects.create()
        serializer = AdminContactSettingsSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminBriefListView(APIView):
    def get(self, request):
        if request.headers.get("X-Admin-Key") != settings.RAMP_ADMIN_KEY:
            return Response({"detail": "Неверный ключ администратора."}, status=status.HTTP_403_FORBIDDEN)
        return Response(TechnicalBriefSerializer(TechnicalBrief.objects.select_related("customer").all(), many=True).data)

