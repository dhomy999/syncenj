"""
Quick authentication test.
Run from project root:
    python scripts/test_auth.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import validate, USERNAME
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.utils.logger import logger


def main():
    try:
        validate()
    except EnvironmentError as e:
        logger.error(str(e))
        logger.info("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    logger.info(f"Testing authentication for user: {USERNAME}")

    with EnjaziClient() as client:
        token = get_valid_token(client)
        logger.success(f"Token acquired: {token[:25]}...")
        logger.info("Authentication system working correctly.")


if __name__ == "__main__":
    main()
