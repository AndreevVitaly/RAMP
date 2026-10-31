from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ramps", "0010_technicalbrief_profile_image")]

    operations = [
        migrations.AddField(model_name="savedproject", name="status", field=models.CharField(choices=[("saved", "Сохранён"), ("submitted", "Передан в работу"), ("in_progress", "В работе"), ("completed", "Выполнено")], default="saved", max_length=20, verbose_name="Статус")),
        migrations.AddField(model_name="savedproject", name="planned_completion_date", field=models.DateField(blank=True, null=True, verbose_name="Плановая дата выполнения")),
        migrations.AddField(model_name="savedproject", name="selected_by_admin", field=models.BooleanField(default=False, verbose_name="Выбран администратором")),
        migrations.AddField(model_name="savedproject", name="completed_at", field=models.DateTimeField(blank=True, null=True, verbose_name="Выполнен")),
    ]
