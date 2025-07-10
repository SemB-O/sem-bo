import mercadopago
from django.conf import settings


class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

    def create_payment(self, amount, token, description, installments, payment_method_id, payer_email):
        payment_data = {
            "transaction_amount": float(amount),
            "token": token,
            "description": description,
            "installments": installments,
            "payment_method_id": payment_method_id,
            "payer": {
                "email": payer_email
            }
        }
        response = self.sdk.payment().create(payment_data)
        return response["response"]

    def create_checkout_preference(self, plan, user_data):
        preference_data = {
            "items": [
                {
                    "title": f"Assinatura do plano {plan.name}",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": float(plan.price),
                }
            ],
            "payer": {
                "email": user_data.get("email")
            },
            "external_reference": f"{user_data.get('email')}:{plan.id}",
            "notification_url": "https://seusite.com/api/payment/webhook/", 
        }

        response = self.sdk.preference().create(preference_data)
        return response["response"]["id"]

