import os
from src.utils.json_storage import JsonStorage


class APIConfig:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.json_path = os.path.join(self.script_dir, 'data', 'endpoints', 'session_data.json')
        self.json_storage = JsonStorage(self.json_path)
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from JSON file"""
        config = self.json_storage.load_data()
        if not config:
            raise ValueError("Failed to load API configuration from JSON file")
        return config

    @property
    def session_id(self):
        return self.config.get('session_id')

    @property
    def transaction_guid(self):
        return self.config.get('transaction_guid')

    @property
    def transaction_number(self):
        return self.config.get('transaction_number')

    @property
    def table_number(self):
        return self.config.get('table_number')

    @property
    def property_id(self):
        return self.config.get('property_id')

    @property
    def revenue_center_id(self):
        return self.config.get('revenue_center_id')

    @property
    def client_id(self):
        return self.config.get('client_id')

    @property
    def subscription_key(self):
        return self.config.get('subscription_key')

    @property
    def base_url(self):
        return self.config.get('base_url')

    def get_headers(self):
        """Get headers for API requests"""
        return {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }

    def get_payload(self, session_id=None):
        """Get common payload for API requests"""
        return {
            "PropertyID": self.property_id,
            "RevenueCenterID": self.revenue_center_id,
            "ClientID": self.client_id,
            "SessionID": session_id or self.session_id,
            "TableNumber": self.table_number,
            "TransactionGUID": self.transaction_guid,
        } 