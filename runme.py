# -*- coding: UTF-8 -*-
"""
    Unit Test Lab
    2025-03-27
    Description:
    
"""

import os
import asyncio

from src import main


def load_environ():
    try:
        with open(".env", "r") as f:
            for line in f:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip()
        return True
    except FileNotFoundError:
        return False


def check_environ():
    if "BOT_TOKEN" not in os.environ:
        print("BOT_TOKEN is not set in the environment.")
        return False
    if "HOST" not in os.environ:
        print("HOST is not set in the environment.")
        return False
    if "PORT" not in os.environ:
        print("PORT is not set in the environment.")
        return False
    if "POSTGRES_DB" not in os.environ:
        print("POSTGRES_DB is not set in the environment.")
        return False
    if "POSTGRES_PASSWORD" not in os.environ:
        print("POSTGRES_PASSWORD is not set in the environment.")
        return False
    if "POSTGRES_USER" not in os.environ:
        print("POSTGRES_USER is not set in the environment.")
        return False
    return True


if __name__ == "__main__":
    load_environ()
    # check if all required environment variables are set
    if not check_environ():
        exit(1)
    try:
        asyncio.run(main())
        pass
    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...")
    except SystemExit:
        print("System exit. Shutting down...")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
    finally:
        print("Server stopped.")
    exit(0)

