from django.urls import path
from cbo.api.payment.views import PaymentCheckoutModalView

urlpatterns = [
    path('checkout/modal/', PaymentCheckoutModalView.as_view(), name='checkout_modal'),
]
