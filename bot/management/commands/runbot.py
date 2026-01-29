"""
Django management command to run the Telegram bot
Usage: python manage.py runbot
"""
from django.core.management.base import BaseCommand
from bot.bot import main


class Command(BaseCommand):
    help = 'Run the Eagles View Telegram Bot'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Eagles View Bot...'))
        main()
