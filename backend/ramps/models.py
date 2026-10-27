import uuid

from django.db import models


def image_upload_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"ramp_images/{instance.kind}/{uuid.uuid4().hex}.{extension}"


class RampImage(models.Model):
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    KIND_CHOICES = ((PHOTO, "Фотография"), (ILLUSTRATION, "Иллюстрация"))
    IMAGE_TYPE_CHOICES = (
        ("product", "Главный вид изделия"),
        ("sofa", "Пандус возле дивана"),
        ("bed", "Пандус возле кровати"),
        ("folded", "Пандус в сложенном состоянии"),
        ("storage", "Хранение за мебелью"),
        ("carpet", "Крупный план покрытия"),
    )

    kind = models.CharField("Тип", max_length=20, choices=KIND_CHOICES)
    file = models.FileField("Файл", upload_to=image_upload_path)
    original_name = models.CharField("Исходное имя файла", max_length=255)
    file_sha256 = models.CharField("Контрольная сумма файла", max_length=64)
    title = models.CharField("Название", max_length=160, blank=True)
    caption = models.CharField("Подпись", max_length=300, blank=True)
    image_type = models.CharField("Сюжет изображения", max_length=30, choices=IMAGE_TYPE_CHOICES, blank=True)
    color = models.CharField("Цвет", max_length=30, blank=True)
    has_slats = models.BooleanField("Поперечные рейки", default=True)
    side_rails = models.BooleanField("Боковые бортики", default=False)
    description = models.TextField("Описание", blank=True)
    configuration = models.JSONField("Конфигурация", default=dict, blank=True)
    is_primary = models.BooleanField("Основное изображение", default=False)
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)

    class Meta:
        ordering = ("-is_primary", "-created_at")
        verbose_name = "Изображение пандуса"
        verbose_name_plural = "Изображения пандусов"

    def __str__(self):
        return self.title or self.original_name


class AdminContactSettings(models.Model):
    email = models.EmailField("Электронная почта", blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    telegram = models.CharField("Telegram", max_length=80, blank=True)
    max_contact = models.CharField("MAX", max_length=160, blank=True)
    preferred_channel = models.CharField("Предпочтительный канал", max_length=20, default="email")
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Контакты администратора"
        verbose_name_plural = "Контакты администратора"

    def __str__(self):
        return "Контакты администратора"


class Customer(models.Model):
    name = models.CharField("Имя", max_length=120)
    email = models.EmailField("Электронная почта")
    password_hash = models.CharField("Хеш пароля", max_length=128, blank=True, default="")
    phone = models.CharField("Телефон", max_length=30, unique=True, null=True, blank=True)
    email_verified = models.BooleanField("Почта подтверждена", default=False)
    created_at = models.DateTimeField("Зарегистрирован", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return f"{self.name} ({self.email})"


class PhoneVerification(models.Model):
    REGISTRATION = "registration"
    LOGIN = "login"
    PURPOSE_CHOICES = ((REGISTRATION, "Регистрация"), (LOGIN, "Вход"))

    phone = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default=REGISTRATION)
    code_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class EmailCodeRequest(models.Model):
    email_digest = models.CharField(max_length=64, db_index=True)
    ip_digest = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class CustomerAuthAttempt(models.Model):
    purpose = models.CharField(max_length=12)
    email_digest = models.CharField(max_length=64, db_index=True)
    ip_digest = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class CustomerSession(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sessions")
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class SavedProject(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="Клиент", on_delete=models.CASCADE, related_name="saved_projects")
    name = models.CharField("Название", max_length=120)
    configuration = models.JSONField("Параметры изделия", default=dict)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "Сохранённый проект"
        verbose_name_plural = "Сохранённые проекты"

    def __str__(self):
        return self.name


class TechnicalBrief(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="Клиент", on_delete=models.CASCADE, related_name="technical_briefs")
    message = models.TextField("Комментарий", blank=True)
    configuration = models.JSONField("Конфигурация", default=dict)
    result = models.JSONField("Результат расчёта", default=dict)
    requested_channels = models.JSONField("Каналы отправки", default=list)
    delivery_status = models.JSONField("Статус отправки", default=dict)
    profile_image = models.TextField("Изображение геометрического профиля", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Техническое задание"
        verbose_name_plural = "Технические задания"

    def __str__(self):
        return f"Техническое задание №{self.pk}"

