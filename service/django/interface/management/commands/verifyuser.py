from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from optparse import make_option

import os

class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('--admin','-a',dest='admin',action='store_true',default=False),
		make_option('--disable','-d',dest='disable',action='store_true',default=False),
		make_option('--email','-e',dest='email',action='store'),
		make_option('--groups','-g',dest='groups',action='store'),
		make_option('--password','-p',dest='password',action='store'),
		make_option('--resave','-r',dest='resave',action='store_true',default=False),
		make_option('--resave_password','-f',dest='resave_password',action='store_true',default=False),
		make_option('--superuser','-s',dest='superuser',action='store_true',default=False),
		make_option('--through','-t',dest='through',action='store'),
		make_option('--username','-u',dest='username',action='store'),
	)
	help = 'Verifies user exists.  Sets admin/superuser status as requested.'

	def handle(self, **options):
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
				if created or (options.get('resave') and options.get('resave_password')):
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
