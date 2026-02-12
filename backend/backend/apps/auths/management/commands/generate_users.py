from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import random

User = get_user_model()


class Command(BaseCommand):
    """
    Generate fake users for testing
    
    Usage:
        python manage.py generate_users
        python manage.py generate_users --count 50
        python manage.py generate_users --count 10 --with-superuser
        python manage.py generate_users --clear
    """
    
    help = 'Generate fake users for testing purposes'
    
    # Fake data for generation
    FIRST_NAMES = [
        'Айдар', 'Ерлан', 'Асель', 'Дина', 'Нұрлан', 'Жанна', 'Бауыржан', 
        'Айгүл', 'Серік', 'Гүлнар', 'Алмас', 'Сауле', 'Қуаныш', 'Динара',
        'Ержан', 'Асем', 'Болат', 'Күнсұлу', 'Тимур', 'Жансая', 'Арман',
        'Малика', 'Дәурен', 'Айжан', 'Нұрбол', 'Камила', 'Ерболат', 'Айнұр',
        'John', 'Emma', 'Michael', 'Sarah', 'David', 'Lisa', 'James', 'Anna',
        'Robert', 'Maria', 'William', 'Elena', 'Richard', 'Sophie', 'Thomas'
    ]
    
    LAST_NAMES = [
        'Әбдіраман', 'Жұмабаев', 'Сейітова', 'Төлеген', 'Қасымов', 'Нұрланова',
        'Бекболат', 'Смағұлова', 'Есімов', 'Қожахметова', 'Мұхамеджан', 'Аманова',
        'Сатыбалды', 'Жақсылық', 'Темірбеков', 'Өтепова', 'Мұратбек', 'Серікова',
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
        'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson'
    ]
    
    DOMAINS = [
        'gmail.com', 'yahoo.com', 'outlook.com', 'mail.ru', 
        'yandex.kz', 'inbox.ru', 'hotmail.com', 'icloud.com'
    ]

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments"""
        
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of users to generate (default: 20)'
        )
        
        parser.add_argument(
            '--with-superuser',
            action='store_true',
            help='Create one superuser along with regular users'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing users before generating new ones'
        )
        
        parser.add_argument(
            '--password',
            type=str,
            default='password123',
            help='Default password for all generated users (default: password123)'
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command"""
        
        count = options['count']
        with_superuser = options['with_superuser']
        clear = options['clear']
        password = options['password']
        
        # Clear existing users if requested
        if clear:
            self._clear_users()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🚀 Generating {count} users...\n')
        )
        
        # Generate superuser if requested
        if with_superuser:
            self._generate_superuser(password)
        
        # Generate regular users
        self._generate_users(count, password)
        
        # Show summary
        self._show_summary()

    def _clear_users(self) -> None:
        """Delete all existing users"""
        
        confirm = input('⚠️  Are you sure you want to delete ALL users? [y/N]: ')
        
        if confirm.lower() == 'y':
            count = User.objects.count()
            User.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'✓ Deleted {count} existing users\n')
            )
        else:
            self.stdout.write(self.style.WARNING('Skipped clearing users\n'))

    def _generate_superuser(self, password: str) -> None:
        """Generate a superuser"""
        
        email = 'admin@admin.com'
        
        try:
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Superuser {email} already exists')
                )
            else:
                user = User.objects.create_superuser(
                    email=email,
                    full_name='Admin User',
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Superuser created: {email}')
                )
                self.stdout.write(f'  Password: {password}\n')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error creating superuser: {e}\n'))

    def _generate_users(self, count: int, password: str) -> None:
        """Generate regular users"""
        
        created = 0
        skipped = 0
        
        for i in range(count):
            try:
                # Generate random name
                first_name = random.choice(self.FIRST_NAMES)
                last_name = random.choice(self.LAST_NAMES)
                full_name = f'{first_name} {last_name}'
                
                # Generate email
                username = f'{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}'
                # Remove spaces and special characters
                username = username.replace(' ', '').replace('ә', 'a').replace('і', 'i')\
                    .replace('ң', 'n').replace('ғ', 'g').replace('ү', 'u').replace('ұ', 'u')\
                    .replace('қ', 'k').replace('ө', 'o').replace('һ', 'h')
                
                domain = random.choice(self.DOMAINS)
                email = f'{username}@{domain}'
                
                # Check if user exists
                if User.objects.filter(email=email).exists():
                    skipped += 1
                    continue
                
                # Create user
                user = User.objects.create_user(
                    email=email,
                    full_name=full_name,
                    password=password
                )
                
                # Randomly assign staff status (10% chance)
                if random.random() < 0.1:
                    user.is_staff = True
                    user.save()
                
                created += 1
                
                # Show progress
                if (created + skipped) % 10 == 0:
                    self.stdout.write(f'  Progress: {created + skipped}/{count}')
                
            except IntegrityError:
                skipped += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error: {e}'))
                skipped += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Created {created} users')
        )
        if skipped > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Skipped {skipped} users (duplicates or errors)')
            )

    def _show_summary(self) -> None:
        """Show summary of generated users"""
        
        total = User.objects.count()
        active = User.objects.filter(is_active=True).count()
        staff = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(
            self.style.SUCCESS('\n' + '='*50)
        )
        self.stdout.write(
            self.style.SUCCESS('📊 DATABASE SUMMARY')
        )
        self.stdout.write(
            self.style.SUCCESS('='*50)
        )
        self.stdout.write(f'Total Users:      {total}')
        self.stdout.write(f'Active Users:     {active}')
        self.stdout.write(f'Staff Users:      {staff}')
        self.stdout.write(f'Superusers:       {superusers}')
        self.stdout.write(
            self.style.SUCCESS('='*50 + '\n')
        )
        
        # Show some sample users
        sample_users = User.objects.all()[:5]
        
        if sample_users:
            self.stdout.write(self.style.SUCCESS('📝 Sample Users:'))
            self.stdout.write('-'*50)
            for user in sample_users:
                staff_badge = ' [STAFF]' if user.is_staff else ''
                super_badge = ' [SUPER]' if user.is_superuser else ''
                self.stdout.write(
                    f'  • {user.email}{staff_badge}{super_badge}'
                )
                self.stdout.write(f'    Name: {user.full_name}')
            self.stdout.write('-'*50 + '\n')
        
        # Show login credentials
        self.stdout.write(
            self.style.WARNING('🔑 Login Credentials:')
        )
        self.stdout.write('  Email: any generated email')
        self.stdout.write('  Password: password123 (or your custom password)')
        
        if User.objects.filter(email='admin@admin.com').exists():
            self.stdout.write('\n  Superuser:')
            self.stdout.write('  Email: admin@admin.com')
            self.stdout.write('  Password: password123 (or your custom password)')
        
        self.stdout.write('')