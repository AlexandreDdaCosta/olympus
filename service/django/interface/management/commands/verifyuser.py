from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Verifies user exists.  Sets admin/superuser status as requested.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin',
            action='store_true',
            default=False,
            dest='admin',
            help='Give admin privileges',
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            default=False,
            dest='disable',
            help='Turn off user access',
        )
        parser.add_argument(
            '--email',
            action='store',
            dest='email',
            help='Setting for user email address',
        )
        parser.add_argument(
            '--groups',
            action='store',
            dest='groups',
            help='User permission groups',
        )
        parser.add_argument(
            '--password',
            action='store',
            dest='password',
            help='Setting for user password',
        )
        parser.add_argument(
            '--resave',
            action='store_true',
            default=False,
            dest='resave',
            help='Force update of all specified parameters',
        )
        parser.add_argument(
            '--resave_password',
            action='store_true',
            default=False,
            dest='resave_password',
            help='Force update user password',
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            default=False,
            dest='superuser',
            help='Give superuser privileges',
        )
        parser.add_argument(
            '--through',
            action='store',
            dest='through',
        )
        parser.add_argument(
            '--username',
            action='store',
            dest='username',
            help='ID of user being updated/added',
        )

    def handle(self, *args, **options):
        disable = options.get('disable')
        password = options.get('password')
        username = options.get('username')
        if disable and username:
            try:
                user = User.objects.get(username=username)
                user.set_password(username)
                user.is_active = False
                user.save()
            except User.DoesNotExist:
                pass
        elif password and username:
            user, created = User.objects.get_or_create(username=username)
            if user and (created or options.get('resave')):
                if (created or
                    (options.get('resave') and
                     options.get('resave_password'))):
                    user.set_password(password)
                if options.get('email'):
                    user.email = options.get('email')
                user.is_staff = options.get('admin')
                user.is_active = True
                user.is_superuser = options.get('superuser')
                user.save()
                if options.get('groups'):
                    groups = options.get('groups').split(',')
                    for group in groups:
                        g = Group.objects.get(name=group)
                        g.user_set.add(user)
        else:
            raise Exception("Missing parameter.")
