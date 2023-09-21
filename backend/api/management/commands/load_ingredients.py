import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Импорт в базу данных ингредиентов."""

    def handle(self, *args, **options) -> None:
        csv_file = Path(__file__).resolve().parent / 'data' / 'ingredients.csv'

        with open(csv_file, encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                name = row[0]
                measurement_unit = row[1]
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit,
                )
                self.stdout.write(self.style.SUCCESS(row))
            self.stdout.write(self.style.SUCCESS('Импортирование завершено'))
