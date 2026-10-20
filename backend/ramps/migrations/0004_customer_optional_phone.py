from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ramps", "0003_customer_email_verified")]
    operations = [
        migrations.AlterField(
            model_name="customer",
            name="phone",
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
    ]
