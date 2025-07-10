from django.forms import CharField, DateField
from django.core.exceptions import ValidationError
from datetime import date

def validate_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calc_digit(cpf_slice, length):
        weights = list(range(length + 1, 1, -1))
        total = sum(int(d) * w for d, w in zip(cpf_slice, weights))
        return (total * 10 % 11) % 10

    d1 = calc_digit(cpf[:9], 9)
    d2 = calc_digit(cpf[:10], 10)

    return cpf[-2:] == f"{d1}{d2}"


class CPFField(CharField):
    default_error_messages = {
        'invalid': 'CPF inválido.',
    }

    def clean(self, value):
        value = super().clean(value)
        if value and not validate_cpf(value):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        return value


class DateOfBirthField(DateField):
    def __init__(self, *args, min_age=18, **kwargs):
        self.min_age = min_age
        super().__init__(*args, **kwargs)

    def clean(self, value):
        dob = super().clean(value)
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < self.min_age:
                raise ValidationError(f"Você precisa ter pelo menos {self.min_age} anos.")
        return dob
