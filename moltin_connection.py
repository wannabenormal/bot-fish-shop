from datetime import datetime

import requests


class MoltinConnection():
    def __init__(self, base_url, client_id):
        self.base_url = base_url
        self.client_id = client_id
        self.access_token = None
        self.access_token_expires = None

    def get_products(self):
        self.__check_or_update_token()

        response = requests.get(
            f'{self.base_url}/v2/products',
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        response.raise_for_status()

        return response.json()

    def get_user_cart(self, userId):
        self.__check_or_update_token()

        response = requests.get(
            f'{self.base_url}/v2/carts/{userId}/items',
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        response.raise_for_status()

        return response.json()

    def add_to_cart(self, userId, productId, quantity=1):
        self.__check_or_update_token()

        product = {
            'data': {
                'id': productId,
                'quantity': quantity,
                'type': 'cart_item',
            }
        }

        response = requests.post(
            f'{self.base_url}/v2/carts/{userId}/items',
            json=product,
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        response.raise_for_status()

        return response.json()

    def __check_or_update_token(self, grant_type='implicit'):
        now = datetime.now()
        ts = datetime.timestamp(now)

        if not self.access_token or ts > self.access_token_expires:
            response = requests.post(
                f'{self.base_url}/oauth/access_token',
                {
                    'client_id': self.client_id,
                    'grant_type': grant_type
                }
            )

            response.raise_for_status()
            token_info = response.json()
            self.access_token = token_info['access_token']
            self.access_token_expires = token_info['expires']
