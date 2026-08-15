import random
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from polls.models import Option, Poll, Vote

User = get_user_model()

DEMO_PASSWORD = "kararsizim123"

DEMO_USERS = [
    {"username": "ayse", "email": "ayse@example.com"},
    {"username": "mehmet", "email": "mehmet@example.com"},
    {"username": "elif", "email": "elif@example.com"},
]

DEMO_POLLS = [
    {"question": "Bugün sinemaya mı gitsem, restorana mı?", "options": ["Sinema", "Restoran"]},
    {"question": "Hafta sonu dağa mı çıksam, denize mi?", "options": ["Dağ", "Deniz"]},
    {"question": "Öğle yemeğinde ne yiyelim?", "options": ["Pizza", "Lahmacun", "Salata", "Burger"]},
    {"question": "Yeni telefon rengi hangisi olsun?", "options": ["Siyah", "Beyaz", "Mavi", "Yeşil", "Mor"]},
    {"question": "Akşam dizisi mi film mi izlesek?", "options": ["Dizi", "Film"]},
    {"question": "Tatil için hangi şehir?", "options": ["İstanbul", "İzmir", "Antalya", "Bodrum"]},
    {"question": "Kahve mi çay mı içmeliyim?", "options": ["Kahve", "Çay"]},
    {"question": "Spor salonuna mı yürüyüşe mi gitsem?", "options": ["Spor salonu", "Yürüyüş"]},
    {"question": "Yeni kitap hangi türde olsun?", "options": ["Bilim kurgu", "Polisiye", "Roman"]},
    {"question": "Doğum günü partisi nerede olsun?", "options": ["Evde", "Restoranda", "Parkta"]},
    {"question": "Bu hafta sonu ne pişirsem?", "options": ["Makarna", "Çorba", "Kebap", "Vegan yemek"]},
    {"question": "Yeni evcil hayvan hangisi olmalı?", "options": ["Kedi", "Köpek", "Balık", "Kuş", "Tavşan"]},
]


class Command(BaseCommand):
    help = "Demo veri üretir: 3 kullanıcı, 12 anket, rastgele oylar."

    @transaction.atomic
    def handle(self, *args, **options):
        Vote.objects.all().delete()
        Option.objects.all().delete()
        Poll.objects.all().delete()

        users = [self._get_or_create_user(data) for data in DEMO_USERS]

        for index, poll_data in enumerate(DEMO_POLLS):
            author = users[index % len(users)]
            status = Poll.STATUS_CLOSED if index % 5 == 0 else Poll.STATUS_ACTIVE
            poll = Poll.objects.create(
                question=poll_data["question"],
                author=author,
                status=status,
            )
            options = [
                Option.objects.create(poll=poll, text=text, position=position)
                for position, text in enumerate(poll_data["options"])
            ]
            self._cast_random_votes(poll, options, users)

        self.stdout.write(
            self.style.SUCCESS(f"{len(users)} kullanıcı, {len(DEMO_POLLS)} anket oluşturuldu.")
        )

    @staticmethod
    def _get_or_create_user(data):
        user, _ = User.objects.get_or_create(
            username=data["username"], defaults={"email": data["email"]}
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    @staticmethod
    def _cast_random_votes(poll, options, users):
        voters = [user for user in users if random.random() < 0.7]
        anon_count = random.randint(0, 6)

        for user in voters:
            option = random.choice(options)
            Vote.objects.create(
                poll=poll, option=option, user=user, voter_key=secrets.token_hex(16)
            )
            Option.objects.filter(pk=option.pk).update(vote_count=F("vote_count") + 1)
            Poll.objects.filter(pk=poll.pk).update(total_votes=F("total_votes") + 1)

        for _ in range(anon_count):
            option = random.choice(options)
            Vote.objects.create(
                poll=poll, option=option, user=None, voter_key=secrets.token_hex(16)
            )
            Option.objects.filter(pk=option.pk).update(vote_count=F("vote_count") + 1)
            Poll.objects.filter(pk=poll.pk).update(total_votes=F("total_votes") + 1)
