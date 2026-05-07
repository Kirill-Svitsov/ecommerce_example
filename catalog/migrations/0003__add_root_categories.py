from django.db import migrations


def add_root_categories(apps, schema_editor):
    """Добавляет две корневые категории"""
    Category = apps.get_model('catalog', 'Category')
    Category.objects.get_or_create(
        slug='designer-items',
        defaults={
            'name_ru': 'Дизайнерские предметы',
            'name_en': 'Designer items',
            'description_ru': 'Коллекция дизайнерских предметов интерьера',
            'description_en': 'Collection of designer interior items',
            'is_active': True,
            'sort_order': 1,
        }
    )
    Category.objects.get_or_create(
        slug='art',
        defaults={
            'name_ru': 'Арт',
            'name_en': 'Art',
            'description_ru': 'Коллекция произведений искусства',
            'description_en': 'Collection of art pieces',
            'is_active': True,
            'sort_order': 2,
        }
    )


def remove_root_categories(apps, schema_editor):
    """Удаляет корневые категории (для отката миграции)"""
    Category = apps.get_model('catalog', 'Category')
    Category.objects.filter(slug__in=['designer-items', 'art']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0002_item_art_description_en_item_art_description_ru'),
    ]

    operations = [
        migrations.RunPython(add_root_categories, remove_root_categories),
    ]
