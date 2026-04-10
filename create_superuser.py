import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produção.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'lucas')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'senha123')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, password=password, email=email)
    print(f'Superusuário "{username}" criado com sucesso!')
else:
    print(f'Usuário "{username}" já existe.')