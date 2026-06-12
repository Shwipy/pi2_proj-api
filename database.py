import psycopg2
import os

def get_connection():

    con = psycopg2.connect(os.getenv("DB"))
    
    return con,con.cursor() 