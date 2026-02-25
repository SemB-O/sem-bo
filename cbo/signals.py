from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import FavoriteProceduresFolder

User = get_user_model()

@receiver(post_save, sender=User)
def create_default_favorite_folder(sender, instance, created, **kwargs):
    if created:
        FavoriteProceduresFolder.objects.get_or_create(
            user=instance,
            name="Geral",
            defaults={'description': "Meus Favoritos"}
        )
