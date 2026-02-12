from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError

User = get_user_model()


class Command(BaseCommand):
    """
    Django management command for user operations
    
    Usage:
        python manage.py users --create
        python manage.py users --list
        python manage.py users --delete <email>
        python manage.py users --activate <email>
        python manage.py users --deactivate <email>
        python manage.py users --make-staff <email>
        python manage.py users --remove-staff <email>
    """
    
    help = 'Manage users in the system'

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments"""
        
        # Create user
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create a new user interactively'
        )
        
        # Create superuser
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a new superuser interactively'
        )
        
        # List users
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all users'
        )
        
        # Delete user
        parser.add_argument(
            '--delete',
            type=str,
            help='Delete user by email'
        )
        
        # Activate user
        parser.add_argument(
            '--activate',
            type=str,
            help='Activate user by email'
        )
        
        # Deactivate user
        parser.add_argument(
            '--deactivate',
            type=str,
            help='Deactivate user by email'
        )
        
        # Make staff
        parser.add_argument(
            '--make-staff',
            type=str,
            help='Grant staff status to user by email'
        )
        
        # Remove staff
        parser.add_argument(
            '--remove-staff',
            type=str,
            help='Remove staff status from user by email'
        )
        
        # Get user info
        parser.add_argument(
            '--info',
            type=str,
            help='Get detailed information about user by email'
        )
        
        # Count users
        parser.add_argument(
            '--count',
            action='store_true',
            help='Count total users'
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command"""
        
        if options['create']:
            self._create_user(is_superuser=False)
        
        elif options['create_superuser']:
            self._create_user(is_superuser=True)
        
        elif options['list']:
            self._list_users()
        
        elif options['delete']:
            self._delete_user(options['delete'])
        
        elif options['activate']:
            self._activate_user(options['activate'])
        
        elif options['deactivate']:
            self._deactivate_user(options['deactivate'])
        
        elif options['make_staff']:
            self._make_staff(options['make_staff'])
        
        elif options['remove_staff']:
            self._remove_staff(options['remove_staff'])
        
        elif options['info']:
            self._get_user_info(options['info'])
        
        elif options['count']:
            self._count_users()
        
        else:
            self.stdout.write(
                self.style.WARNING('No action specified. Use --help for available options.')
            )

    def _create_user(self, is_superuser: bool = False) -> None:
        """Create a new user interactively"""
        
        user_type = "superuser" if is_superuser else "user"
        self.stdout.write(self.style.SUCCESS(f'\n=== Creating new {user_type} ===\n'))
        
        try:
            # Get email
            email = input('Email: ').strip()
            if not email:
                self.stdout.write(self.style.ERROR('Email cannot be empty'))
                return
            
            # Check if user exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.ERROR(f'User with email {email} already exists'))
                return
            
            # Get full name
            full_name = input('Full Name: ').strip()
            if not full_name:
                self.stdout.write(self.style.ERROR('Full name cannot be empty'))
                return
            
            # Get password
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
                return
            
            # Create user
            if is_superuser:
                user = User.objects.create_superuser(
                    email=email,
                    full_name=full_name,
                    password=password
                )
            else:
                user = User.objects.create_user(
                    email=email,
                    full_name=full_name,
                    password=password
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ {user_type.capitalize()} created successfully!')
            )
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Name: {user.full_name}')
            self.stdout.write(f'  Staff: {user.is_staff}')
            self.stdout.write(f'  Superuser: {user.is_superuser}\n')
            
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f'Validation error: {e}'))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'Database error: {e}'))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n\nOperation cancelled'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def _list_users(self) -> None:
        """List all users"""
        
        users = User.objects.all().order_by('-id')
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Total Users: {users.count()} ===\n'))
        
        # Header
        self.stdout.write(
            f"{'ID':<6} {'EMAIL':<30} {'NAME':<25} {'ACTIVE':<8} {'STAFF':<8} {'SUPER':<8}"
        )
        self.stdout.write('-' * 90)
        
        # Users
        for user in users:
            active_icon = '✓' if user.is_active else '✗'
            staff_icon = '✓' if user.is_staff else '✗'
            super_icon = '✓' if user.is_superuser else '✗'
            
            self.stdout.write(
                f"{user.id:<6} {user.email:<30} {user.full_name:<25} "
                f"{active_icon:<8} {staff_icon:<8} {super_icon:<8}"
            )
        
        self.stdout.write('')

    def _delete_user(self, email: str) -> None:
        """Delete user by email"""
        
        try:
            user = User.objects.get(email=email)
            
            # Confirmation
            confirm = input(f'Are you sure you want to delete user "{user.full_name}" ({user.email})? [y/N]: ')
            
            if confirm.lower() == 'y':
                user.delete()
                self.stdout.write(self.style.SUCCESS(f'✓ User {email} deleted successfully'))
            else:
                self.stdout.write(self.style.WARNING('Operation cancelled'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def _activate_user(self, email: str) -> None:
        """Activate user"""
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_active:
                self.stdout.write(self.style.WARNING(f'User {email} is already active'))
            else:
                user.is_active = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ User {email} activated successfully'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def _deactivate_user(self, email: str) -> None:
        """Deactivate user"""
        
        try:
            user = User.objects.get(email=email)
            
            if not user.is_active:
                self.stdout.write(self.style.WARNING(f'User {email} is already inactive'))
            else:
                user.is_active = False
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ User {email} deactivated successfully'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def _make_staff(self, email: str) -> None:
        """Grant staff status"""
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_staff:
                self.stdout.write(self.style.WARNING(f'User {email} is already staff'))
            else:
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ User {email} granted staff status'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def _remove_staff(self, email: str) -> None:
        """Remove staff status"""
        
        try:
            user = User.objects.get(email=email)
            
            if not user.is_staff:
                self.stdout.write(self.style.WARNING(f'User {email} is not staff'))
            else:
                user.is_staff = False
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Staff status removed from {email}'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def _get_user_info(self, email: str) -> None:
        """Get detailed user information"""
        
        try:
            user = User.objects.get(email=email)
            
            self.stdout.write(self.style.SUCCESS('\n=== User Information ===\n'))
            self.stdout.write(f'ID: {user.id}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Full Name: {user.full_name}')
            self.stdout.write(f'Active: {"Yes" if user.is_active else "No"}')
            self.stdout.write(f'Staff: {"Yes" if user.is_staff else "No"}')
            self.stdout.write(f'Superuser: {"Yes" if user.is_superuser else "No"}')
            self.stdout.write(f'Last Login: {user.last_login or "Never"}')
            self.stdout.write('')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def _count_users(self) -> None:
        """Count users"""
        
        total = User.objects.count()
        active = User.objects.filter(is_active=True).count()
        staff = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(self.style.SUCCESS('\n=== User Statistics ===\n'))
        self.stdout.write(f'Total Users: {total}')
        self.stdout.write(f'Active Users: {active}')
        self.stdout.write(f'Staff Users: {staff}')
        self.stdout.write(f'Superusers: {superusers}')
        self.stdout.write('')