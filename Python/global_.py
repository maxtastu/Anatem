# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 15:06:23 2018

@author: m.tastu

Variables globales pour Anatem : outils divers utiles un peu partout
"""
import os
import pandas as pd

#Chemins Anatem
MAINDIR   = os.path.dirname(os.getcwd())
CONFIGDIR = MAINDIR + "\\Config\\"
PYDIR     = MAINDIR + "\\Python\\"
EXPORTDIR = MAINDIR + "\\Exports\\"
SAVEDIR   = MAINDIR + "\\Sauvegardes\\"
TEMPDIR   = MAINDIR + "\\Temporaire\\"

#DF des paramètres des stations
STATIONS = pd.read_csv(
        CONFIGDIR+"stations.csv",
        index_col='station',
        encoding = 'utf-8',
        dtype={"suffixe_st":str},
        )
#Dictionnaire des noms de stations
NOMS = STATIONS["nom"].to_dict()
#DF des paraèmtres de Phoeniks
PHOENIKS = pd.read_csv(
        CONFIGDIR+"phoeniks.csv",
        sep=";",
        encoding = 'utf-8',
        )

#ordre des scénarios de pluie
SC_ORDRE = [  
        "MoyMax",
        "MoyMoy",
        "MoyMin",
        "RR3",
        "LocMax",
        "LocMin",
        "Manuel_1",
        "Manuel_2",
        "Pluie_nulle",
        ]

def trim(string):
    u"""supprime les espaces en début et fin de lignes ds une chaîne de caracs

    argument : chaîne de caractères
    sortie : chaîne de caractères nettoyée

    """

    lines = string.split("\n")
    lines = [line.strip() for line in lines]
    string = "\n".join(lines)

    return string

def ptrim(string):
    u"""print la chaîne nettoyée (fct trim)
    
    """
    print(trim(string))   
        
class StdoutRedirector():
    u"""classe de redirection de la sortie standard vers un widget choisi
    
    Paramètres :
        - text_area : widget supportant l'ajout de texte avec une méthode
        appendPlainText
      
    """

    def __init__(self,text_area):
        self.text_area = text_area

    def write(self,str):
        self.text_area.appendPlainText(str)
