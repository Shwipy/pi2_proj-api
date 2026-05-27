import psycopg2
import os

def get_connection():
    return psycopg2.connect(os.getenv("DB"))

def get_cursor():
    return get_connection().cursor()