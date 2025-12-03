from faker import Faker

# fake = Faker('en_US')
# full_name = fake.name().replace('.', '')
# email = f'{full_name.replace(" ", "_")}@hmshost.com'
# # email = 'sousa74733@wbd4l.awesome47.com'
# phone_number = fake.phone_number()
# TEST_CARD = {
#         'fullname': full_name,
#         'email': email,
#         'phone_number': phone_number,
#         'number': '4111111111111111',
#         'exp': '12/27',
#         'cvv': '123',
#         'zip': '11111'
#     }

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
