from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
from datetime import timedelta


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userotp',
            name='email',
            field=models.EmailField(default='', max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userotp',
            name='purpose',
            field=models.CharField(
                choices=[('email_verification', 'التحقق من البريد الإلكتروني'), ('password_reset', 'إعادة تعيين كلمة المرور')],
                default='email_verification',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='userotp',
            name='expires_at',
            field=models.DateTimeField(default=timezone.now() + timedelta(minutes=10)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userotp',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='otps',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterModelOptions(
            name='userotp',
            options={'ordering': ['-created_at']},
        ),
    ]
