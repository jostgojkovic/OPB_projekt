from bottleext import *

from database import Repo
from Data.Modeli import *
from functools import wraps
import re
import Data.auth_public as auth_public
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import os

repo = Repo()

SERVER_PORT = os.environ.get('BOTTLE_PORT', 8081)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)


conn = psycopg2.connect(database=auth_public.db, host=auth_public.host, user=auth_public.user, password=auth_public.password, port=DB_PORT)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 


def password_hash(s):
    """Vrni SHA-512 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.sha512()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

@get('/')
def osnovna_stran():
    return template('osnovna_stran.html')

def cookie_required(f):
    """
    Dekorator, ki zahteva veljaven piškotek. Če piškotka ni, uporabnika preusmeri na stran za prijavo.
    """
    @wraps(f)
    def decorated( *args, **kwargs):
        cookie = request.get_cookie("username")
        if cookie:
            return f(*args, **kwargs)
        return template('prijava.html')
    return decorated

def cookie_required_sef(f):
    """
    Dekorator, ki zahteva veljaven piškotek sefa. Če piškotka ni, uporabnika preusmeri na stran za prijavo.
    """
    @wraps(f)
    def decorated(*args, **kwargs):

        cookie = request.get_cookie("rola")
        if cookie == "sef":
            return f(*args, **kwargs)

        return template("sef_prijava.html", napaka="Za dostop se je potrebno prijaviti kot sef")

    return decorated

@get('/komentar')
@cookie_required  
def komentar_get():
    cur.execute(""" SELECT * FROM komentar ORDER by "id" DESC """)
    posts = cur.fetchall() #dobi vse objave
    samo_objave = []
    for post in posts:
        besedilo = post["vsebina"]
        samo_objave.append(besedilo)
    uporabniska = []
    for p in posts:
        id_objavitelja = int(p[2])
        cur.execute(""" SELECT * FROM stranka WHERE "id" = %s """, [id_objavitelja] )
        lst = cur.fetchall()[0]
        user_objavitelja = str(lst[1])
        uporabniska.append(user_objavitelja)
    skupaj = tuple(zip(samo_objave,uporabniska))
    return template('komentar.html', posts=posts, objave=samo_objave, uporabniska=uporabniska, skupaj=skupaj, lst=lst)

@post('/komentar')
@cookie_required
def komentar_post():
    uporabnik = request.get_cookie("username")
    cur.execute("""SELECT * FROM stranka WHERE "username" = %s""", [uporabnik])
    lst = cur.fetchall()[0]
    id_user = lst[0]
    content = request.forms.get('content')
    my_new_string = re.sub('Ä', 'č', content)
    my_new_string = re.sub('Å½', 'Ž', my_new_string)
    my_new_string = re.sub('Å¾', 'ž', my_new_string)
    my_new_string = re.sub('Å¡', 'š', my_new_string)
    my_new_string = re.sub('Å', 'Š', my_new_string)
    if my_new_string[0] == "č":
        my_new_string = "Č"+ my_new_string[1:]
    for i in range(len(my_new_string)-2):
        if my_new_string[i] == "Š":
            my_new_string = my_new_string[:i+1]+my_new_string[i+2:]
    
    cur.execute(""" INSERT INTO komentar ("vsebina", "stranka_id") 
                    VALUES (%s, %s)""", (my_new_string, id_user))
    conn.commit()
    redirect(url('komentar_get'))
    

@get('/prijava') 
def prijava_get():
    return template("prijava.html")

@post('/prijava') 
def prijava_post():
    uporabnisko_ime = request.forms.get('uporabnisko_ime')
    geslo = password_hash(request.forms.get('geslo'))
    if uporabnisko_ime is None or geslo is None:
        redirect(url('prijava_get'))
    hashBaza = None
    try: 
        hashBaza = cur.execute('SELECT "password" FROM stranka WHERE "username" = %s', [uporabnisko_ime])
        hashBaza = cur.fetchone()[0]
        id_stranka= cur.execute('SELECT "id" FROM stranka WHERE "username" = %s', [uporabnisko_ime])
        id_stranka = cur.fetchall()[0][0]
    except:
        hashBaza = None
    if hashBaza is None:
        redirect(url('prijava_get'))
        return
    if geslo != hashBaza:
        redirect(url('prijava_get'))
        return
    response.set_cookie("username", uporabnisko_ime,  path = "/") 
    response.set_cookie("rola", "stranka",  path = "/")
    response.set_cookie("id", str(id_stranka), path="/")
    redirect(url('gost_prijavljen_get',id_stranka=id_stranka)) 


@get('/gost/prijavljen')
@cookie_required
def gost_prijavljen_get():
    return template("osnovna_stran_prijavljen")


@get('/gost/rezervacija')
@cookie_required  
def gost_rezervacija_get():
    return template("rezervacija.html")

@post('/gost/rezervacija')
@cookie_required  
def gost_rezervacija_post():
    id_stranke = int(request.cookies.get("id"))
    start_datum = request.forms.get('start_datetime')
    konec_datum = request.forms.get('end_datetime')
    st_gostov = request.forms.get('persons')

    # ni možna rezervacija v preteklost
    danes = datetime.now()

    datum = datetime.strptime(start_datum, "%Y-%m-%dT%H:%M")
    datum_konec = datetime.strptime(konec_datum, "%Y-%m-%dT%H:%M")

    if datum < danes:
         return template_user("rezervacija.html",  napaka="Ni mogoče potovati v preteklost!")
    
    # ni možna rezervirat za več kot 1 dan
    if datum_konec - datum >= timedelta(days=1):
        return template_user("rezervacija.html",  napaka="V restavraciji ne morete prespati!")

    # rez se konca na isti dan
    if datum_konec.date() != datum.date():
        return template_user("rezervacija.html",  napaka="V restavraciji ne morete prespati!")
    
    # nesme bit konec pred zacetkom
    if datum_konec <= datum:
        return template_user("rezervacija.html", napaka="Konec rezervacije ne sme biti pred začetkom rezervacije!")
    
    # dolžina rezervacije more bit usaj 1 uro:
    if datum_konec - datum <= timedelta(hours=1):
        return template_user("rezervacija.html", napaka="Rezervacija mora trajati vsaj 1 uro!")
 
    cur.execute("""
        SELECT m."id"
        FROM miza AS m
        WHERE m."kapaciteta" = %s 
        AND m."id" NOT IN (
                SELECT r."miza_id"
                FROM rezervacija AS r
                WHERE (r."cas_rezervacije" < %s AND r."konec_rezervacije" > %s)
        )
        """, (st_gostov,konec_datum, start_datum ))
    prosta_miza = cur.fetchone()
    if not prosta_miza:
        return template_user("rezervacija.html", napaka="Žal za izbrani termin ni proste mize!")
    
    rezervacija1 = Rezervacija(id_stranke=id_stranke, stevilo_gostov=st_gostov, cas_rezervacije=start_datum, konec_rezervacije=konec_datum, miza_id=prosta_miza[0])
    repo.dodaj_rezervacije(rezervacija1)


    redirect(url('gost_narocilo_get'))


@get('/sef/prijava')
def prijava_sef_get():
    return template("sef_prijava.html")

# PRIJAVA ZA sefa
@post('/sef/prijava')
def prijava_sef_post():
    uporabnisko_ime = request.forms.get('uporabnisko_ime')
    geslo = request.forms.get('geslo')
    if uporabnisko_ime is None or geslo is None:
        return template("sef_prijava.html")
    hashBaza = None
    try:
        hashBaza = cur.execute(
            """SELECT "password" FROM sef WHERE "username" = %s""", [uporabnisko_ime])
        hashBaza = cur.fetchone()[0]
        id_sef = cur.execute(
            """SELECT "id" FROM sef WHERE "username" = %s""", [uporabnisko_ime])
        id_sef = cur.fetchall()[0]
    except TypeError:
        hashBaza = None
    if hashBaza is None:
        return template("sef_prijava.html")
    if geslo != hashBaza:
        return template("sef_prijava.html")
    response.set_cookie("username", uporabnisko_ime,  path="/")
    response.set_cookie("rola", "sef",  path="/")
    response.set_cookie("id", str(id_sef),  path="/")

    redirect(url('aktivne_rezervacije_get'))


@get('/odjava')
def odjava():
    """
    Odjavi uporabnika iz aplikacije. Pobriše piškotke o uporabniku in njegovi roli.
    """

    response.delete_cookie("username")
    response.delete_cookie("rola")
    response.delete_cookie("id")

    return template('osnovna_stran.html', napaka=None)


@get('/registracija')
def registracija_get():
    return template('registracija.html')

@post('/registracija')
def registracija_post():
    uporabnisko_ime = request.forms.uporabnisko_ime
    geslo = password_hash(request.forms.geslo)
    ime = request.forms.ime
    stranka1 = Stranka(name=ime, username=uporabnisko_ime,password=geslo)
    repo.dodaj_stranka(stranka1)
    redirect(url('osnovna_stran'))



@get("/gost/narocilo/")
@cookie_required
def gost_narocilo_get():
    cur.execute("""SELECT "id", "ime_jedi", "opis_jedi", "cena" FROM meni ORDER BY "id" """)
    rows = cur.fetchall()
    return template("narocanje.html", produkti_nova=rows)

@post("/gost/narocilo/")
@cookie_required
def gost_narocilo_post():
    id_stranke = int(request.cookies.get("id"))
    izbira = request.forms.getall("izbira")
    kolicina = [int(request.forms.get(f"kolicina{jed}", 1)) for jed in izbira]
    cur.execute(""" SELECT "id" FROM rezervacija WHERE "id_stranke" = %s""", [id_stranke])
    lst = cur.fetchall()    
    id_rezervacije = lst[-1][0]
    n = 0
    cene = []
    imena_jedi = []
    for i, k in zip(izbira,kolicina):
        cur.execute(""" SELECT "cena","ime_jedi" FROM meni WHERE "id"=%s """, [int(izbira[n])])
        lst2 = cur.fetchall()
        cena = lst2[0][0]
        ime = lst2[0][1]
        vsebina = Vsebina_rezervacije(rezervacija_id=id_rezervacije, meni_id=int(izbira[n]),cena=cena)
        for j in range(0,k):
            repo.dodaj_vsebina_rezervacije(vsebina)
        cene.append(cena)
        imena_jedi.append(ime)
        n=n+1
    cur.execute(""" SELECT * FROM rezervacija WHERE "id_stranke" = %s""", [id_stranke])
    vse = cur.fetchall()[-1]
    return template("koncano_narocilo.html", izbira=vse, imena_jedi =imena_jedi, cene=cene, kolicina=kolicina)


@get('/pregled_rezervacij')
@cookie_required_sef
def aktivne_rezervacije_get():
    cur.execute("""
        SELECT rezervacija."id", stranka."username", rezervacija."stevilo_gostov", rezervacija."cas_rezervacije", rezervacija."konec_rezervacije"
        FROM rezervacija
        LEFT JOIN stranka on rezervacija."id_stranke" = stranka."id"
        WHERE rezervacija."cas_rezervacije" > CURRENT_TIMESTAMP
        ORDER BY rezervacija."cas_rezervacije" ASC""")
    rez = cur.fetchall()
    idji = [l[0] for l in rez]
    jedi_vse = []
    for i in idji:
        cur.execute("""
            SELECT meni."ime_jedi", meni."cena" FROM vsebina_rezervacije
                    LEFT JOIN meni ON vsebina_rezervacije."meni_id" = meni."id"
                    WHERE vsebina_rezervacije."rezervacija_id" = %s
                    """, [i])
        jedi = cur.fetchall()
        jedi_vse.append(jedi)
    for res, hrana in zip(rez, jedi_vse):
        res.append(hrana)
    for sublist in rez:
        for i in range(len(sublist)):
            if isinstance(sublist[i], datetime):
                sublist[i] = sublist[i].strftime("%d. %m. %Y ob %H:%M uri")

    return template('aktivne_rezervacije.html', rez = rez, idji=idji, jedi_vse=jedi_vse)




debug(True)

if __name__ == "__main__":
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER)