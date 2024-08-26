from django.http import JsonResponse
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()


def run_migrations(request):
    app = request.GET.get('app', None)
    number = request.GET.get('number', None)

    args = []
    if app:
        args.append(app)
    if number:
        args.append(number)

    call_command('migrate', *args)

    return JsonResponse({'message': 'Migrations completed successfully'})


def create_superuser(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        return JsonResponse({'message': 'Superuser created successfully'})
    else:
        return JsonResponse({'message': 'Superuser already exists'})


def run_collectstatic(request):
    try:
        call_command('collectstatic', '--no-input')
        return JsonResponse({'message': 'Collectstatic executado com sucesso.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
