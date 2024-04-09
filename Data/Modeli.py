from dataclasses import dataclass, field
from datetime import datetime

@dataclass 
class Komentar:
    id: int = field(default=0)
    vsebina: str = field(default="")

@dataclass
class Meni:
    id: int = field(default=0)
    ime_jedi: str = field(default="")
    opis_jedi: str = field(default="")
    cena: int = field(default=0)

@dataclass
class Narocilo:
    id: int = field(default=0)
    status: str = field(default="")
    cena: int = field(default=0)
    stranka_id: int = field(default=0)

@dataclass
class Rezervacija:
    id: int = field(default=0)
    stevilo_gostov: int = field(default=0)
    id_stranke: int = field(default=0)
    cas_rezervacije: datetime = field(default=datetime.now())
    miza_id: int = field(default=0)


@dataclass
class Stranka:
    id: int = field(default=0)
    name: str = field(default="")
    username: str = field(default="")
    password: str = field(default="")


@dataclass
class Vsebina_narocil:
    id: int = field(default=0)
    narocilo_id: int = field(default=0)
    meni_id: int = field(default=0)
    cena: int = field(default=0)


@dataclass
class Sef:
    id: int = field(default=0)
    name: str = field(default="")
    username: str = field(default="")
    password: str = field(default="")

@dataclass
class Miza:
    id: int = field(default=0)
    kapaciteta: int = field(default=0)