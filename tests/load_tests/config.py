"""
Load Test Configuration
"""
import os

# API Configuration
BASE_URL = "https://digitalmwqa.azure-api.net"
API_KEY = "bf837e849a7948308c103d08c3b731ce"
CLIENT_ID = "3289FE1A-A4CA-49DC-9CDF-C2831781E850"

PROPERTY_ID = "33"
REVENUE_CENTER_ID = "810"
EMPLOYEE_NUMBER = 90004

# Test Duration
TEST_DURATION_SECONDS = int(os.getenv('TEST_DURATION', '1800'))  # Default: 5 minutes

# Table Range
TABLE_START = int(os.getenv('TABLE_START', '51'))
TABLE_END = int(os.getenv('TABLE_END', '70'))  # Default: 30 tables

# User spawn rate (doesn't matter much, just for setup)
SPAWN_RATE = int(os.getenv('SPAWN_RATE', '10'))

def get_user_count():
    return TABLE_END - TABLE_START + 1

# Allure
ALLURE_RESULTS_DIR = "allure-results"
LOCUST_RESULTS_FILE = "locust_stats.json"

# Report metadata
TEST_METADATA = {
    "environment": "QA",
    "application": "QR Ordering System",
    "test_type": "Synchronized Load Test",
    "tester": "QA Automation Team"
}