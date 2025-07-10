from django.db import models
from django.conf import settings


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        CANCELLED = 'cancelled', 'Cancelled'
        REJECTED = 'rejected', 'Rejected'
        REFUNDED = 'refunded', 'Refunded'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    plan = models.ForeignKey(
        'Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_id = models.CharField(max_length=100, unique=True)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)
    external_reference = models.CharField(max_length=255, blank=True, null=True)
    payment_type_id = models.CharField(max_length=50, blank=True, null=True)
    net_received_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    payer_email = models.EmailField()

    def __str__(self):
        return f'Payment #{self.id} - {self.status}'
