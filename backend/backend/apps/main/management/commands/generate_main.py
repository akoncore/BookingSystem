"""
Django Management Command for generating test data for Main app

Usage:
    python manage.py generate_main
    python manage.py generate_main --salons 5 --masters 10 --bookings 20
    python manage.py generate_main --clear  # Clear all data first
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.utils import timezone
from datetime import timedelta, time, datetime
import random

from apps.main.models import Salon, Master, Service, Booking, WorkSchedule


class Command(BaseCommand):
    help = 'Generate test data for Main app (Salons, Masters, Services, Bookings)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--salons',
            type=int,
            default=3,
            help='Number of salons to create'
        )
        parser.add_argument(
            '--masters',
            type=int,
            default=5,
            help='Number of masters per salon'
        )
        parser.add_argument(
            '--services',
            type=int,
            default=8,
            help='Number of services per salon'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=15,
            help='Number of bookings to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating'
        )

    def handle(self, *args, **options):
        # Get User model dynamically
        User = apps.get_model('auths', 'CustomUser')
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Booking.objects.all().delete()
            WorkSchedule.objects.all().delete()
            Master.objects.all().delete()
            Service.objects.all().delete()
            Salon.objects.all().delete()
            # Don't delete users, keep them
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        # Get or create users
        admins = self._get_or_create_admins(User, options['salons'])
        masters = self._get_or_create_masters(User, options['salons'] * options['masters'])
        clients = self._get_or_create_clients(User, 10)

        # Generate data
        salons = self._generate_salons(admins, options['salons'])
        self._generate_masters(salons, masters, options['masters'])
        self._generate_services(salons, options['services'])
        self._generate_work_schedules()
        self._generate_bookings(salons, clients, options['bookings'])

        self.stdout.write(self.style.SUCCESS('\n=== Generation Complete ==='))
        self.stdout.write(f"✓ {Salon.objects.count()} Salons")
        self.stdout.write(f"✓ {Master.objects.count()} Masters")
        self.stdout.write(f"✓ {Service.objects.count()} Services")
        self.stdout.write(f"✓ {WorkSchedule.objects.count()} Work Schedules")
        self.stdout.write(f"✓ {Booking.objects.count()} Bookings")

    def _get_or_create_admins(self, User, count):
        """Get or create admin users"""
        self.stdout.write('Creating admin users...')
        admins = []
        
        for i in range(count):
            email = f'admin{i+1}@salon.kz'
            admin, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': f'Admin {i+1}',
                    'role': 'admin',
                    'phone': f'+7701234{i:04d}',
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                admin.set_password('admin123')
                admin.save()
                self.stdout.write(f'  Created: {email}')
            admins.append(admin)
        
        return admins

    def _get_or_create_masters(self, User, count):
        """Get or create master users"""
        self.stdout.write('Creating master users...')
        masters = []
        
        for i in range(count):
            email = f'master{i+1}@salon.kz'
            master, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': f'Master {i+1}',
                    'role': 'master',
                    'phone': f'+7702345{i:04d}',
                    'is_active': True
                }
            )
            if created:
                master.set_password('master123')
                master.save()
                self.stdout.write(f'  Created: {email}')
            masters.append(master)
        
        return masters

    def _get_or_create_clients(self, User, count):
        """Get or create client users"""
        self.stdout.write('Creating client users...')
        clients = []
        
        for i in range(count):
            email = f'client{i+1}@test.kz'
            client, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': f'Client {i+1}',
                    'role': 'client',
                    'phone': f'+7703456{i:04d}',
                    'is_active': True
                }
            )
            if created:
                client.set_password('client123')
                client.save()
                self.stdout.write(f'  Created: {email}')
            clients.append(client)
        
        return clients

    def _generate_salons(self, admins, count):
        """Generate salons"""
        self.stdout.write('\nGenerating salons...')
        salons = []
        
        salon_names = [
            'Elite Barbershop', 'Royal Cut', 'Style Master',
            'Premium Salon', 'Gentleman\'s Choice', 'Modern Barber',
            'Classic Style', 'Urban Cuts', 'Luxury Salon'
        ]
        
        addresses = [
            'Almaty, Dostyk Ave, 123',
            'Almaty, Abai Ave, 45',
            'Almaty, Furmanov St, 89',
            'Almaty, Zheltoqsan St, 67',
            'Almaty, Baitursynov St, 34'
        ]
        
        for i in range(min(count, len(admins))):
            salon = Salon.objects.create(
                name=salon_names[i % len(salon_names)],
                address=addresses[i % len(addresses)],
                owner=admins[i],
                phone=f'+77011{i:06d}',
                description=f'Professional barbershop with experienced masters',
                is_active=True
            )
            salons.append(salon)
            self.stdout.write(f'  ✓ {salon.name}')
        
        return salons

    def _generate_masters(self, salons, master_users, count_per_salon):
        """Generate master profiles"""
        self.stdout.write('\nGenerating master profiles...')
        
        specializations = [
            'Hair Stylist', 'Beard Specialist', 'Classic Haircut',
            'Modern Styles', 'Coloring Expert', 'All-round Barber'
        ]
        
        master_idx = 0
        for salon in salons:
            for _ in range(count_per_salon):
                if master_idx >= len(master_users):
                    break
                    
                master = Master.objects.create(
                    user=master_users[master_idx],
                    salon=salon,
                    specialization=random.choice(specializations),
                    experience_years=random.randint(1, 15),
                    bio=f'Professional barber with passion for styling',
                    is_approved=True
                )
                self.stdout.write(f'  ✓ {master.user.full_name} at {salon.name}')
                master_idx += 1

    def _generate_services(self, salons, count_per_salon):
        """Generate services"""
        self.stdout.write('\nGenerating services...')
        
        services_data = [
            ('Classic Haircut', 3000, 30),
            ('Beard Trim', 1500, 20),
            ('Hair + Beard', 4000, 45),
            ('Styling', 2000, 25),
            ('Coloring', 5000, 60),
            ('Shaving', 2500, 30),
            ('Kids Haircut', 2000, 25),
            ('VIP Service', 8000, 90),
        ]
        
        for salon in salons:
            for name, price, duration in services_data[:count_per_salon]:
                service = Service.objects.create(
                    name=name,
                    description=f'{name} - professional service',
                    price=price,
                    duration=timedelta(minutes=duration),
                    salon=salon,
                    is_active=True
                )
                self.stdout.write(f'  ✓ {service.name} at {salon.name}')

    def _generate_work_schedules(self):
        """Generate work schedules for all masters"""
        self.stdout.write('\nGenerating work schedules...')
        
        masters = Master.objects.filter(is_approved=True)
        
        for master in masters:
            # Monday to Friday: 9:00 - 18:00
            for weekday in range(5):
                WorkSchedule.objects.create(
                    master=master.user,
                    weekday=weekday,
                    start_time=time(9, 0),
                    end_time=time(18, 0),
                    is_working=True
                )
            
            # Saturday: 10:00 - 16:00
            WorkSchedule.objects.create(
                master=master.user,
                weekday=5,
                start_time=time(10, 0),
                end_time=time(16, 0),
                is_working=True
            )
            
            # Sunday: day off
            WorkSchedule.objects.create(
                master=master.user,
                weekday=6,
                start_time=time(0, 0),
                end_time=time(0, 0),
                is_working=False
            )
            
            self.stdout.write(f'  ✓ Schedule for {master.user.full_name}')

    def _generate_bookings(self, salons, clients, count):
        """Generate bookings"""
        self.stdout.write('\nGenerating bookings...')
        
        statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        status_weights = [0.3, 0.4, 0.2, 0.1]  # Distribution
        
        for i in range(count):
            salon = random.choice(salons)
            master_profile = random.choice(list(salon.masters.filter(is_approved=True)))
            client = random.choice(clients)
            
            # Random date: from 7 days ago to 14 days ahead
            days_offset = random.randint(-7, 14)
            appointment_date = timezone.now().date() + timedelta(days=days_offset)
            
            # Random time between 9:00 and 17:00
            hour = random.randint(9, 16)
            minute = random.choice([0, 30])
            appointment_time = time(hour, minute)
            
            # Status based on date
            if appointment_date < timezone.now().date():
                status = random.choices(['completed', 'cancelled'], weights=[0.8, 0.2])[0]
            else:
                status = random.choices(statuses, weights=status_weights)[0]
            
            booking = Booking.objects.create(
                client=client,
                master=master_profile.user,
                salon=salon,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=status,
                notes=f'Auto-generated booking #{i+1}'
            )
            
            # Add 1-3 random services
            services = random.sample(
                list(salon.services.filter(is_active=True)),
                k=min(random.randint(1, 3), salon.services.count())
            )
            booking.services.set(services)
            booking.calculate_total_price()
            booking.save()
            
            self.stdout.write(
                f'  ✓ Booking {booking.booking_code}: '
                f'{client.full_name} → {master_profile.user.full_name} '
                f'({appointment_date})'
            )