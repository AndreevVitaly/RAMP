from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ramps", "0006_savedproject")]

    operations = [
        migrations.AddField(
            model_name="phoneverification",
            name="purpose",
            field=models.CharField(choices=[("registration", "Регистрация"), ("login", "Вход")], default="registration", max_length=20),
        ),
    ]
