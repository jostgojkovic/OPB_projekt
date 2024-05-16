import pandas as pd
import re
from pandas import DataFrame

from Database import Repo
from Modeli import *
from typing import Dict
from re import sub
import dataclasses

podatki_meni = pd.read_csv(r'Data/meni.csv', sep=";")
df = pd.DataFrame(podatki_meni)

df2 = df.copy()

df2.columns = ['ime_jedi', 'opis_jedi','cena']

repo = Repo()

def uvozi_v_sql(df, ime):
    repo.df_to_sql_create(df, ime, add_serial=True, use_camel_case=False)
    repo.df_to_sql_insert(df, ime, use_camel_case=False)

#uvozi_v_sql(df2, "meni") #ne poganjaj te vrstice


