from environs import Env

from moltin_connection import MoltinConnection

if __name__ == '__main__':
    env = Env()
    env.read_env()

    base_url = env.str('MOLTIN_BASE_URL')
    client_id = env.str('MOLTIN_CLIENT_ID')
    moltin = MoltinConnection(base_url, client_id)

    print(moltin.get_products())
