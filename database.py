
from datetime import datetime as dt, timedelta
# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

from typing import List, TypeVar, Type, Callable
from Data.Modeli import *    #uvozimo classe tabel
import os

#from pandas import DataFrame
#from re import sub

import Data.auth as auth  
from datetime import date

DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

class Repo:

    def __init__(self):
        self.conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    
    def tabela_stranka(self) -> List[Stranka]:
        self.cur.execute("""
            SELECT * FROM stranka
        """)
        return [Stranka(id, name, username, password) for (id, name, username, password) in self.cur.fetchall()]


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
    
    def dodaj_sef(self, Sef: Sef) -> Sef:
        # ali je že v tabeli?
        self.cur.execute("""
            SELECT * from sef
            WHERE "username" = %s
          """, (Sef.username,))

        row = self.cur.fetchone()
        if row:
            Sef.id = row[0]
            return Sef
        
        #nov uporabnik
        self.cur.execute("""
            INSERT INTO stranka ("name", "username", "password")
              VALUES (%s, %s, %s); """, (Sef.name, Sef.username, Sef.password))
        self.conn.commit()
        return Sef

    def tabela_rezervacije(self, datum) -> List[Rezervacija]:
        #funkcija prikaze tabelo rezervacij, ki so od datuma "datum" naprej 
        self.cur.execute("""
            SELECT * FROM rezervacija
            WHERE "cas_rezervacije" >= %s """, (datum)) #mogoce vejica
        return [Rezervacija(id, stevilo_gostov, id_stranke, cas_rezervacije, miza_id) for (id, stevilo_gostov, id_stranke, cas_rezervacije, miza_id) in self.cur.fetchall()]


    def dodaj_rezervacije(self, Rezervacija:Rezervacija) -> Rezervacija:
        self.cur.execute("""
            INSERT INTO rezervacija ("stevilo_gostov", "id_stranke", "cas_rezervacije","miza_id")
              VALUES (%s, %s, %s, %s)
              returning id """, (Rezervacija.stevilo_gostov, Rezervacija.id_stranke, Rezervacija.cas_rezervacije, Rezervacija.miza_id))
        id,=self.cur.fetchone()
        self.conn.commit()
        return Rezervacija
    
    def tabela_narocil(self, datum) -> List[Narocilo]:
        #funkcija prikaze tabelo vseh narocil 
        self.cur.execute(""" 
            SELECT * FROM narocilo """)
        return [Narocilo(id, status, cena, stranka_id) for (id, status, cena, stranka_id) in self.cur.fetchall()]

    def dodaj_narocilo(self, Narocilo:Narocilo) -> Narocilo:
        self.cur.execute("""
            INSERT INTO narocilo ("status", "cena", "stranka_id")
              VALUES (%s, %s, %s)
              returning id """, (Narocilo.status, Narocilo.cena, Narocilo.stranka_id))
        id,=self.cur.fetchone()
        self.conn.commit()
        return Narocilo

    def dodaj_vsebina_narocilo(self, Vsebina_narocil:Vsebina_narocil) -> Vsebina_narocil:
        self.cur.execute("""
            INSERT INTO vsebina_narocil ("narocilo_id", "meni_id", "cena")
              VALUES (%s, %s, %s)
              returning id """, (Vsebina_narocil.narocilo_id, Vsebina_narocil.meni_id, Vsebina_narocil.cena))
        id,=self.cur.fetchone()
        self.conn.commit()
        return Vsebina_narocil

    def tabela_vsebina_narocil(self) -> List[Vsebina_narocil]:
        #funkcija  
        self.cur.execute(""" 
            SELECT * FROM vsebin_narocil """)
        return [Vsebina_narocil(id, narocilo_id, meni_id, cena) for (id, narocilo_id, meni_id, cena) in self.cur.fetchall()]
        

    def dobi_proste_mize(self, datum_nove, st_gostov_nove):
        self.cur.execute(
            """SELECT miza.id FROM miza
            LEFT JOIN rezervacija ON rezervacija.miza_id = miza.id
            WHERE kapaciteta = %s AND miza.id NOT IN 
                (SELECT miza.id FROM miza
                LEFT JOIN rezervacija ON rezervacija.miza_id = miza.id WHERE
                DATEADD(hour,2, %s) > cas_rezervacije AND
                DATEADD(hour,-2, %s) < cas_rezervacije""",(int(st_gostov_nove), datum_nove, datum_nove, ))
        prosta_miza = self.cur.fetchone()
        return prosta_miza # mogce TODATE pri %s
    


#     def dobi_proste_parcele_brez_moje_rezervacije(self, id_rezervacije, datum_nove, st_dni_nove, st_odraslih, st_otrok):
#         self.cur.execute(
#             """SELECT parcela.id FROM parcela
#             LEFT JOIN rezervacije ON rezervacije.rezervirana_parcela = parcela.id
#             WHERE st_gostov >= %s AND parcela.id NOT IN 
#                 (SELECT parcela.id FROM parcela
#                 LEFT JOIN rezervacije ON rezervacije.rezervirana_parcela = parcela.id 
#                 WHERE NOT rezervacije.id = %s AND
#                 pricetek_bivanja + st_nocitev  > TO_DATE(%s, 'YYYY-MM-DD') AND
#                 pricetek_bivanja < TO_DATE(%s, 'YYYY-MM-DD') + %s)""",(int(st_odraslih)+int(st_otrok), id_rezervacije, datum_nove, datum_nove, int(st_dni_nove)))
#         prosta_parcela = self.cur.fetchall()
#         return prosta_parcela

#     def zbrisi_rezervacijo(self, id_rezervacije):
#         self.cur.execute("""DELETE FROM rezervacije WHERE id = %s""", (id_rezervacije,))
#         self.conn.commit()
#         return 
# #         
#     def ustvari_racun(self, id_rez, emso):
#         self.cur.execute("""INSERT INTO racun (id_rezervacije, izdajatelj) VALUES (%s, %s); """, (id_rez, emso))
#         self.conn.commit()
#         return
    
#     def posodobi_rezervacijo(self, id_rezervacije, pricetek_bivanja, st_nocitev, odrasli, otroci, nova_parcela):
#         self.cur.execute(
#             """
#             UPDATE rezervacije
#             SET pricetek_bivanja = %s,
#                 st_nocitev = %s,
#                 odrasli = %s,
#                 otroci = %s,
#                 rezervirana_parcela = %s
#             WHERE rezervacije.id = %s""", (pricetek_bivanja, int(st_nocitev), int(odrasli), int(otroci), int(nova_parcela), int(id_rezervacije)))
#         self.conn.commit()
#         return
