from django.core.management.base import BaseCommand
from app.models import Member


class Command(BaseCommand):
    help = "Seed members"

    def handle(self, *args, **options):
        seeds = [
            ("12345678", "山田 太郎"),
            ("87654321", "佐藤 花子"),
            ("11112222", "鈴木 次郎"),
        ]

        for num, name in seeds:
            Member.objects.update_or_create(
                member_number=num,
                defaults={"name": name, "is_active": True},
            )

        self.stdout.write(self.style.SUCCESS("Seeded members"))
