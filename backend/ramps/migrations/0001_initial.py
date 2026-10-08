from django.db import migrations, models
import ramps.models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="RampImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("photo", "Фотография"), ("illustration", "Иллюстрация")], max_length=20)),
                ("file", models.FileField(upload_to=ramps.models.image_upload_path)),
                ("original_name", models.CharField(max_length=255)),
                ("file_sha256", models.CharField(max_length=64)),
                ("title", models.CharField(blank=True, max_length=160)),
                ("caption", models.CharField(blank=True, max_length=300)),
                ("image_type", models.CharField(blank=True, choices=[("product", "Главный вид изделия"), ("sofa", "Пандус возле дивана"), ("bed", "Пандус возле кровати"), ("folded", "Пандус в сложенном состоянии"), ("storage", "Хранение за мебелью"), ("carpet", "Крупный план покрытия")], max_length=30)),
                ("color", models.CharField(blank=True, max_length=30)),
                ("has_slats", models.BooleanField(default=True)),
                ("side_rails", models.BooleanField(default=False)),
                ("description", models.TextField(blank=True)),
                ("configuration", models.JSONField(blank=True, default=dict)),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("-is_primary", "-created_at")},
        ),
    ]
