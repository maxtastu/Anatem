# -*- coding: utf-8 -*-
"""
Created on Tue Aug 14 10:37:56 2018

@author: m.tastu

classes de run pour piloter GRP, Phoeniks et Analog.

- ModelInit() définit les fonctions communes aux deux classes filles

    - RunModeles(ModelesInit, acquisition.Acquisition)
      pilotage de run, mode temps réel ou rejeu
      
    - ChargementModeles(ModelesInit)
      pilotage du chargement d'une sauvegarde
"""
import os
import shutil
import subprocess
import csv
import pandas as pd
import numpy as np
from ConfigParser import ConfigParser
from datetime import datetime as dt, timedelta as td

from libhydro.core import simulation      as LbHsimulation,      \
                          sitehydro       as LbHsitehydro,       \
                          intervenant     as LbHintervenant,     \
                          modeleprevision as LbHmodeleprevision
from libhydro.conv import xml as LbHxml


import acquisition
from global_ import *

class AnalogError(Exception):
    u"""classe d'exception utilisée pour les exceptions propres à Analog :
        pas de donnée en base Sacha pour l'événement
    
    """
    pass


class ModelesInit():
    u"""classe de pilotage de tous les modèles
    
    fonctionnalités définies à ce niveau :
        - lecutre des courbes de tarage / conversion QH
        - lecture des sorties de GRP
        - pilotage de Phoeniks
        - pilotage des Analog
        - export des sorties de modèle (GRP)

    """
    def __init__(self,
                 TR,
                 rejeu,
                 chargement):
        u"""initialisation des variables de base

        """
        self.TR, self.rejeu, self.chargement = TR, rejeu, chargement
        
        self.bddANA = {}

        assert(type(self.TR) == type(self.rejeu) == type(self.chargement)
               and (self.TR+self.rejeu+self.chargement)==1), \
        "TR, rejeu, chargement doivent etre des booleens avec 1 seul True"

        ###GRP###
        
        #chemins
        config = ConfigParser()
        config.read(CONFIGDIR+"config.ini")

        self.GRP_params  = config.get("GRP", "Parametres")
        self.GRP_entrees = config.get("GRP", "Entrees")
        self.GRP_sorties = config.get("GRP", "Sorties")
        self.GRP_exe     = config.get("GRP", "Executable")
        self.repoPdf = self.GRP_sorties + "\\Fiches_Controle\\"

        #dico codes H3/ codes pluie
        self.codeBV = STATIONS["BNBV"].to_dict()
        
        #lecture paramétrage des numéros correspondant aux scénarios de pluie
        with open (CONFIGDIR+"GRP_scenarios_pluie.csv","r") as f:
            reader = csv.reader(f,delimiter=";")
            self.numScenarios = {row[0]:row[1] for row in reader}


        self.prefixe = "_D" if self.rejeu else ""            
        self.dossierSortie = TEMPDIR if self.chargement else self.GRP_sorties
            
        self.GRPfini = False #utile pour threading UI

    def get_CT(self):
        u"""récupération des courbes de tarage en base
        
        (nécessite qu'il existe déjà un attribut self.stations
        
        """
        
        try:
            self.CT = acquisition.get_CT(self.stations)
        except:
            self.echecCT = True
            ptrim(u"""Acquisition des courbes de tarage impossible.
                  Pas de conversion débit vers hauteur.
                  """)
        else:
            self.echecCT = False

    def conversion_Q_H(self, dfIn, colsIn, colsOut):
        u"""conversion Q vers H des valeurs d'un tableau
        
        Paramètres:
            - dfIn DataFrame d'entrée
            les Q sont en colonne, les stations en 1er niveau d'index
            - colsIn  liste des noms des colonnes à convertir
            - colsOut liste des noms des nouvelles colonnes, dans l'ordre
            
        Sortie :
            - dfOut df avec les même index que dfIn,
            colonnes converties en H avec noms de colonnes colsOut
            nouvelles colonnes concaténées à droite des anciennes
        
        """
        
        if self.echecCT:
            return dfIn
        
        dfOut = dfIn[colsIn].apply(
                lambda row: self.CT[row.name[0]](row),
                result_type="expand",
                axis=1
                )
        dfOut.rename(dict(enumerate(colsOut)), axis=1,inplace=True)        
        dfOut = pd.concat([dfIn, dfOut], axis=1)        
        return dfOut            

    def lecture_sortie_GRP(self):
        u"""lit les fichiers de sortie de GRP: obs, prev, et incertitude

        fichiers dans le répertoire Sorties de GRP:
            - GRP_Obs.txt
            - GRP_Prev_000x.txt pour chaque scenario de pluie
            - \INC\GRP_Prev_000x.txt pour chaque scenario de pluie

        construit deux DF :
            - self.GRPobs issu de GRP_Obs.txt
                index : station, date
                colonnes : Qobs, Pobs

            - self.GRPprev issu des GRP_Prev_00xx.txt et \INC\GRP_Prev_00xx.txt
                index : station, scenario, date
                colonnes : Qprev, Pprev, q10, q90
                nommage des scénarios de pluie d'après GRP_scenarios_pluie.csv

        unité : tous les Q sont convertis des l/s en m3/s
        
        ajout du préfixe _D en mode rejeu (exemple : GRP_D_Obs.txt)
        
        """

        #GRP_Obs.txt to df
        self.GRPobs = pd.read_csv(
                self.dossierSortie+"\\GRP{}_Obs.txt".format(self.prefixe),
                sep=';',
                usecols=[1,2,3,4],
                names=['station','date','Qobs','Pobs'],
                skiprows=1,
                skipfooter=1,
                engine='python',
                dtype={'station':'str',
                       'date':'str',
                       'Qobs':'float',
                       'Pobs':'float'},
                skipinitialspace=True,
                na_values=[-9.99,-99.9])
        self.GRPobs['date'] = pd.to_datetime(
                self.GRPobs['date'],
                format='%Y%m%d%H')
        self.GRPobs["Qobs"] *= 0.001 #conversion en m3/s
        self.GRPobs.set_index(['station','date'],inplace=True)

        self.GRPobs.sort_index(inplace=True)
        self.GRPobs.sort_index(axis=1, inplace=True)

        #GRPprev
        GRPprev = []
        for scenario in self.scenarios:
            #lecture de GRP_Prev_00xx.txt
            GRPprevSc = pd.read_csv(
                    self.dossierSortie+"\\GRP{}_Prev_{}.txt".format(
                            self.prefixe,
                            self.numScenarios[scenario]),
                    sep=';',
                    usecols=[1,2,3,4],
                    names=['station','date','Qprev','Pprev'],
                    skiprows=1,
                    skipfooter=1,
                    engine='python',
                    dtype={'station':'str',
                           'date':'str',
                           'Qprev':'float',
                           'Pprev':'float'},
                    skipinitialspace=True,
                    na_values=[-9.99,-99.9])
            GRPprevSc['date'] = pd.to_datetime(
                    GRPprevSc['date'],
                    format='%Y%m%d%H')
            GRPprevSc["Qprev"] *= 0.001 #conversion des l/s en m3/s
            GRPprevSc["scenario"] = scenario
            GRPprevSc.set_index(['station','scenario','date'],inplace=True)

            #récup de t_prev directement dans les fichiers de sortie
            #(t_prev utile pour lire les Inc + pour sauvegarder)
            if not hasattr(self, "t_prev"): #pour ne le faire qu'une fois
                self.t_prev = GRPprevSc.index.levels[-1][0].to_pydatetime() \
                         - td(hours=1)

            #lecture de \INC\GRP_Prev_00xx.txt
            cheminInc = self.dossierSortie+"\\INC\\GRP{}_Prev_{}.txt".format(
                                self.prefixe,
                                self.numScenarios[scenario])
            try:
                GRPincSc = pd.read_csv(cheminInc,
                        sep=';',
                        usecols = [0,1,3,4],
                        names=['station','date','q10','q90'],
                        skiprows=1,
                        skipinitialspace=True,
                        )
            except IOError:
                ptrim(u"""Fichier {} introuvable : pas d'incertitude
                      pour GRP avec le scénario {}.
                      """
                      .format(cheminInc, scenario))
            else:
                #conversion temps relatif en date
                GRPincSc['date'] = self.t_prev + \
                    pd.to_timedelta(GRPincSc['date'],unit='h')
                GRPincSc["scenario"] = scenario
                GRPincSc.set_index(['station','scenario','date'],inplace=True)

                #concatenation GRPprevSc et GRPincSc
                GRPprevSc = pd.concat(
                        [GRPprevSc, GRPincSc],
                        axis=1,
                        join='outer')

            GRPprev += [GRPprevSc]

        self.GRPprev = pd.concat(GRPprev, sort=True)
        
        #cas aucune incertitude : ajout colonnes q10, q90 de NaN
        if "q10" not in self.GRPprev.columns:
            import numpy as np
            self.GRPprev["q10"] = np.nan
            self.GRPprev["q90"] = np.nan

        self.GRPprev.sort_index(inplace=True)
        self.GRPprev.sort_index(axis=1, inplace=True)

        
        self.GRPfini = True


    def calcul_sum_P(self, station, t_deb, t_fin):
        u"""calcule la somme des de la pluie obs et les sommes des pluies
        prévues sur la période choisie
        Utile pour Phoeniks et Analog.
        
        Paramètres :
            - station 
            - t_deb format dt, date de début de la période
            - t_fin format dt, date de fin   de la période
            
        Sortie :
            - sumPobs  float     pluie obs sur la période
            - sumPprev pd.Series pluie prev sur la période, 
                                 scénarios de pluie en index
        
        """        
        
        sumPobs = self.Pobs .loc[(station,slice(t_deb,t_fin)),"Pobs"].sum()
        sumPprev= self.Pprev.loc[(station,slice(t_deb,t_fin)),slice(None)].sum()
        
        return sumPobs, sumPprev

    def pilote_Phoeniks(self, config, q0, t_deb, t_fin):
        u"""pilotage de Phoeniks pour la config sélectionnée
        donne les prévisions pour chaque scénario de pluies sélectionnées
        entre t_deb et t_fin, avec débit de base q0 à t0
        
        Paramètres :
            - config, # de la config issu de phoeniks.csv
            - q0 débit de base
            - t_deb heure de début de la sélection de pluie
            - t_fin heure de fin   de la sélection de pluie
            
        Sorties :
            - PHOprev DataFrame des résultats de phoeniks
            index : scenarios de pluie
            colonnes : CG, Qprev, Hprev
            - t_max heure du max prévu (indépendante du scénario de pluie)
        
        """

        station = PHOENIKS.loc[config, "stations"]
        k_Q   = PHOENIKS.loc[config, "constante_Q"]
        cQ0_Q = PHOENIKS.loc[config, "coeff_Q0_Q"]
        cCG_Q = PHOENIKS.loc[config, "coeff_CG_Q"]
        k_t   = td(hours=PHOENIKS.loc[config, "constante_heure"])
        cCG_t = PHOENIKS.loc[config, "coeff_CG_heure"]
        			        
        #calculs des cumuls générateurs
        sumPobs, sumPprev= self.calcul_sum_P(station, t_deb, t_fin)

        #construction tableau CG + résultats
        PHOprev = pd.DataFrame(
                data={"CG":0, "Qprev":0},# "t_max":t0},
                index=self.scenarios)
        #remplissage colonne CG
        if not sumPprev.empty:
            PHOprev["CG"] = sumPprev            
        if not np.isnan(sumPobs):
            PHOprev["CG"] += sumPobs
        
        #calculs sortie déterministe
        PHOprev["Qprev"] = (k_Q + cQ0_Q*q0) + cCG_Q*PHOprev["CG"]
        PHOprev["Hprev"] = PHOprev["Qprev"].apply(self.CT[station])
        t_max = t_deb + k_t + td(seconds=cCG_t*(t_fin-t_deb).total_seconds())
        
        return PHOprev, t_max
    
    def pilote_Analog(self, station, q0, Pmin, Pmax):
        u"""pilotage d'Analog à la station sélectionnée :
        Récupère les événements de la base Analog à la station 
        tq Pmin <= CG <= Pmax
        si Pmin == Pmax, tri dans un intervalle de +/- 1 mm
        
        Trie les événements par |q0 - q0_événement| croissant
        
        Paramètres :
            - station
            - q0 débit de base
            - Pmin borne basse cumul générateur
            - Pmax borne haute cumul générateur         
        
        """
        
        #lecture base Analog à la station
        if station not in self.bddANA:
            self.bddANA[station] = pd.read_csv(
                    CONFIGDIR+"Analog_base/{}.csv".format(station),
                    skiprows=[1],
                    parse_dates=["Debut_pluie","Fin_pluie",
                                 "Debut_montee","Fin_montee"],
                    dayfirst=True)
        
        #cas Pmin == Pmax: construction intervalle de 2mm
        if Pmin == Pmax:
            Pmin -= 1
            Pmax += 1
        
        #sélection des événements analogues
        analog = self.bddANA[station].loc[
                (self.bddANA[station].CumulRadar >= Pmin) 
                & 
                (self.bddANA[station].CumulRadar <= Pmax)
                ].copy()
        analog["Qdiff"] = abs(analog["Qdeb"] - q0)
        analog.sort_values(by="Qdiff", inplace=True)
        
        #dictionnaire des événements déjà lus en base Sacha
        #clés : index de self.bddANA[station]
        #valeurs : (Qeve, Peve) de l'événement
        self.sachaANA = {}
        #liste des événements analogues
        self.evesANA = analog.index

    
    def select_evenement(self, station, eve):
        u"""Sélectionne l'événement choisi comme événement principal pour
        l'affichage graphique.
        Interroge la base Sacha si l'événement n'est pas encore lu.
        
        Paramètres :
            - station code de la station choisie
            - eve index de l'événement dans self.bddANA[station]
        
        """
        
        #lecture base Sacha
        if station not in self.sachaANA:
            self.sachaANA[station] = self.lecture_Sacha_Analog(station, eve)        
        elif eve not in self.sachaANA[station].index. \
                            get_level_values(level="evenement"):            
            self.sachaANA[station] = pd.concat(
                    [self.sachaANA[station],
                     self.lecture_Sacha_Analog(station, eve)])
            self.sachaANA[station].sort_index(level="evenement", inplace=True)
            
        self.selectANA = eve
        
    
    def lecture_Sacha_Analog(self, station, eve):
        u"""interroge la base Sacha pour chercher les données de l'événement
        + conversion Q vers H
        
        Paramètres :
            - station
            - eve index de l'événement dans self.bddANA[station]
            
        Sortie :
            - QPeve df des données Q, P et H sur l'événement
            colonnes : Qobs, Pobs, + Hobs si CT
                   
        """
        
        sEve = self.bddANA[station].loc[eve]

        Qeve = acquisition.get_obs_Sacha(
                stations=[station],
                grandeur="Q",
                t_deb=sEve.loc["Debut_montee"],
                t_fin=sEve.loc["Fin_montee"], # + td(hours=48),
                bddTR=False
                )[0]

        if Qeve.empty:
            raise AnalogError("Pas de donnee en base Sacha pour cet evenement")
        
        Qeve = self.conversion_Q_H(Qeve,["Qobs"],["Hobs"])
        
        Peve = acquisition.get_obs_Sacha(
                stations=[station],
                grandeur="P",
                t_deb=sEve.loc["Debut_pluie"],
                t_fin=sEve.loc["Fin_pluie"],
                bddTR=False
                )[0]
        
        QPeve = pd.concat([Qeve, Peve], axis=1).reset_index()
        del QPeve["station"]
        QPeve["evenement"] = eve
        QPeve.set_index(["evenement", "date"], inplace=True)        
        
        return QPeve

    def xml_unitaire(self, station, scenario, modele="GRP", QH="Q"):
        u"""construit le xml format Sandre pour lecture dans l'EAO,
        pour les paramètres station, modele, scenario souhaités
        
        Paramètres :
            - station code de la station
            - scenario libellé du scénario modèle
            - modele  défaut "GRP" modèle à exporter. (GRP slmt pour le moment)
            - QH      défaut "Q" unité, "Q" ou "H"
               
        """
        #construction série du même format que libhydro.simulation.Previsions
        #double index [dte, prb]
        if QH == "Q":
            cols = ["Qprev","q10","q90"]
            conv = 1000 #conversion Q des m3/s aux l/s
            entite = entite = LbHsitehydro.Sitehydro(code=station)
        elif QH == "H":
            cols = ["Hprev","h10","h90"]
            conv = 10 #conversion H des cm aux mm
            entite = LbHsitehydro.Stationhydro(code=station
                                    +STATIONS.loc[station,"suffixe_st"])
        
        prv = self.GRPprev.loc[(station,scenario),cols].dropna()
        prv.rename(columns=dict(zip(cols,[50,0,100])),inplace=True)
        prv = prv.stack()
        prv.index.names = ["dte","prb"]
        prv *= conv #gestion unité     
        
        type_modele = "76gGRPt000"

        commentaire = trim(
                """{{ContexteSimul}}
                       {{CodeScenarioSimul}}{}_{}{{/CodeScenarioSimul}}
                       {{DtBaseSimul}}{}{{/DtBaseSimul}}
                   {{/ContexteSimul}}"""
                   .format(modele,scenario, 
                           dt.strftime(self.t_prev,"%Y-%m-%dT%H:%M:%S"))
                   )
        
        simul = LbHsimulation.Simulation(
            entite=entite,
            grandeur=QH,
            modeleprevision = LbHmodeleprevision.Modeleprevision(type_modele),
            public=False,
            intervenant = self.SACN,
            dtprod=self.t_prev, #date dernière obs, voir doc EAO
            previsions = prv,
            commentaire = commentaire
            )

        return simul, prv

    def export_xml(self, configs, repertoire):
        u"""exporte les sorties de modèles choisies au format XML
        Pour l'instant GRP seulement, en Q et H
        
        Paramètres :
            - configs liste ou tuple de tuples (station, scénario)
            exemple : [("H6230210","MoyMax"),
                       ("H4130410","MoyMin")]
            - repertoire chemin du répertoire où écrire les fichiers
        
        """
        
        #en-tête
        self.SACN = LbHintervenant.Intervenant(
                code=13000626500016,origine='SIRET'
                )
        contact = LbHintervenant.Contact(
                code=613,
                intervenant=self.SACN
                )       
        xmlScenario = LbHxml.Scenario(
                emetteur=contact,
                destinataire = self.SACN,
                dtprod=dt.utcnow()
                )

        #corps du xml
        xmlSimul = []
        errors = []        
        for config in configs:
            try:                
                xmlSimul += [self.xml_unitaire(
                        station=config[0], 
                        scenario=config[1],
                        QH="Q")[0]]
                if not self.echecCT:
                    xmlSimul += [self.xml_unitaire(
                            station=config[0], 
                            scenario=config[1],
                            QH="H")[0]]                    
            except:
                errors += [config]

        if len(errors) > 0:            
            ptrim(u"""Export XML impossible pour les sorties de modèles :
                """+ "\n".join(str(config) for config in errors)
                )                    
        if len(xmlSimul) == 0:
            ptrim(u"""# Export XML impossible #""")
            return
        
        xmlMsg = LbHxml.Message(
                scenario=xmlScenario,
                simulations = xmlSimul
                )
        nom = "{}_{}.xml".format(
            dt.strftime(self.t_prev, "%y%m%d-%Hh%M"),
            dt.strftime(dt.utcnow(), "%y%m%d-%Hh%M%S")
            )
        chemin = os.path.join(repertoire,nom)        
        xmlMsg.write(chemin, force=True, bdhydro=True)
                # Force : remplace un fichier existant
                # bdhydro : formate le xml dans le format specifique PhYC, 
                # sinon xml_hydrométrie classique

        ptrim(u"""# XML enregistré avec succès #
              {}""".format(chemin))


    def export_csv(self, configs, repertoire):
        u"""exporte les sorties de modèles choisies au format CSV
        Pour l'instant GRP seulement, en Q et H
        
        Paramètres :
            - configs liste ou tuple de tuples (station, scénario)
            exemple : [("H6230210","MoyMax"),
                       ("H4130410","MoyMin")]
            - repertoire chemin du répertoire où écrire les fichiers
        
        """

        #réindexage + pratique pour slicing
        self.csvPrev = self.GRPprev.reset_index() \
                        .set_index(["station","scenario"])         
        #slicing sorties de modèles
        self.csvPrev = self.csvPrev.loc[
                [(config[0], config[1]) for config in configs]
                ]
        self.csvPrev.reset_index(inplace=True)
        self.csvPrev.rename(
                columns={u"Qprev":u"Qprev_m3/s",
                         u"Pprev":u"Pprev_mm",
                         u"Hprev":u"Hprev_cm",
                         },
                         inplace=True)        

        #ajout colonne t_prev, pour comparer des sorties de modèles
        self.csvPrev[u"t_prev"]=self.t_prev
        
        mappers = {
                u"troncon": u"troncon",
                u"nom": u"nom_ascii",
                u"affluent": u"affluent_ascii"
                }        
        for col in mappers:
            self.csvPrev[col] = self.csvPrev[u"station"].map(
                    STATIONS[mappers[col]].to_dict()
                    )
        nom = "{}_{}.csv".format(
            dt.strftime(self.t_prev, "%y%m%d-%Hh%M"),
            dt.strftime(dt.utcnow(), "%y%m%d-%Hh%M%S")
            )
        chemin = os.path.join(repertoire,nom)        
        self.csvPrev.to_csv(
                chemin,
                sep=";",
                index=False,
                encoding="utf-8"
                )
    
        ptrim(u"""# CSV enregistré avec succès #
              {}""".format(chemin))
        
        
