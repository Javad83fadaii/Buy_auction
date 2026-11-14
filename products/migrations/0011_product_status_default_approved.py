from django.db import migrations, models


def approve_all_products(apps, schema_editor):
    """وضعیت‌های گردش‌کار قبلی (پیش‌نویس، در انتظار بررسی، منتشر شده) را تأیید شده می‌کند."""
    Product = apps.get_model('products', 'Product')
    Product.objects.exclude(status='REJECTED').update(status='APPROVED')


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_product_price_text'),
    ]

    operations = [
        migrations.RunPython(approve_all_products, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='status',
            field=models.CharField(
                choices=[
                    ('DRAFT', 'پیش‌نویس'),
                    ('PENDING_REVIEW', 'در انتظار بررسی'),
                    ('APPROVED', 'تأیید شده'),
                    ('PUBLISHED', 'منتشر شده'),
                    ('REJECTED', 'رد شده'),
                ],
                db_index=True,
                default='APPROVED',
                max_length=32,
                verbose_name='وضعیت',
            ),
        ),
    ]
