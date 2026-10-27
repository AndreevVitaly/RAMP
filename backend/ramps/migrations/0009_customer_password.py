from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ramps", "0008_emailcoderequest")]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="password_hash",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="Хеш пароля"),
        ),
        migrations.CreateModel(
            name="CustomerAuthAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purpose", models.CharField(max_length=12)),
                ("email_digest", models.CharField(db_index=True, max_length=64)),
                ("ip_digest", models.CharField(db_index=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
        ),
    ]