class RunModeles(ModelesInit, acquisition.Acquisition):
    u"""classe de pilotage des modèles en mode temps réel ou rejeu
    
    fonctionnalités définies à ce niveau :
        - acquisition et traitement des données d'entrée
        - pilotage de GRP :
           - construction des fichiers d'entrée
           - lancement du modèle
           - lecture des fiches contrôle (pdf)
        - sauvegarde du run
    
    """
    def __init__(self, TR, rejeu, date_rejeu=None):
        
        ModelesInit.__init__(
                self, 
                TR=TR,
                rejeu=rejeu,
                chargement=False
                )
        acquisition.Acquisition.__init__(
                self, 
                rejeu=self.rejeu, 
                date_rejeu=date_rejeu
                )    
        
        ptrim(u"""### Nouvelle session ###
                  Mode : {}
                  Date pivot : {} (TU)""".format(
        u"Rejeu" if self.rejeu else u"Temps réel",
       dt.strftime(self.t_prev, "%d/%m/%Y %H:%M")))
        
        #retient si run déjà sauvegardé ou pas
        self.isSaved = False

    def acquis(self, stations, profondeur=td(hours=48)):
        u"""acquisition des données d'entrée et courbes de tarage

        """
        
        ptrim(u"# Acquisition des données d'entrée #")
        self.get_donnees_entree(stations, profondeur)
        self.get_CT()
        self.Qobs = self.conversion_Q_H(self.Qobs,["Qobs"],["Hobs"])
        
        ptrim(u"""# Acquisition terminée #
                  {} station{}""".format(
                  len(self.stations),
                  "" if len(self.stations)==1 else "s")
              )
        
        self.stationsGRP = [station for station in self.stations 
                       if not np.isnan(STATIONS.loc[station,"GRP_horizon"])]
        self.stationsPHO = [station for station in self.stations
                       if station in PHOENIKS["stations"].values]

        
    def lance_traitement_donnees_entree(self, Pmanu):
        u"""pilote l'intégration des scénarios de pluie manuels et le
        traitement de la pluie prévue
        
        Paramètres :
         - Pmanu  None si pas de sc de pluie manuels, 
                  DataFrame sinon
        
        """       
        #TODO supprimer cette fonction qui devient inutile par rapport
        # à celle de niveau acquis, ou trouver une plus value
        self.traitement_donnees_entree(Pmanu=Pmanu)
            

    def pilote_GRP(self):
        u"""pilotage du lancement de GRP
        ne passe que les stations pour lesquelles GRP existe
        (colonne GRP_horizon de stations.csv)
        
        """
        
        self.construction_entree_GRP()
        self.lancement_GRP()
        self.lecture_sortie_GRP()
        self.dico_fiches_pdf()
        
        #Conversion Q vers H
        self.GRPobs = self.conversion_Q_H(
                self.GRPobs,
                ["Qobs"],
                ["Hobs"]
                )               
        self.GRPprev = self.conversion_Q_H(
                self.GRPprev, 
                ["Qprev", "q10", "q90"], 
                ["Hprev", "h10", "h90"] 
                )            

    def construction_entree_GRP(self):
        u"""écrit les fichiers d'entrée de GRP + modifie les fichiers de config

        nommage des scenarios de pluie de la forme :
            Scen_[xxx]_Plu[scenario].txt
            avec scenario : nom du scénario dans les colonnes de Pprev
            xxx : numéro à 3 chiffres, à partir de 000
            numérotation des scénarios de pluie d'après GRP_scenarios_pluie.csv
            le 1er chiffre (0) passe à la trappe
            
            - to do : scénarios manuels
        """

        #vide le dossier entrées 
        #(important : les sc de pluie qui trainent causent des bugs de GRP)
        for fichier in os.listdir(self.GRP_entrees):
            if fichier[-4:] == ".txt":
                os.remove(self.GRP_entrees+"\\"+fichier)
        
            
        #écriture fichiers avec données d'entrée
        # 1. Debit.TXT   Qobs
        fichierQ = "   ;station ;date    ;heure;Qobs ;\n"
        for (station, date) in self.Qobs.index:
            ligne = "DEB;{};{};{:.3f};\n".format(
                    station,
                    dt.strftime(date, "%Y%m%d;%H:%M")
                    ,self.Qobs.loc[(station, date), 'Qobs']
                    )
            fichierQ += ligne
        fichierQ += "FIN;OBS;\n"
        with open (self.GRP_entrees+"/Debit.txt", "w") as f:
            f.write(fichierQ)

        # 2. Pluie.TXT   Pobs
        fichierP = "   ;station ;date    ;heure;Pobs ;\n"
        for (station, date) in self.Pobs.index:
            ligne = "PLU;{};{};{:.3f};\n".format(
                    self.codeBV[station],
                    dt.strftime(date, "%Y%m%d;%H:%M")
                    ,self.Pobs.loc[(station, date), 'Pobs']
                    )
            fichierP += ligne
        fichierP += "FIN;OBS;\n"
        with open (self.GRP_entrees+"/Pluie.txt", "w") as f:
            f.write(fichierP)

        # 3. scénarios de pluie
        if not list(self.scenarios) == ["Pluie_nulle"]:
            for scenario in self.scenarios:
                fichierP = "   ;station ;date    ;heure;Pprev_{};\n"   \
                           .format(scenario)
                for (station, date) in self.Pprev[scenario].dropna().index:
                    ligne = "PLU;{};{};{:.3f};\n".format(
                            station,
                            dt.strftime(date, "%Y%m%d;%H:%M")
                            ,self.Pprev.loc[(station, date), scenario]
                            )                             
                    fichierP += ligne
                fichierP += "FIN;PRV;\n"
                with open (self.GRP_entrees+"/Scen_{}_Plu_{}.txt".format(
                                self.numScenarios[scenario][1:],
                                scenario
                                ), "w") as f:
                    f.write(fichierP)

        #màj des fichiers de config

        # 1. Config_Prevision.txt
        with open (self.GRP_params + "/Config_Prevision.txt", "r") as fIn:
            fichier = fIn.read().split("\n")
        # MODFON temps_reel / temps_diff
        if self.rejeu:
            fichier[6] = "Temps_diff"
            # INSTPR date_rejeu si rejeu
            fichier[9] = dt.strftime(self.date_rejeu,"%Y-%m-%d %H:%M:%S")
        else:
            fichier[6] = "Temps_reel"
        # OBSTYP TXT
        fichier[15] = "TXT"
        # CONFIR NON
        fichier[48] = "NON"        
        # SCENBR nb de scénarios de pluie
        #garder une valeur élevée (>= n° du dernier scénario de pluie)
        #sinon effets de bord dans GRP
        fichier[27] = "{:03n}".format(11) 
        # CODMOD codes modèles des fichiers de prévision
        suffixe = ""
        if self.rejeu: suffixe = "9999"
        fichier[45] = ";".join([self.numScenarios[sc] for sc in self.scenarios]
                              +[suffixe])

        with open (self.GRP_params + "/Config_Prevision.txt", "w") as fOut:
            fOut.write("\n".join(fichier))

        # 2. Liste_Bassins.DAT
        with open (self.GRP_params + "/Liste_Bassins.DAT", "r") as fIn:
            fichierIn = fIn.read().split("\n")
        #1/0 colonne C suivant si run à la station
        fichierOut = fichierIn[:24]
        for ligne in fichierIn[24:-1]:
            if ligne[1:9] in self.stationsGRP:
                ligne = ligne[:18] + '1' + ligne[19:]
            else:
                ligne = ligne[:18] + '0' + ligne[19:]
            fichierOut += [ligne]

        with open (self.GRP_params + "\\Liste_Bassins.DAT", "w") as fOut:
            fOut.write("\n".join(fichierOut)+"\n")        

    def lancement_GRP(self):
        u"""vide dossiers :
            - sorties,
            - fiches contrôle,
            - dernier import,
        puis lance GRP

        """
        #vide les fichiers de sortie
        #utile car effets de bord aux fichiers qui trainent
        for fichier in [f for f in os.listdir(self.GRP_sorties) 
                        if os.path.isfile(os.path.join(self.GRP_sorties, f))]:
            os.remove(os.path.join(self.GRP_sorties, fichier))            
        #vide le dossier Fiches_Controle
        #(utile pour accéder ensuite à la dernière fiche)
        for fiche in os.listdir(self.repoPdf):
            os.remove(self.repoPdf+fiche)
        for fichier in os.listdir(self.GRP_entrees+"\\Dernier_Import"):
            os.remove(self.GRP_entrees+"\\Dernier_Import\\"+fichier)
        
        ptrim(u"""# Lancement du run GRP #
                  {} stations""".format(len(self.stationsGRP)))
        subprocess.Popen(self.GRP_exe).wait()
        ptrim(u"# Fin du run GRP #")


    def dico_fiches_pdf(self):
        u"""construit dictionnaire des fiches performances de GRP aux stations
        (il ne doit exister qu'une seule fiche par station)

        """
        
        #TODO gérer erreurs avec les fiches pdf (notamment fiche ouverte)
        self.fiches_pdf = {}

        for station in self.stationsGRP:
            for fiche in os.listdir(self.repoPdf):
                if fiche[-12:-4] == station:
                    self.fiches_pdf[station] = fiche
                    break


    def sauvegarde(self, saveMode):
        u"""sauvegarde les données d'entrée et les résultats de GRP temps réel

        Argument :
            - saveMode: "M" pour manuel" ou "A" pour automatique

        Nom du dossier construit : de la forme 2018_09_13_09h00_M_01
        date t_prev en TU,
        saveMode M ou A,
        compteur sur 2 chiffres pour permettre plusieurs saves successives
        (le compteur commence à 1)

        fichiers sauvegardés :
          - GRP_obs.txt
          - GRP_prev_00xx.txt pour chaque scénario de pluie
          - INC/GRP_inc_00xx.txt pour chaque scénario de pluie
          - rapport_run.txt fichier contenant notamment la correspondance
          numéro/nom des scénarios de pluie

        """

        if self.isSaved == True:
            print(u"Il existe déjà une sauvegarde pour ce run.")
            return

        #nommage du dossier
        num = 1
        dossierSave = SAVEDIR + "{}_{}_{:02d}".format(
                dt.strftime(self.t_prev, "%Y_%m_%d_%Hh%M"),
                saveMode,
                num)
        #incrémentation du compteur s'il y a déjà une sauvegarde
        #pour le même couple saveMode, t_prev
        while 1:
            if os.path.isdir(dossierSave):
                num+=1
                dossierSave = SAVEDIR + "{}_{}_{:02d}".format(
                        dt.strftime(self.t_prev, "%Y_%m_%d_%Hh%M"),
                        saveMode,
                        num)
            else:
                break

        #construction du dossier
        os.mkdir(dossierSave)
        os.mkdir(dossierSave+"\\INC")
        
        #copie des données d'entrée
        self.Qobs.to_csv(dossierSave+"\\Qobs.csv",sep=";")
        self.Pobs.to_csv(dossierSave+"\\Pobs.csv",sep=";")
        self.Pprev.to_csv(dossierSave+"\\Pprev.csv",sep=";")

        #copie des fichiers de GRP
        shutil.copy2(self.GRP_sorties+"\\GRP_Obs.txt",dossierSave)
        for scenario in self.scenarios:
            shutil.copy2(
                    self.GRP_sorties+"\\GRP_Prev_{}.txt".format(
                            self.numScenarios[scenario]),
                    dossierSave
                    )
            cheminInc = self.GRP_sorties+"\\INC\\GRP_Prev_{}.txt".format(
                            self.numScenarios[scenario]
                            )
            if os.path.isfile(cheminInc): #gestion cas pb incertitude
                shutil.copy2(cheminInc, dossierSave+"\\INC")

        #rapport du run
        rapport = """### Sauvegarde de GRP temps reel ###
        
            Mode run: {} (M: manuel, A: automatique)
            sauvegarde {}_{:02d} du {}
            t_prev:{}

            stations:{}
            stationsGRP:{}
            stationsPHO:{}
                       
            # Scenarios de pluie #
        """.format(
                saveMode,
                saveMode, num, dt.strftime(dt.utcnow(), "%Y_%m_%d_%Hh%M"),                
                dt.strftime(self.t_prev, "%Y_%m_%d_%Hh%M"),
                ";".join(self.stations),
                ";".join(self.stationsGRP),
                ";".join(self.stationsPHO),
               )
        
        rapport = trim("\n".join(
                [rapport]+
                ["{};{}".format(scenario,self.numScenarios[scenario]) 
                 for scenario in self.scenarios]
                ))
        with open (dossierSave+"\\rapport_run.txt","w") as f:
            f.write(rapport)

        self.isSaved = True
        self.dossierSave = dossierSave

        ptrim(u"""# Run GRP sauvegardé #
              Dossier :\n{}""".format(self.dossierSave))


