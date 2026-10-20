from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("ramps", "0002_accounts_and_briefs")]
    operations = [migrations.RenameField(model_name="customer", old_name="phone_verified", new_name="email_verified")]
