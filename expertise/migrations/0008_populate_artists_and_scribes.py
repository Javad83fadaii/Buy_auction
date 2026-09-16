from django.db import migrations


def populate_artists_and_scribes(apps, schema_editor):
    ArtistOrScribe = apps.get_model('expertise', 'ArtistOrScribe')
    ExpertAppraisal = apps.get_model('expertise', 'ExpertAppraisal')
    Product = apps.get_model('products', 'Product')

    seen_names = set()

    for appraisal in ExpertAppraisal.objects.exclude(artist_or_scribe_name='').iterator():
        raw_name = appraisal.artist_or_scribe_name or ''
        cleaned_name = ' '.join(raw_name.split())
        if cleaned_name and cleaned_name not in seen_names:
            ArtistOrScribe.objects.get_or_create(name=cleaned_name)
            seen_names.add(cleaned_name)

    for product in Product.objects.exclude(artist='').iterator():
        raw_name = product.artist or ''
        cleaned_name = ' '.join(raw_name.split())
        if cleaned_name and cleaned_name not in seen_names:
            ArtistOrScribe.objects.get_or_create(name=cleaned_name)
            seen_names.add(cleaned_name)


class Migration(migrations.Migration):

    dependencies = [
        ('expertise', '0007_artistorscribe'),
        ('products', '0003_product_assigned_expert'),
    ]

    operations = [
        migrations.RunPython(populate_artists_and_scribes, reverse_code=migrations.RunPython.noop),
    ]