class ChargementModeles(ModelesInit):
    u"""classe de pilotage du chargement de save
    
    fonctionnalités définies à ce niveau :
        - chargement save
    
    """
    
    def __init__(self, dossierSave):
        self.dossierSave = dossierSave
        ModelesInit.__init__(self, TR=False, rejeu=False, chargement=True)
       
    def charger(self):
        u"""charge les paramètres, données d'entrées et données GRP du run
        
        """

        #suppression du dossier Temporaire s'il existe
        if os.path.isdir(TEMPDIR):
            shutil.rmtree(TEMPDIR)

        shutil.copytree(self.dossierSave, TEMPDIR)
        
        #lecture de rapport_run.txt
        with open (TEMPDIR+"rapport_run.txt", "r") as f:
            rapport = f.read()
            rapport = rapport.split("\n")
        self.t_prev = dt.strptime(rapport[4].split(":")[1], "%Y_%m_%d_%Hh%M")
        self.stations = rapport[6].split(":")[1].split(";")
        self.stationsGRP = rapport[7].split(":")[1].split(";")
        self.stationsPHO = rapport[8].split(":")[1].split(";")
        self.scenarios = [ligne.split(";")[0] for ligne in rapport[12:]]

        #niveaux de vigilance, CT
        self.get_CT()
        self.nivVigi = acquisition.get_niveaux_vigilance(self.stations)
        
        #Qobs, Pobs, Pprev
        self.Qobs = pd.read_csv(self.dossierSave+"/Qobs.csv",
                                sep=";",
                                parse_dates=["date"],
                                index_col = ["station","date"])
        #appel CT si pas de Hobs
        if "Hobs" not in self.Qobs.columns:
            self.Qobs = self.conversion_Q_H(self.Qobs,["Qobs"],["Hobs"])            
        self.Pobs = pd.read_csv(self.dossierSave+"/Pobs.csv",
                                sep=";",
                                parse_dates=["date"],
                                index_col = ["station","date"])
        self.Pprev = pd.read_csv(self.dossierSave+"/Pprev.csv",
                                sep=";",
                                parse_dates=["date"],
                                index_col = ["station","date"])
        
        #mise dans l'ordre des scénarios de pluie pour l'affichage
        self.scenarios = [sc for sc in SC_ORDRE if sc in self.scenarios]
        self.Pprev = self.Pprev[self.scenarios]
        
        #chargement GRP
        self.lecture_sortie_GRP()

        #Conversion Q vers H
        self.GRPobs = self.conversion_Q_H(
                self.GRPobs,
                ["Qobs"],
                ["Hobs"]
                )               
        self.GRPprev = self.conversion_Q_H(
                self.GRPprev, 
                ["Qprev", "q10", "q90"], 
                ["Hprev", "h10", "h90"] 
                )  

        ptrim(u"""### Chargement effectué ###
              Dossier de sauvegarde : {}
              Date pivot : {} (TU)
              {} stations dont {} GRP""".format(
              self.dossierSave,
              dt.strftime(self.t_prev, "%d/%m/%Y %H:%M"),
              len(self.stations), len(self.stationsGRP)
              )
              )
       
