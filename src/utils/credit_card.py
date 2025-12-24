from faker import Faker


def generate_customer():
    fake = Faker('en_US')
    full_name = fake.name().replace('.', '')
    email = f'{full_name.replace(" ", "_")}@hmshost.com'
    phone_number = fake.phone_number()
    return {
        'fullname': full_name,
        'email': email,
        'phone_number': phone_number,
        'number': '4111111111111111',
        'exp': '12/27',
        'cvv': '123',
        'zip': '11111'
    }
