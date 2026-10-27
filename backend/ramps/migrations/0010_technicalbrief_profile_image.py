from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ramps", "0009_customer_password")]

    operations = [
        migrations.AddField(
            model_name="technicalbrief",
            name="profile_image",
            field=models.TextField(blank=True, verbose_name="Изображение геометрического профиля"),
        ),
    ]