if __name__ == "__main__":
    ### paramètres ###
    stations = STATIONS.index[:2]
    t_rejeu = dt(year=2018, month=12, day=9, hour=12)
    profondeur = td(hours=12) 
    
    ### chargement save ###
#    run = ChargementModeles("Sauvegardes/2019_04_18_10h00_M_01")
#    run.charger()

    ### run temps réel ###
    run = RunModeles(
            TR=True,
            rejeu=False,
            )

    ### run rejeu ###
#    run = RunModeles(
#            TR=False,
#            rejeu=True,
#            profondeur=profondeur,
#            date_rejeu=t_rejeu,
#            )

    run.acquis(stations, profondeur=profondeur)
    run.traitement_donnees_entree()
    ### Phoeniks ###
#    run.pilote_Phoeniks(
#            config=0,
#            q0 = 10,
#            t_deb=run.t_prev-td(hours=48),
#            t_fin=run.t_prev+td(hours=48),
#            )
    
    ### Analog ###
#    run.pilote_Analog(stations[0], q0=100,Pmin=20,Pmax=25)
#    run.select_evenement(stations[0], 9)
#    run.select_evenement(stations[0], 0)
    
    ### GRP ###
    run.pilote_GRP()
#    run.sauvegarde(saveMode="M")
    print run.GRPprev.head()
    
    ### Export ###
#    run.export_xml(
#            [
#                ("H3100420","MoyMax","Q"), #Saumont
#                ("H3110410","MoyMax","H"), #Gournay
#                ("H3110410","RR3","H")     #Gournay
#            ],
#            "D:\PGRP_developpement")
    
