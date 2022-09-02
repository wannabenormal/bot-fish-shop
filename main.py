import os

from dotenv import load_dotenv

from moltin_connection import MoltinConnection

if __name__ == '__main__':
    load_dotenv()

    base_url = os.getenv('MOLTIN_BASE_URL')
    client_id = os.getenv('MOLTIN_CLIENT_ID')
    moltin = MoltinConnection(base_url, client_id)
    temp_id = '5605018d-92a5-42f7-bf2c-8855ec84fff4'
    moltin.add_to_cart(1, temp_id, quantity=2)

    print(moltin.get_user_cart(1))
