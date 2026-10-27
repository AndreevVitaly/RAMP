from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import secrets

from .accounts import admin_authorized, customer_from_request, deliver_brief, digest, issue_admin_token, issue_session, normalize_phone
from .models import AdminContactSettings, Customer, PhoneVerification, RampImage, SavedProject, TechnicalBrief
from .rate_limit import allow_customer_auth_attempt, allow_email_code_request
from .serializers import AdminContactSettingsSerializer, AdminSavedProjectSerializer, CustomerSerializer, RampCalculationSerializer, RampImageSerializer, SavedProjectSerializer, TechnicalBriefSerializer
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

    def create(self, request, *args, **kwargs):
        if not admin_authorized(request):
            return Response({"detail": "Требуется вход администратора."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        kind = self.request.query_params.get("kind")
        return queryset.filter(kind=kind) if kind else queryset


class RampImageDetailView(RetrieveUpdateDestroyAPIView):
    queryset = RampImage.objects.all()
    serializer_class = RampImageSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def update(self, request, *args, **kwargs):
        if not admin_authorized(request):
            return Response({"detail": "Требуется вход администратора."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not admin_authorized(request):
            return Response({"detail": "Требуется вход администратора."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        storage, name = instance.file.storage, instance.file.name
        instance.delete()
        storage.delete(name)


class CustomerRegisterView(APIView):
    def post(self, request):
        name = str(request.data.get("name") or "").strip()
        email = str(request.data.get("email") or "").strip().lower()
        password = str(request.data.get("password") or "")
        if not name or len(name) > 120:
            return Response({"detail": "Укажите имя до 120 символов."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError:
            return Response({"detail": "Укажите корректный email."}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 10 or len(password) > 128:
            return Response({"detail": "Пароль должен содержать от 10 до 128 символов."}, status=status.HTTP_400_BAD_REQUEST)
        if not allow_customer_auth_attempt(request, email, "register"):
            return Response({"detail": "Слишком много попыток. Попробуйте позже."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if Customer.objects.filter(email__iexact=email).exists():
            return Response({"detail": "Этот email уже зарегистрирован. Войдите в аккаунт."}, status=status.HTTP_400_BAD_REQUEST)
        customer = Customer.objects.create(name=name, email=email, password_hash=make_password(password))
        return Response({"token": issue_session(customer), "customer": CustomerSerializer(customer).data}, status=status.HTTP_201_CREATED)


class CustomerPasswordLoginView(APIView):
    def post(self, request):
        email = str(request.data.get("email") or "").strip().lower()
        password = str(request.data.get("password") or "")
        if not email or not password:
            return Response({"detail": "Введите email и пароль."}, status=status.HTTP_400_BAD_REQUEST)
        if not allow_customer_auth_attempt(request, email, "login"):
            return Response({"detail": "Слишком много попыток. Попробуйте позже."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        customer = Customer.objects.filter(email__iexact=email).first()
        if not customer or not customer.password_hash or not check_password(password, customer.password_hash):
            return Response({"detail": "Неверный email или пароль."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"token": issue_session(customer), "customer": CustomerSerializer(customer).data})


class RequestEmailCodeView(APIView):
    def post(self, request):
        name = str(request.data.get("name", "")).strip()
        email = str(request.data.get("email", "")).strip().lower()
        supplied_phone = str(request.data.get("phone") or "").strip()
        try:
            phone = normalize_phone(supplied_phone) if supplied_phone else ""
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        if not name or "@" not in email:
            return Response({"detail": "Укажите имя и корректную электронную почту."}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.DEBUG and settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
            return Response({"detail": "Отправка почты пока не настроена."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not allow_email_code_request(request, email):
            return Response({"detail": "Слишком много запросов кода. Подождите и попробуйте позже."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        code = f"{secrets.randbelow(1_000_000):06d}"
        PhoneVerification.objects.filter(email__iexact=email).delete()
        PhoneVerification.objects.create(phone=phone, name=name, email=email, purpose=PhoneVerification.REGISTRATION, code_digest=digest(code), expires_at=timezone.now() + timedelta(minutes=10))
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


class RequestLoginCodeView(APIView):
    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        if "@" not in email:
            return Response({"detail": "Укажите корректную электронную почту."}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.DEBUG and settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
            return Response({"detail": "Отправка почты пока не настроена."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not allow_email_code_request(request, email):
            return Response({"detail": "Слишком много запросов кода. Подождите и попробуйте позже."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        message = "Если этот адрес зарегистрирован, код входа отправлен на электронную почту."
        customer = Customer.objects.filter(email__iexact=email, email_verified=True).first()
        if not customer:
            return Response({"detail": message})

        code = f"{secrets.randbelow(1_000_000):06d}"
        PhoneVerification.objects.filter(email__iexact=email).delete()
        PhoneVerification.objects.create(
            phone="", name=customer.name, email=customer.email, purpose=PhoneVerification.LOGIN,
            code_digest=digest(code), expires_at=timezone.now() + timedelta(minutes=10),
        )
        try:
            send_mail("Код входа RAMP", f"Ваш код входа: {code}\n\nКод действует 10 минут.", settings.DEFAULT_FROM_EMAIL, [customer.email])
            delivered = True
        except Exception:
            delivered = False
        if not delivered and not settings.DEBUG:
            return Response({"detail": "Сервис отправки почты пока не настроен."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        payload = {"detail": message}
        if settings.DEBUG:
            payload["dev_code"] = code
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
        if challenge.purpose == PhoneVerification.LOGIN:
            if not customer or not customer.email_verified:
                return Response({"detail": "Аккаунт не найден. Зарегистрируйтесь заново."}, status=status.HTTP_400_BAD_REQUEST)
            challenge.delete()
            return Response({"token": issue_session(customer), "customer": CustomerSerializer(customer).data})
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


class CustomerPasswordView(APIView):
    def post(self, request):
        customer = customer_from_request(request)
        current_password = str(request.data.get("current_password") or "")
        new_password = str(request.data.get("new_password") or "")
        if customer.password_hash and not check_password(current_password, customer.password_hash):
            return Response({"detail": "Текущий пароль указан неверно."}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 10 or len(new_password) > 128:
            return Response({"detail": "Новый пароль должен содержать от 10 до 128 символов."}, status=status.HTTP_400_BAD_REQUEST)
        customer.password_hash = make_password(new_password)
        customer.save(update_fields=("password_hash", "updated_at"))
        return Response({"detail": "Пароль сохранён."})


class SavedProjectListCreateView(APIView):
    def get(self, request):
        customer = customer_from_request(request)
        return Response(SavedProjectSerializer(customer.saved_projects.all(), many=True).data)

    def post(self, request):
        customer = customer_from_request(request)
        serializer = SavedProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(customer=customer)
        return Response(SavedProjectSerializer(project).data, status=status.HTTP_201_CREATED)


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


class TechnicalBriefPdfPreviewView(APIView):
    def post(self, request):
        if admin_authorized(request):
            customer_id = request.data.get("customer_id")
            if customer_id is not None:
                if not str(customer_id).isdigit():
                    return Response({"detail": "Некорректный идентификатор клиента."}, status=status.HTTP_400_BAD_REQUEST)
                customer = Customer.objects.filter(pk=int(customer_id)).first()
                if not customer:
                    return Response({"detail": "Клиент не найден."}, status=status.HTTP_404_NOT_FOUND)
            else:
                customer = Customer(name="Администратор", email="", phone="")
        else:
            customer = customer_from_request(request)
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
            brief = TechnicalBrief(
                customer=customer,
                message=str(request.data.get("message", ""))[:5000],
                configuration=fields,
                result=result,
            )
            pdf = build_brief_pdf(brief)
        except ImportError:
            return Response({"detail": "Генератор PDF не установлен."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            return Response({"detail": "Не удалось сформировать PDF."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="ramp-technical-brief.pdf"'
        return response


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


class AdminSavedProjectListView(APIView):
    def get(self, request):
        if not admin_authorized(request):
            return Response({"detail": "Требуется вход администратора."}, status=status.HTTP_403_FORBIDDEN)
        projects = SavedProject.objects.select_related("customer").all()
        return Response(AdminSavedProjectSerializer(projects, many=True).data)


def django_admin_project_preview(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"detail": "Требуется вход администратора."}, status=403)
    project = get_object_or_404(SavedProject.objects.select_related("customer"), pk=pk)
    return JsonResponse(AdminSavedProjectSerializer(project).data)


class AdminLoginView(APIView):
    def post(self, request):
        username = str(request.data.get("username", ""))
        password = str(request.data.get("password", ""))
        user = authenticate(request=request, username=username, password=password)
        if not user or not user.is_active or not user.is_staff:
            return Response({"detail": "Неверный логин или пароль."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"token": issue_admin_token(user), "expires_in_hours": 12})

