from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import secrets

from .accounts import admin_authorized, customer_from_request, deliver_brief, digest, issue_admin_token, issue_session, normalize_phone
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


class RequestEmailCodeView(APIView):
    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        email = str(request.data.get("email", "")).strip()
        supplied_phone = str(request.data.get("phone") or "").strip()
        try:
            phone = normalize_phone(supplied_phone) if supplied_phone else ""
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        if not name or "@" not in email:
            return Response({"detail": "Укажите имя и корректную электронную почту."}, status=status.HTTP_400_BAD_REQUEST)
        code = f"{secrets.randbelow(1_000_000):06d}"
        PhoneVerification.objects.filter(email__iexact=email).delete()
        PhoneVerification.objects.create(phone=phone, name=name, email=email, code_digest=digest(code), expires_at=timezone.now() + timedelta(minutes=10))
        try:
            send_mail("Код регистрации RAMP", f"Ваш код подтверждения: {code}\n\nКод действует 10 минут.", settings.DEFAULT_FROM_EMAIL, [email])
            delivered = True
        except Exception:
            delivered = False
        payload = {"detail": "Код подтверждения отправлен на электронную почту.", "email_configured": delivered}
        if settings.DEBUG:
            payload["dev_code"] = code
        elif not delivered:
            return Response({"detail": "Сервис отправки почты пока не настроен."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(payload)


class VerifyEmailCodeView(APIView):
    def post(self, request):
        email = str(request.data.get("email", "")).strip()
        challenge = PhoneVerification.objects.filter(email__iexact=email, expires_at__gt=timezone.now()).order_by("-created_at").first()
        if not challenge or challenge.attempts >= 5 or challenge.code_digest != digest(str(request.data.get("code", ""))):
            if challenge:
                challenge.attempts += 1
                challenge.save(update_fields=("attempts",))
            return Response({"detail": "Неверный или просроченный код."}, status=status.HTTP_400_BAD_REQUEST)
        customer = Customer.objects.filter(email__iexact=challenge.email).first()
        if challenge.phone and Customer.objects.filter(phone=challenge.phone).exclude(pk=customer.pk if customer else None).exists():
            return Response({"detail": "Этот телефон уже указан в другом аккаунте. Измените данные регистрации."}, status=status.HTTP_400_BAD_REQUEST)
        if customer:
            customer.name = challenge.name
            customer.email = challenge.email
            customer.phone = challenge.phone or customer.phone
            customer.email_verified = True
            customer.save(update_fields=("name", "email", "phone", "email_verified", "updated_at"))
        else:
            customer = Customer.objects.create(name=challenge.name, email=challenge.email, phone=challenge.phone or None, email_verified=True)
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


class TechnicalBriefPdfView(APIView):
    def post(self, request):
        customer = customer_from_request(request)
        contacts = AdminContactSettings.objects.first()
        if not contacts or not contacts.email:
            return Response({"detail": "Администратор ещё не указал адрес электронной почты."}, status=status.HTTP_400_BAD_REQUEST)
        configuration = request.data.get("configuration")
        if not isinstance(configuration, dict):
            return Response({"detail": "Не указаны параметры пандуса."}, status=status.HTTP_400_BAD_REQUEST)
        fields = {key: configuration[key] for key in RampCalculationSerializer().fields if key in configuration}
        calculation = RampCalculationSerializer(data=fields)
        calculation.is_valid(raise_exception=True)
        try:
            result = calculate_ramp_configuration(**calculation.validated_data)
        except RampGeometryError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from .brief_pdf import build_brief_pdf
        except ImportError:
            return Response({"detail": "Генератор PDF не установлен. Установите зависимости backend из requirements.txt."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        brief = TechnicalBrief.objects.create(
            customer=customer, message=str(request.data.get("message", ""))[:5000],
            configuration=fields, result=result, requested_channels=["email"],
        )
        try:
            pdf = build_brief_pdf(brief)
        except Exception:
            brief.delivery_status = {"pdf": "failed"}
            brief.save(update_fields=("delivery_status",))
            return Response({"detail": "Не удалось сформировать PDF. Задание сохранено, письма не отправлены."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        delivery = {}
        for recipient, address in (("admin", contacts.email), ("customer", customer.email)):
            try:
                email = EmailMessage(
                    f"Техническое задание RAMP №{brief.pk}",
                    f"Во вложении техническое задание RAMP №{brief.pk} в формате PDF.",
                    settings.DEFAULT_FROM_EMAIL, [address],
                )
                email.attach(f"ramp-technical-brief-{brief.pk}.pdf", pdf, "application/pdf")
                email.send(fail_silently=False)
                delivery[recipient] = "sent" if settings.EMAIL_BACKEND != "django.core.mail.backends.console.EmailBackend" else "console_only"
            except Exception:
                delivery[recipient] = "failed"
        brief.delivery_status = {"pdf_email": delivery}
        brief.save(update_fields=("delivery_status",))
        return Response({"id": brief.pk, "delivery_status": delivery, "download_url": f"/api/ramp/account/briefs/{brief.pk}/pdf/"}, status=status.HTTP_201_CREATED)


class TechnicalBriefPdfDownloadView(APIView):
    def get(self, request, pk):
        customer = customer_from_request(request)
        brief = customer.technical_briefs.filter(pk=pk).first()
        if not brief or "pdf_email" not in brief.delivery_status:
            return Response({"detail": "Техническое задание не найдено."}, status=status.HTTP_404_NOT_FOUND)
        try:
            from .brief_pdf import build_brief_pdf
        except ImportError:
            return Response({"detail": "Генератор PDF не установлен."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        response = HttpResponse(build_brief_pdf(brief), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="ramp-technical-brief-{brief.pk}.pdf"'
        return response


class AdminSettingsView(APIView):
    def get(self, request):
        instance = AdminContactSettings.objects.first() or AdminContactSettings.objects.create()
        return Response(AdminContactSettingsSerializer(instance).data)

    def put(self, request):
        if not admin_authorized(request):
            return Response({"detail": "Неверный ключ администратора."}, status=status.HTTP_403_FORBIDDEN)
        instance = AdminContactSettings.objects.first() or AdminContactSettings.objects.create()
        serializer = AdminContactSettingsSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminBriefListView(APIView):
    def get(self, request):
        if not admin_authorized(request):
            return Response({"detail": "Неверный ключ администратора."}, status=status.HTTP_403_FORBIDDEN)
        return Response(TechnicalBriefSerializer(TechnicalBrief.objects.select_related("customer").all(), many=True).data)


class AdminLoginView(APIView):
    def post(self, request):
        username = str(request.data.get("username", ""))
        password = str(request.data.get("password", ""))
        if not secrets.compare_digest(username, settings.RAMP_ADMIN_USERNAME) or not secrets.compare_digest(password, settings.RAMP_ADMIN_PASSWORD):
            return Response({"detail": "Неверный логин или пароль."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"token": issue_admin_token(), "expires_in_hours": 12})

