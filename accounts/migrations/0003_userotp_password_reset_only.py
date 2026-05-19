from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_admin_password_change_request"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userotp",
            name="purpose",
            field=models.CharField(
                choices=[("password_reset", "إعادة تعيين كلمة المرور")],
                default="password_reset",
                max_length=20,
            ),
        ),
    ]
