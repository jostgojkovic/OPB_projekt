
from datetime import datetime as dt, timedelta
# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

from typing import List, TypeVar, Type, Callable
from Data.Modeli import *    #uvozimo classe tabel
import os

#from pandas import DataFrame
#from re import sub
import Data.auth_public as auth  
from datetime import date

DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

class Repo:

    def __init__(self):
        self.conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def dodaj_stranka(self, Stranka: Stranka) -> Stranka:
        # ali je že v tabeli?
        self.cur.execute("""
            SELECT * from stranka
            WHERE "username" = %s
          """, (Stranka.username,))

        row = self.cur.fetchone()
        if row:
            Stranka.id = row[0]
            return Stranka
        
        #nov uporabnik
        self.cur.execute("""
            INSERT INTO stranka ("name", "username", "password")
              VALUES (%s, %s, %s); """, (Stranka.name, Stranka.username, Stranka.password))
        self.conn.commit()
        return Stranka
    
    def dodaj_rezervacije(self, Rezervacija:Rezervacija) -> Rezervacija:
        self.cur.execute("""
            INSERT INTO rezervacija ("stevilo_gostov", "id_stranke", "cas_rezervacije", "konec_rezervacije","miza_id")
              VALUES (%s, %s, %s, %s, %s)
              returning id """, (Rezervacija.stevilo_gostov, Rezervacija.id_stranke, Rezervacija.cas_rezervacije, Rezervacija.konec_rezervacije, Rezervacija.miza_id))
        id,=self.cur.fetchone()
        self.conn.commit()
        return Rezervacija
    

    def dodaj_vsebina_rezervacije(self, Vsebina_rezervacije:Vsebina_rezervacije) -> Vsebina_rezervacije:
        self.cur.execute("""
            INSERT INTO vsebina_rezervacije ("rezervacija_id", "meni_id", "cena")
              VALUES (%s, %s, %s)
              returning id """, (Vsebina_rezervacije.rezervacija_id, Vsebina_rezervacije.meni_id, Vsebina_rezervacije.cena))
        id,=self.cur.fetchone()
        self.conn.commit()
        return Vsebina_rezervacije

    
