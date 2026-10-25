import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ramps", "0005_alter_admincontactsettings_options_and_more")]

    operations = [
        migrations.CreateModel(
            name="SavedProject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Название")),
                ("configuration", models.JSONField(default=dict, verbose_name="Параметры изделия")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_projects", to="ramps.customer", verbose_name="Клиент")),
            ],
            options={"ordering": ("-created_at", "-id"), "verbose_name": "Сохранённый проект", "verbose_name_plural": "Сохранённые проекты"},
        ),
    ]
