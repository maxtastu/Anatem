# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 12:22:07 2018

@author: m.tastu

fonctions d'acquisition des données pour le lancement de modèles
"""
import pyodbc
import pandas as pd
import numpy as np
import csv
import threading
import urllib
import json
from datetime import datetime as dt, timedelta as td
from ConfigParser import ConfigParser
from scipy.interpolate import interp1d

from libbdimage import bdiws
from libbdimage.bdimage import NCollection, Collection
from libbdimage.bdixml import r2016 as bdixml

import cStringIO as StringIO

from global_ import *

config = ConfigParser()
config.read(CONFIGDIR+"config.ini")

SACHA_BASE = config.get("Sacha", "SACHA_BASE")
SACHA_DRIVER = config.get("Sacha", "SACHA_DRIVER")
SACHA_PWD = config.get("Sacha", "SACHA_PWD")

BAREME_BASE = config.get("Bareme", "BAREME_BASE")
BAREME_DRIVER = config.get("Bareme", "BAREME_DRIVER")
BAREME_PWD = config.get("Bareme", "BAREME_PWD")

class AcquisitionError(Exception):
    pass

def connect_Sacha(function):
    def wrapper(*args, **kwargs):

        global conSacha, curSacha
        conSacha = pyodbc.connect(
                'DRIVER={};DBQ={};PWD={}'
                .format(SACHA_DRIVER,SACHA_BASE,SACHA_PWD))
        curSacha = conSacha.cursor()

        try:
            return function(*args, **kwargs)
        finally:
            curSacha.close()
            conSacha.close()
    return wrapper

def connect_Bareme(function):
    def wrapper(*args, **kwargs):

        global conBareme, curBareme
        conBareme = pyodbc.connect(
                'DRIVER={};DBQ={};PWD={}'
                .format(BAREME_DRIVER,BAREME_BASE,BAREME_PWD))
        curBareme = conBareme.cursor()

        try:
            return function(*args, **kwargs)
        finally:
            curBareme.close()
            conBareme.close()
    return wrapper


@connect_Sacha
def get_obs_Sacha(stations, grandeur, t_deb, t_fin, bddTR=True):
    u"""acquisition des données observées dans la base Sacha.
    
    Paramètres :
        - stations  liste de codes site hydro3
        - grandeur  "Q" pour débit ou "P" pour pluie
        - t_deb     datetime borne basse des dates à acquérir
        - t_fin     datetime borne haute des dates à acquérir
        - bddTR     bool defaut True,
                        True   pour données temps réel,
                        False  pour données historiques
                        
    Sorties :
        - obs     df à double index (station, date)
                       1 colonne - Qobs (unité : m3/s) si grandeur Q
                                 - Hobs (unité : mm  ) si grandeur P
        - lacunes liste des stations sans donnée en base sur la plage de temps
                             
    """
    #TODO interroger pour plusieurs grandeurs en même temps
    source = "donnees_treel" if bddTR else "donnees"
    nature = {"Q": "1",
              "P": "3",
              }
    conversion = {"Q":1.,  #m3/s
                  "P":.1,  #1/10ème de mm vers mm
                  }
    list_dfs = []
    lacunes  = []
    _obs = "{}obs".format(grandeur)
    
    for station in stations:
        nosta = curSacha.execute("""
                SELECT nosta
                FROM station
                WHERE codesitehydro3 = '{}'
                """
                .format(station)
                ).fetchone()[0]

        data = curSacha.execute("""
                SELECT ladate, valeur
                FROM {}
                WHERE nosta = {}
                AND nature = {}
                AND ladate >= #{}#
                AND ladate <= #{}#
                ORDER BY ladate
                """
                .format(source,
                        str(nosta),
                        nature[grandeur],
                        t_deb.strftime('%m/%d/%Y %H:%M:%S'),
                        t_fin.strftime('%m/%d/%Y %H:%M:%S')
                    )
                ).fetchall()

        if len(data) == 0:
            lacunes += [station]
        else:
            df = pd.DataFrame.from_records(data,columns=['date', _obs])
            df['station'] = station
            df = df.set_index(['station','date'])
            list_dfs += [df]
    #si lacune pour toutes les stations sélectionnées, construction DF vide
    obs = pd.concat(list_dfs) if len(lacunes) != len(stations) \
          else pd.DataFrame()
          
    #conversion de l'unité des données
    obs *= conversion[grandeur]
    
    return obs, lacunes

@connect_Sacha
def get_Qobs(stations, t_prev, t_zero):
    """extrait le débit observé aux stations de la base Sacha

    arguments
    - stations : liste de codes hydro3 (codes site)
    - t_prev : borne haute des dates recueillies
    - t_zero : borne basse

    sortie
    - dfQobs : df à double index (station, date)
               1 colonne Qobs (unité : m3/s)
    - lacunesQ : liste des stations sans Q en base sur la plage de temps

    """

    list_dfs = []
    lacunesQ = []

    for station in stations:
        try:
            nosta = curSacha.execute("""
                    SELECT nosta
                    FROM station
                    WHERE codesitehydro3 = '{}'
                    """.format(station)
                    ).fetchone()[0]
    
            Q = curSacha.execute("""
                    SELECT ladate, valeur
                    FROM donnees_treel
                    WHERE nosta = {}
                    AND nature = 1
                    AND ladate >= #{}#
                    AND ladate <= #{}#
                    ORDER BY ladate
                    """.format(str(nosta),
                               t_zero.strftime('%m/%d/%Y %H:%M:%S'),
                               t_prev.strftime('%m/%d/%Y %H:%M:%S')
                        )
                    ).fetchall()
    
            if len(Q) == 0:
                raise AcquisitionError(
            """Lacune de Q dans la base Sacha pour la station {}"""
            .format(station))
        except AcquisitionError:
            lacunesQ += [station]            
        else:
            df = pd.DataFrame.from_records(Q,columns=['date', 'Qobs'])
            df['station'] = station
            df = df.set_index(['station','date'])
    
            list_dfs += [df]
    #gestion cas lacune de Q pour toutes les stations sélectionnées
    if len(lacunesQ) != len(stations):
        dfQobs = pd.concat(list_dfs)
    else: dfQobs = None
    
    if len(lacunesQ) != 0:
        ptrim(u"""{0} station{1} ignorée{1} car lacune de Q en base :
                  {2}
                  """.format(
              len(lacunesQ),
              "" if len(lacunesQ)==1 else "s",
              "\n".join(NOMS[station] for station in lacunesQ)
             ))
    
    return dfQobs, lacunesQ

@connect_Sacha
def get_Pobs(stations, t_prev, t_zero):
    """extrait la pluie de bassin Antilope TR aux stations de la base Sacha

    arguments
    - stations : liste de codes hydro3 (codes site)
    - t_prev : borne haute des dates recueillies
    - t_zero : borne basse

    sortie
    - dfPobs : df à double index (station, date)
               1 colonne Pobs (unité : mm)

    """
    list_dfs = []

    for station in stations:
        nosta = curSacha.execute("""
                SELECT nosta
                FROM station
                WHERE codesitehydro3 = '{}'
                """.format(station)
                ).fetchone()[0]

        P = curSacha.execute("""
                SELECT ladate, valeur
                FROM donnees_treel
                WHERE nosta = {}
                AND nature = 3
                AND ladate >= #{}#
                AND ladate <= #{}#
                ORDER BY ladate
                """.format(str(nosta),
                           t_zero.strftime('%m/%d/%Y %H:%M:%S'),
                           t_prev.strftime('%m/%d/%Y %H:%M:%S')
                    )
                ).fetchall()

        df = pd.DataFrame.from_records(P,columns=['date', 'Pobs'])
        df['Pobs'] = .1 * df['Pobs'] #pluie en 1/10ème de mm dans Sacha
        df['station'] = station
        df = df.set_index(['station','date'])

        list_dfs += [df]

    dfPobs = pd.concat(list_dfs)
    #note : ralentissements possibles avec concat
    #la doc recommande d'utiliser une liste en intention

    return dfPobs

@connect_Sacha
def get_niveaux_vigilance(stations):
    u"""récupère les niveaux de vigilance en H et en Q dans la base Sacha

    arguments
    - stations : liste de codes hydro3 (codes site)
    
    sortie :
    - nivVigi DataFrame
        - 2 niveaux d'index : station, niveau
        Niveau : JB, JH, OB, OH, RB, RH (s'ils existent à la station)
        - 2 colonnes : H, Q
        unités : H en cm, Q en m3/s
    """
    nivVigiStations = []
    for station in stations:
        nosta = curSacha.execute("""
                SELECT nosta
                FROM station
                WHERE codesitehydro3 = '{}'
                """.format(station)
                ).fetchone()[0]
        Hvig = curSacha.execute("""
                SELECT h_jaunemin , h_jaune, 
                       h_orangemin, h_orange, 
                       h_rougemin , h_rouge 
                FROM station 
                WHERE nosta = {}
                """.format(nosta)
                ).fetchone()
        Qvig = curSacha.execute("""
                SELECT q_jaunemin , q_jaune, 
                       q_orangemin, q_orange, 
                       q_rougemin , q_rouge 
                FROM station 
                WHERE nosta = {}
                """.format(nosta)
                ).fetchone()

        nivVigiStations += [pd.DataFrame.from_records(
                data=np.transpose([Hvig, Qvig]),
                index=["JB","JH","OB","OH","RB","RH"],
                columns=["H","Q"],
                ).dropna()]
        
    nivVigi = pd.concat(
            nivVigiStations,
            keys=stations,
            names=["station","niveau"]
            )

    nivVigi.sort_values(by=["station","H"], inplace=True)

        
    return nivVigi


@connect_Bareme
def get_CT(stations):
    """extrait les courbe de tarages active dans base Bareme

    arguments
    - stations : liste de codes hydro3 (codes site)

    sortie
    - CT dictionnaire de fonctions courbe de tarage
    CT[station] (Q en m3/s) = H en mm
    CT[station] (Q hors CT) = NaN

    """

    CT = {}

    for station in stations:
        nosta = curBareme.execute("""
                       SELECT nosta
                       FROM station
                       WHERE codesitehydro3 = '{}'
                       """.format(station)
                       ).fetchone()[0]

        # On prend la courbe valide dans le futur
        date = curBareme.execute("""
                      SELECT MAX(cdatefin)
                      FROM entetecourbe
                      WHERE nosta = {}
                      """.format(nosta)
                      ).fetchone()[0]

        noCT = curBareme.execute("""
                      SELECT noct
                      FROM entetecourbe
                      WHERE nosta = {}
                      AND cdatefin = #{}#
                      """.format(nosta,date)
                      ).fetchone()[0]

        fetch = curBareme.execute("""
                    SELECT nopt,h,q
                    FROM pointcourbe
                    WHERE noct = {}
                    ORDER BY Q
                    """.format(noCT)
                    ).fetchall()
        dfCT = pd.DataFrame.from_records(
                fetch,
                columns=['point','H(mm)','Q(m3/s)'],
                index='point')
        #Note: les fonctions interp1d ne gèrent pas les NaN en entrée
        CT[station] = interp1d(dfCT['Q(m3/s)'].values,
                                     dfCT['H(mm)'].values*0.1, #conv mm vers cm
                                     bounds_error=False,
                                     fill_value="extrapolate",
                                     )

    return CT

def get_sympo_rr(stations, t_prev):
    u"""récupère les prévisions sympo rr3 de la BD Image, converties au mm
    
    paramètres
    - stations : liste de codes hydro3 (codes site)
    - t_prev date de début des prévisions recueillies, modulo 3h
    (si t_prev 17hxx min, 1ère prévision à 15h00)

    sortie:
    - Pprev DataFrame avec date en index
     et en colonnes 
         - station
         - RR3 pluie prévue au pas de temps 3h (inchangé)
    
    """

    #correspondance code station / code zone pluie
    hydro2BNBV = STATIONS.loc[stations, "BNBV"].to_dict()
    BNBV2hydro = {}
    for (k,v) in hydro2BNBV.items():
        v = v.replace("x","") #suppr les xx en fin de ligne
        hydro2BNBV[k] = v
        BNBV2hydro[v] = k
    
    #paramètres de la requête
    ZONES = hydro2BNBV.values()
    PROXIE = {'http':None}
    FAMILY, KIND = 'sympo', 'rr'
    START = dt(t_prev.year, t_prev.month, t_prev.day, t_prev.hour) \
            + td(hours = 3 - t_prev.hour%3)
    #horizon des prévisions calées sur horizon du BP
    STOP = t_prev + td(days=3) - td(hours=t_prev.hour)
    #choix du network en fonction de l'ancienneté pour cibler le plus proche
    #en base (voir doc bdimage)
    NETWORK = dt(t_prev.year, t_prev.month, t_prev.day, t_prev.hour)
    delta_t = dt.utcnow() - t_prev
    if delta_t < td(days=15):
        NETWORK += td(minutes = t_prev.minute - t_prev.minute%15)
    elif delta_t < td(days=90):
        pass
    else:
        NETWORK -= td(hours = t_prev.hour % 6)
        
    client = bdiws.Client(proxies=PROXIE)
    ncollec = NCollection(
            family=FAMILY,
            kind=KIND, 
            start=START, 
            network=NETWORK,
            stop = STOP,
            )
    prev_stat = client.getprevbynetworkstatsbyzones(
        ncollec, zones=ZONES, mode='async', wait=1)

    tup = []
    dteNetwork = dt.strptime(
            bdixml.Message.from_file(StringIO.StringIO(prev_stat))
            .report.request["dateNetwork"], "%Y%m%d%H%M")
    for image in bdixml.Message.from_file(
            StringIO.StringIO(prev_stat)).previsions[0].images:
        date = dt.strptime(image.dateasstr, "%Y%m%d%H%M")
        for band in image.bands:
            for stats in band.stats:
                tup += [(date, BNBV2hydro[stats.zone], stats.stat["moy"])]
    Pprev = pd.DataFrame.from_records(
            tup,columns=["date","station","RR3"],
            index="date"
           )
  
    Pprev['RR3'] /= 10. #  conversion du 1/10ème de mm au mm
    if Pprev.empty:
        raise AcquisitionError(
                u"""Echec recuperation previsions sympo RR3.""")

    return Pprev, dteNetwork


def params_BP():
    u"""lecture fichier avec pondération des zones BP par bassin
    
    sorties :
    - zonesBP : liste des zones BP
    - coeffBP : dictionnaire des zones BP et coeffs associés par station
    coeffBP[station] = [(coeff0, zone0), ..., (coeff_n, zone_n)]
    
    """
    coeffBP = {}
    with open (CONFIGDIR+"zones_BP_ponderation.csv", "r") as f:
        reader= csv.reader(f, delimiter=";")
        zonesBP = reader.next()[1:]
        for row in reader:
            coeffBP[row[0]] = []
            for i in range(len(zonesBP)):
                if row[i+1] != "":
                    coeffBP[row[0]] += [(float(row[i+1]), unicode(zonesBP[i]))]
    zonesBP = [unicode(zone) for zone in zonesBP]                
    return zonesBP, coeffBP

def get_BP(zonesBP, rejeu=False, t_rejeu=None):
    u"""acquisition des prévisions de pluie BP sur la BD APBP, convertie en mm
    
    arguments :
        - zonesBP : liste des zones BP à appeler
        - rejeu : True si mode rejeu
        - t_rejeu : date du rejeu le cas échéant (datetime)
        
    sortie :
        - BP DataFrame avec indice (zone_BP, date)
        4 colonnes scenario : moy, incmoy, loc, incloc
        
    """

    if rejeu:        
        url = "http://services.schapi.e2.rie.gouv.fr/bdlamedo/wsbdl?" \
                 +"service=bdlamedoGet&version=201107" \
                 +"&request=getReplayBpValues&format=long&zones=" \
                 +"+".join(zonesBP) \
                 +"&date=" + dt.strftime(t_rejeu, "%Y%m%d%H%M")
            
    else:
        url = "http://services.schapi.e2.rie.gouv.fr/bdlamedo/wsbdl?" \
                 +"service=bdlamedoGet&version=201107" \
                 +"&request=getCurrentBpValues&format=long&zones=" \
                 + "+".join(zonesBP)
    try:
        request = urllib.urlopen(url)
        result = json.loads(request.read())
    except:
        #6 décembre 2018 ValueError: No JSON object could be decoded
        #contexte dysfonctionnements informatiques à l'échelle nationale
        raise AcquisitionError(trim(
                u"""Acquisition des prévisions BP impossible :
                    échec de la connexion avec la BD APBP."""))        
    
    if result["statut"] != 0:
        raise AcquisitionError(trim(
                u"""Acquisition des prévisions BP impossible :
                    échec de la connexion avec la BD APBP."""))
    
    bp = []    
    dtesBP = {}
    for data in result["data"]:
        bp += [[unicode(data[0]), #zone
                dt.strptime(data[2],"%Y%m%d%H%M"), #date
                data[3], #moy
                data[4], #incmoy
                data[5], #loc
                data[6], #incloc
                 ]]

    #récupération date de production des 3 BP
        if data[0] == 30402 : #zone Noireau : DIRO
            dtesBP["DIRO "] = dt.strptime(data[7],"%Y%m%d%H%M")
        elif data[0] == 70403 : #zone Perche : DIRIC
            dtesBP["DIRIC"] = dt.strptime(data[7],"%Y%m%d%H%M")
        elif data[0] == 10406 : #zone Andelle : DIRN
            dtesBP["DIRN "] = dt.strptime(data[7],"%Y%m%d%H%M")

    BP = pd.DataFrame(columns=["zone_BP","date","moy","incmoy","loc","incloc"],
                      data=bp
                      )
    if BP.empty:
        raise AcquisitionError(trim(
                u"""Acquisition des previsions BP impossible :
                    resultat de la requete (BD APBP) nul."""))

    BP.set_index(["zone_BP","date"], inplace=True)
    BP.rename_axis("scenario", axis=1, inplace=True)
    BP.sort_index(inplace=True)
    BP *= 0.10 #conversion du 1/10ème de mm au mm
    
    return BP, dtesBP


class Acquisition():
    u"""gère l'acquisition de toutes les données : 
        Qobs, Pobs, Pprev, niveaux de vigilance
        
    màj liste des stations si lacunes de Q
    
    gestion erreur acquisition RR3 ou BP
    
    """
    
    def __init__(self, 
                 rejeu=False,
                 date_rejeu=None):
        u"""initialisation des variables de base
        
        """
        self.rejeu = rejeu
        self.date_rejeu = date_rejeu

        if self.rejeu:
            self.t_prev = self.date_rejeu
        else:
            self.t_prev = dt.utcnow()
            self.t_prev = dt(self.t_prev.year,
                             self.t_prev.month,
                             self.t_prev.day,
                             self.t_prev.hour)
        self.zonesBP, self.coeffBP = params_BP()
        self.scManus = False        

    def get_donnees_entree(self, 
                           stations, 
                           profondeur=td(hours=48),
                           bddTR=True):
        u"""lance l'acquisition de toutes les données brutes
        
        Paramètres : 
            - stations list
            - profondeur td  profondeur des données obs
            - bddTR     bool defaut True,
                            True   pour interrogation Sacha temps réel,
                            False  pour interrogation Sacha historique
        """
        self.t_zero = self.t_prev - profondeur
        self.bddTR = bddTR
        self.get_Obs(stations)
        #TODO 
        #retour au threading pour get_Obs quand j'aurai le temps de chercher
        #comment attraper les exceptions sur le thread parent
        #(cas bien documenté mais pas prioritaire. 22/01/2019)
#        threadObs = threading.Thread(target=self.get_Obs,args=(stations,))
        threadRR3 = threading.Thread(target=self.get_et_traitement_RR3)
        threadBP = threading.Thread(target=self.get_BP)
#        threadObs.start()
        threadRR3.start()
        threadBP.start()

#        threadObs.join()
        threadRR3.join()
        threadBP.join()
        
        print self.rapportAcquisRR3
        print self.rapportAcquisBP
        #ces deux rapports plutôt que ptrim car impossible de communiquer
        #avec l'UI depuis un thread secondaire.
        #TODO associer un signal à ptrim pour communiquer avec l'UI,
        #plutôt que de passer par des rapports qui alourdissent
        
    def get_Obs(self, stations):
        u"""acquisition des données d'entrée Qobs, Pobs + niveaux de vigilance
        
        Paramètres :
            - stations liste des codes H3 des stations
        """

        self.stations = stations
        #Qobs
        self.Qobs, self.lacunesQ = get_obs_Sacha(
                self.stations,
                grandeur="Q",
                t_deb=self.t_zero,
                t_fin=self.t_prev,
                bddTR=self.bddTR)
        if self.Qobs.empty:
            raise AcquisitionError(trim(u"""### Acquisition impossible ###
                                             Motif : Aucun debit"""))    
        elif len(self.lacunesQ) > 0:
            self.stations = [station for station in self.stations 
                                     if station not in self.lacunesQ]
            ptrim(u"""{0} station{1} ignorée{1} car lacune de Q en base :
                      {2}
                      """.format(
                              len(self.lacunesQ),
                              "" if len(self.lacunesQ)==1 else "s",
                              "\n".join(NOMS[station] 
                                        for station in self.lacunesQ)
                              )
                    )     
        self.Qobs.sort_index(inplace=True)
        #Pobs
        self.Pobs, self.lacunesP = get_obs_Sacha(
                self.stations,
                grandeur="P",
                t_deb=self.t_zero,
                t_fin=self.t_prev,
                bddTR=self.bddTR)
        self.Pobs.sort_index(inplace=True)
        #nivVigi
        self.nivVigi = get_niveaux_vigilance(self.stations)


    def get_BP(self):
        u"""acquisition du BP brut.               
            si échec acquisition BP, constrution d'un df BP vide.
            
        """
        
        self.rapportAcquisBP = u""

        try:
            #exercice rejeu 11 : lecture des prévisions BP dans le csv
            #TODO mettre ceci au propre
            if self.t_prev == dt(year=2017, month=12, day=11, hour=7):
                self.BPbrut = pd.read_csv(
                        "BP_exercices_rejeu/Ex11_2017_12_11_0700.csv",
                        sep=";",
                        dtype={"zone_BP":str})
                self.BPbrut["date"] = pd.to_datetime(
                        self.BPbrut["date"],format="%Y_%m_%d")
                self.BPbrut.set_index(["zone_BP","date"], inplace=True)
                self.dtesBP = {
                        "DIRO ":dt.strptime("201712110517", "%Y%m%d%H%M"),
                        "DIRN ":dt.strptime("201712110611", "%Y%m%d%H%M"),
                        "DIRIC":dt.strptime("201712110631", "%Y%m%d%H%M")}
                self.rapportAcquisBP = "\n".join([
        self.rapportAcquisBP,
        trim(
            u"""Rejeu du {}
            Acquisition des prévisions BP par lecture du fichier : {}
            """.format(
            self.t_prev,
            "BP_exercices_rejeu/Ex11_2017_12_11_0700.csv")
            )]
        )
            #exercice rejeu 12 : lecture des prévisions BP dans le csv
            elif self.t_prev == dt(year=2017, month=12, day=29, hour=7):
                self.BPbrut = pd.read_csv(
                        "BP_exercices_rejeu/Ex12_2017_12_29_0700.csv",
                        sep=";",
                        dtype={"zone_BP":str})
                self.BPbrut["date"] = pd.to_datetime(
                        self.BPbrut["date"],format="%Y_%m_%d")
                self.BPbrut.set_index(["zone_BP","date"], inplace=True)
                self.dtesBP = {
                        "DIRO ":dt.strptime("201712290548", "%Y%m%d%H%M"),
                        "DIRN ":dt.strptime("201712290600", "%Y%m%d%H%M"),
                        "DIRIC":dt.strptime("201712290623", "%Y%m%d%H%M")}
                self.rapportAcquisBP = "\n".join([
        self.rapportAcquisBP,
        trim(
            u"""Rejeu du {}
            Acquisition des prévisions BP par lecture du fichier : {}
            """.format(
            self.t_prev,
            "BP_exercices_rejeu/Ex12_2017_12_29_0700.csv")
            )]
        )
            else:    
                self.BPbrut, self.dtesBP = get_BP(self.zonesBP, 
                                              self.rejeu, 
                                              self.t_prev)
        except AcquisitionError:            
            self.echecBP = True
            self.BPbrut = self.BP_secours()
            ptrim(u"""échec de l'acquisition des données BP (BD APBP).""")
            
            return

        self.echecBP = False
        self.rapportAcquisBP = "\n".join([
            self.rapportAcquisBP,
            trim(u"""Dates de production des BP : 
                      {}""".format("\n".join("{}: {} (TU)".format(
                        dirMF, dt.strftime(date, "%d/%m/%Y %H:%M")) 
                    for (dirMF,date) in self.dtesBP.items()))
                )]
            )
                    

    def get_et_traitement_RR3(self):
        u"""opérations du thread associé à l'acquisition des RR3 bruts
        
        1. Acquisition des prévisions RR3
        
        2. Traitement des prévisions : passage au pas de temps horaire
        cumul rr3/ 3 pour chaque heure 
        (pas de prise en compte de la pluie obs pour les 1ers pas de temps)
        
        """
        
        ### Acquisition ###

        try:
            self.Pprev, self.dteNetWorkRR3 = get_sympo_rr(
                    self.stations, 
                    self.t_prev
                    )
        #si échec de l'acquisition RR3: construction df de même forme,
        #avec RR3 nul. profondeur 72h.
        except:
            self.echecRR3 = True
            self.Pprev = self.pprev_secours()
            self.rapportAcquisRR3 = \
            u"""échec de l'acquisition des données sympo RR3 (BD Image)."""
        else: 
            self.echecRR3 = False
            self.rapportAcquisRR3 = trim(
            u"""Fuseau de prévisions RR3 :
                {} (TU)"""          \
            .format(dt.strftime(self.dteNetWorkRR3, "%d/%m/%Y %H:%M"))
            )


        #### Traitement ####
        #passage au pas de temps horaire
        self.Pprev = self.Pprev.pivot(columns="station", values="RR3")
        self.Pprev.sort_index(inplace=True)
        self.Pprev = self.Pprev.asfreq(freq="1H", method="backfill")
        self.Pprev /= 3

        #ajout premiers pas de temps
        delta = self.t_prev.hour % 3
        #cas delta 3h (exemple : il est entre 0h00 et 0h59)
        if delta == 0:
            top = self.Pprev[:1].copy()
            top = pd.concat([top, top])
            top.reset_index(inplace=True)
            top.loc[0,"date"] -= td(hours=2)
            top.loc[1,"date"] -= td(hours=1)
            top.set_index("date",inplace=True)
            self.Pprev = pd.concat([top, self.Pprev])
        #cas delta 2h (exemple : il est entre 1h00 et 1h59)
        elif delta == 1:
            top = self.Pprev[:1].copy()
            top.reset_index(inplace=True)
            top.loc[:,"date"] -= td(hours=1)
            top.set_index("date",inplace=True)
            self.Pprev = pd.concat([top, self.Pprev])

        self.Pprev = self.Pprev.unstack()
        self.Pprev = self.Pprev.reset_index(level="station")
        self.Pprev.rename({0:"RR3"}, axis=1,inplace=True)

    def BP_suivant_rr3(self, row):
        u"""calcule les valeurs horaires de BP suivant répartition RR3
        
        gestion RR3 nul : cumul BP réparti uniformément sur les 24h
        
        arguments :
            - row ligne de Pprev
            - BP df avec index (station, date), colonnes scénarios
            - sumRR3 df avec index date, colonne station
            
        sortie :
            - bp liste des valeurs de bp pour la ligne row, dans l'ordre
            de BP.columns
            
        """

        #note : cas utile pour tests
        #BP DIRN 15/11/2018 après-midi
        #pas de chiffre pour zone BP Epte (10407)
        jourBP = (row.name+td(hours=23)).date()
        station = row.loc["station"]
        #valeurs manquantes remplacées par pluie nulle
        if jourBP not in self.BP.loc[station].index \
                            .get_level_values(level="date"):
            return [None]*len(self.BP.columns)

        #cas rr3 positif : répartition suivant l'enveloppe du rr3        
        if self.sumRR3.loc[jourBP, station] != 0:
            bp= [row.loc["RR3"] \
                    * (self.BP.loc[(station,jourBP), scenario]
                       / self.sumRR3.loc[jourBP, station]
                      ) for scenario in self.BP.columns
                ]
        
        else:
            #cas rr3 nul : réparition uniforme sur 24h
            delta = self.delta_h \
                    if (row.name-td(hours=1)).date() == self.firstDate  \
                    and self.firstHour > 0                              \
                    else 24.
                    
            bp = [1/delta * self.BP.loc[(station, jourBP), scenario]
                  for scenario in self.BP.columns
                  ]
        return bp


    def traitement_donnees_entree(self, Pmanu=None):
        u"""post-traite les données d'entrée
        
        Pluie prévue :
            - mise en forme BP
                - calcul des cumuls par station
                - passage aux colonnes MoyMax, MoyMin 
                  et LocMax, LocMin s'il existe des Loc
                - retranchement de la pluie obs du jour j au cumul BP
            - intégration pluie manuelle
            - répartition BP sur enveloppe RR3
                Répartit les cumuls prévus par le BP
                suivant la répartition temporelle des prévisions RR3
            - mise en forme de Pprev et messages si échecs acquis BP ou RR3
            - initialisation variable self.scenarios
            
        Arguments : 
            - Pmanu, default None. DF des scénarios de pluie manuels,
                    même forme que BP en sortie de get_BP()
                    ie (zone_BP, date) en index, scenarios en colonnes
                    si None, pas de pluie manuelle.
        
        #TODO prolongation du Qobs
        
        """

        ##### traitement BP #####
        self.BP = self.BPbrut.copy()
        ### injection scénario de pluie manuels ###
        if Pmanu is not None:
            self.scManus = True
            self.BP = pd.concat([self.BP, Pmanu], axis=1)
            ptrim(u"""Ajout de {0} scénario{1} de pluie manuel{1}."""
                  .format(len(Pmanu.columns),
                          "" if len(Pmanu.columns)==1 else "s"
                          )
                  )
        else:
            self.scManus = False
            ptrim(u"""Pas de scénarios de pluie manuels.""")

        self.BP.replace([np.nan, None], 0, inplace=True)

            
        ### cumuls par bassin aux stations ###    
   
        lBP = []
        for station in self.stations:            
            lBP += [sum(elem[0]*self.BP.loc[elem[1]] 
                        for elem in self.coeffBP[station])
                    ]
        self.BP = pd.concat(lBP, keys=self.stations, names=["station", "date"])

        ### construction des colonnes max et min ###
        if self.echecBP == False:
            self.BP["MoyMax"] = self.BP["moy"] + self.BP["incmoy"]
            self.BP["MoyMin"] = self.BP["moy"] - self.BP["incmoy"]
            #si colonne loc vide, on suppr les scenarios LocMin / LocMax
            if self.BP["loc"].sum() == 0:
                pass
            #si pas d'incertitude sur les loc, une seule colonne LocMax
            elif self.BP["incloc"].sum() == 0:
                self.BP["LocMax"] = self.BP["loc"]
                #colonnes loc: remplissage valeurs vides avec valeurs moy
                self.BP["LocMax"] = self.BP.loc[:,["LocMax","MoyMax"]] \
                                    .max(axis=1)
            else:
                self.BP["LocMax"] = self.BP["loc"] + self.BP["incloc"]
                self.BP["LocMin"] = self.BP["loc"] - self.BP["incloc"]
                #colonnes loc: remplissage valeurs vides avec valeurs moy
                self.BP["LocMax"] = self.BP.loc[:,["LocMax","MoyMax"]] \
                                    .max(axis=1)
                self.BP["LocMin"] = self.BP.loc[:,["LocMin","MoyMax"]] \
                                    .max(axis=1)       
            for colonne in ["loc", "incloc", "incmoy"]:
                del self.BP[colonne]
            self.BP.rename({"moy":"MoyMoy"}, axis=1,inplace=True)
        
        #ordre des colonnes
        colOrder = ["MoyMax",
                    "MoyMoy",
                    "MoyMin",
                    "LocMax",
                    "LocMin",
                    "Manuel_1",
                    "Manuel_2"
                    ]
        self.BP = self.BP.reindex(
                columns=[col for col in colOrder if col in self.BP.columns])
        

        ### retranchement de la pluie obs du jour j au cumul BP ###
        if self.t_prev.hour > 0:
            J = dt(self.t_prev.year,self.t_prev.month,self.t_prev.day)
            sumPobs = self.Pobs.reset_index()
            sumPobs = sumPobs[sumPobs["date"] >= J + td(hours=1)]
            sumPobs.set_index("station",inplace=True)
            sumPobs = sumPobs.sum(level=0)
            sumPobs["date"] = J + td(hours=24)
            sumPobs.reset_index(inplace=True)
            sumPobs.set_index(["station","date"],inplace=True)                        
            for column in self.BP.columns:
                self.BP.loc[(slice(None),J + td(hours=24)),column]  \
                -= sumPobs["Pobs"]
            self.BP[self.BP <0] = 0


        ### répartition cumul BP sur enveloppe des RR3 ###
        
        if not self.echecBP or self.scManus: #(manip inutile si self.BP vide)
            ## construction sumRR3 df des cumuls RR3 sur 24h ##
            #date = date correspondante dans le df BP
            sumRR3 = self.Pprev.pivot(columns="station", values="RR3")
            sumRR3 = sumRR3.groupby(
                    by=lambda date:(date+td(hours=23)).date()
                    ).sum()
            sumRR3.index = pd.to_datetime(sumRR3.index)
            ## construction sumRR3 df des cumuls RR3 sur 24h ##
            #date = date correspondante dans le df BP
            sumRR3 = self.Pprev.pivot(columns="station", values="RR3")
            self.sumRR3 = sumRR3.groupby(
                    by=lambda date:(date+td(hours=23)).date()
                    ).sum()
        
            ## construction des pluies BP suivant répartition RR3 ##
            
            #utiles pour répartition si RR3 nul
            firstPrev = self.Pprev.index[0]
            self.firstHour = firstPrev.hour
            self.firstDate = firstPrev.date()
            self.delta_h = 24. - self.firstHour + 1
            
            self.Pprev = pd.concat(
            [self.Pprev, 
             self.Pprev.apply(self.BP_suivant_rr3,axis=1,result_type="expand")
                ],axis=1)
            #nommage des colonnes de scénarios BP
            self.Pprev.rename(
                    {i:sc for (i,sc) in enumerate(self.BP.columns)},
                    axis="columns", 
                    inplace=True)
        
        #passage à l'index (station, date) et tri
        self.Pprev.reset_index(inplace=True)
        self.Pprev.set_index(["station", "date"], inplace=True)
        self.Pprev.sort_index(inplace=True)
        
        if self.echecRR3:
            self.Pprev.drop("RR3", axis=1, inplace=True)
            
        #ordre des colonnes
        cols = [sc for sc in SC_ORDRE if sc in self.Pprev.columns]
        self.Pprev = self.Pprev[cols]

    
        ### messages suivant les cas + variable scenarios ###
        if self.echecRR3 and (not self.echecBP or self.scManus):
            ptrim(u"""Cumuls BP répartis uniformément sur 24h.\n""")
        if self.echecRR3 and self.echecBP and not self.scManus:
            self.Pprev.rename(columns={"RR3":"Pluie_nulle"}, inplace=True)
            self.scenarios = ["Pluie_nulle"]
            ptrim(u"""Les modèles seront exécutés en pluie nulle.\n""")
        else:
            self.scenarios = list(self.Pprev.columns)

        ptrim(u"# Traitement des données d'entrée terminé #")

        
    def pprev_secours(self):
        u"""construction d'un DF Pprev vide, pour poursuivre si échec
            d'acquisition de la donnée rr3"""
        START = dt(self.t_prev.year, self.t_prev.month, 
                   self.t_prev.day, self.t_prev.hour) \
                + td(hours = 3 - self.t_prev.hour%3)
        STOP = self.t_prev + td(days=3) - td(hours=self.t_prev.hour)
        delta = STOP-START
        delta = delta.days*24 + delta.seconds/3600 #nb d'heures
        idx = pd.MultiIndex.from_product(
                [[START + td(hours=i) for i in range(0,delta+1,3)],
                 self.stations],
                names=["date","station"]
                )
        PprevSecours = pd.DataFrame(index=idx, data={"RR3":0})
        PprevSecours.reset_index(inplace=True)
        PprevSecours.set_index("date", inplace=True)
        
        return PprevSecours
    
    def BP_secours(self):
        u"""construction d'un DF BP vide, pour poursuivre si échec
        d'acquisition des BP.
        (Utile pour la gestion des scénarios manuels)
        
        """

        idx = pd.MultiIndex.from_product(
                [self.zonesBP,
                [self.t_prev.date()+td(days=i) for i in range(3)]],
                names=["zone_BP","date"],
                )

        BPsecours = pd.DataFrame(index=idx)
        return BPsecours        
    
          
if __name__ == "__main__":
    #exemple d'acquisition temps réel ou temps différé
    stations = STATIONS.index[:2]
    t_prev = dt.utcnow()
    t_prev = dt(t_prev.year, t_prev.month, t_prev.day, t_prev.hour)
    t_rejeu = dt(year=2018, month=6, day=1, hour=00, minute=00)
    profondeur = td(hours=24)    
#    run = Acquisition(rejeu=True, date_rejeu=t_rejeu)
    run = Acquisition(rejeu=False)
    run.get_donnees_entree(stations, profondeur=profondeur, bddTR=True)
    Pmanu=pd.DataFrame(index=run.BPbrut.index, data={"Manuel_1":10})
    run.traitement_donnees_entree(Pmanu=Pmanu)
    print run.Pprev.head()
    
