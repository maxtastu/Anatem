# -*- coding: utf-8 -*-
"""
Created on Tue Aug 14 17:21:42 2018

@author: m.tastu

définition et instantiation + ouverture de la plateforme
"""

import os
import sys
import pandas as pd
import subprocess
import threading
import csv
import pendulum
import time
from collections import OrderedDict
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from mainWindow import Ui_mainWindow, StationListWidgetItem
from dialog_export import DialogExport
from dialog_mode import DialogMode
from functools import partial, wraps
from datetime import datetime as dt, timedelta as td
from Pilote_Modeles import RunModeles, ChargementModeles, AnalogError
from global_ import *

@wraps
def threaded(function):
    u"""décorateur : lance la fonction dans un thread
    
    """

    def wrapper():
        threading.Thread(target=function).start()        
    return wrapper


class Anatem(QMainWindow, Ui_mainWindow):
    u"""classe de la plateforme.
    - propriétés principales de la fenêtre définies dans mainWindow.py
    - permet l'instanciation d'un unique run de modèles à la fois
        - par lancement temps réel ou rejeu
        - ou par chargement d'une sauvegarde
    - visualisation par graphes interactifs des sorties de
        - GRP
        - Phoeniks
        - Analog
        
    Après la fin du run GRP,
        - sauvegarde possible des fichiers du run
        - export possible
            - format XML
            - format CSV
    
    """
    
    signalGRPFini = pyqtSignal()
    signalFinAcquisBrute = pyqtSignal()
    signalFinAcquis = pyqtSignal()
    
    def __init__(self,parent=None):
        
        super(Anatem, self).__init__(parent)        
        self.setupUi(self)
        
        self.titre = (u"ANATEM (Anatem est la Nouvelle Application"
                      u" pour faire Tourner et Expertiser les Modèles)")
        self.version = "1.0.0"
        self.date = dt(year=2019, month=05, day=06)
        
        #icone et titre
        self.setWindowIcon(QIcon(PYDIR+"icon.ico"))
        self.setWindowTitle(self.titre)
        
        self.setAttribute(Qt.WA_DeleteOnClose)
        #http://stackoverflow.com/a/27178019/1119602
        
        #redirection print
        sys.stdout = StdoutRedirector(self.panneauStatus)
        
        ptrim(
            u"""Bienvenue sur Anatem
            Version {} du {}
            """
            .format(self.version, dt.strftime(self.date, "%d/%m/%Y"))
            )
                
        self.dialogMode = DialogMode(self)
        self.dialogMode.accepted.connect(self.new_run)
        self.dialogExport = DialogExport(
                parent=self, 
                repertoire=EXPORTDIR)
        self.dialogExport.btnExport.clicked.connect(self.pilote_export)

        self.actionSauvegarder.setEnabled(False)
        self.actionExport.setEnabled(False)
            
        self.actionNouveau_lancement.triggered.connect(self.dialogMode.exec_)
        self.btnValiderAcquisStations.clicked.connect(self.pilote_acquisition)
        self.btnValiderAcquisScenarios.clicked.connect(self.pilote_traitement_donnees_entree)
        self.signalFinAcquis.connect(self.init_vue_resultats)
        self.btnGRP.clicked.connect(partial(self.btnGRP.setEnabled,False))
        self.btnGRP.clicked.connect(self.lance_GRP)
        self.signalGRPFini.connect(self.suite_run_GRP)
        self.btnsQH.buttonClicked.connect(self.new_QH)
        self.comboBoxStations.currentIndexChanged.connect(
                partial(self.new_station,False))
        self.comboBoxScenarios.currentIndexChanged.connect(self.new_scenario)
        self.btnPdf.clicked.connect(self.affiche_fiche_perf)
        self.actionCharger.triggered.connect(self.ouvrir_dossier_save)
        self.actionSauvegarder.triggered.connect(
                partial(self.sauvegarde,u"Sauvegarder les résultats du run ?"))
        self.actionExport.triggered.connect(self.affiche_dialog_export)
        self.graphePHO.graphe.signalSelectPluie.connect(self.select_pluie_PHO)
        self.graphePHO.graphe.signalQ0.connect(self.set_Q0)
        self.formPHO.btnGo.clicked.connect(self.affiche_PHO)
        self.grapheANA.graphe.signalQ0.connect(self.set_Q0)
        self.grapheANA.graphe.signalSelectPluie.connect(self.select_pluie_ANA)
        self.formANA.btnGo.clicked.connect(self.affiche_tab_ANA)

        #construction dictionnaire noms de stations
        #noms de la forme TRONCON - Station (affluent le cas échéant)
        #TODO construire comme série avec un seul appel à STATIONS
        self.nomStation = {}
        for station in STATIONS.index:
            nomStation = u"{} - {}".format(
                    STATIONS.loc[station,'troncon'].upper(),
                    STATIONS.loc[station,'nom']
                    )
            affluent = STATIONS.loc[station,'affluent']
            if type(affluent) == unicode:
                nomStation += u" ({})".format(affluent)
            self.nomStation[station] = nomStation

        #remplissage liste sélection stations
        self.itemStation = {}
        for station in STATIONS.index:
            self.itemStation[station] = StationListWidgetItem(
                    parent=self.listAcquisStations,
                    code=station)
            self.itemStation[station].setText(self.nomStation[station])

        #checkBoxes de sélection groupées des stations
        self.checkBoxAll.toggled.connect(self.check_all)
        self.checkBoxNone.toggled.connect(self.check_none)
        for troncon in self.checkBoxStation:
            self.checkBoxStation[troncon].toggled.connect(
                    partial(self.check_troncon,troncon)
                    )
            
        self.headerPHO = {
                "CG": u"Cumul générateur (mm)", 
                "Qprev": u"Q max (m3/s)", 
                "Hprev": u"H max (cm)", 
                     }

        #noms de zones BP
        self.headerBP = {}
        with open(CONFIGDIR+"zones_BP_noms.csv") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.headerBP[unicode(row[0])] = unicode(row[1])
                
        self.slotCheckBoxesTabANA = True
                

    def __del__(self):
        u"""restaure sys.stdout à la fermeture de la plateforme
        
        """
        sys.stdout = sys.__stdout__

    def reinit(self):
        u"""réinitialise la plateforme avant lancement d'un nouveau run
        
        """
        self.mainView.setCurrentIndex(0)
        self.repaint()
        self.initFinie = False

        self.comboBoxStations.clear()   #menu déroulant des stations
        self.comboBoxScenarios.clear()  #menu déroulant des scénarios
        self.actionSauvegarder.setEnabled(False)
        self.actionExport.setEnabled(False)
        self.btnPdf.setEnabled(True)
        self.btnGRP.setEnabled(True)
        self.tabWidget.setCurrentIndex(0)
        self.stackGRP.setCurrentIndex(0)
        self.btnH.setEnabled(True)
        self.btnQ.setChecked(True)
        
        self.checkBoxAll.setChecked(False)
        for box in self.checkBoxStation.values():
            box.setChecked(False)
            
        self.formPHO.table.newDF(pd.DataFrame())
        self.formANA.table.newDF(pd.DataFrame())

            
    def new_run(self):
        u"""initie le run temps réel ou rejeu et passe à la page suivante

        paramètres :
            - self.rejeu True si rejeu, False si temps réel
            - self.date_rejeu date du rejeu si rejeu, None si temps réel

        """

        self.reinit()
        #récupère les paramètres du run : TR ou rejeu, date rejeu
        self.TR = self.dialogMode.ui.btnModeTR.isChecked()
        self.rejeu = self.dialogMode.ui.btnModeTD.isChecked()
        if self.rejeu:
            self.date_rejeu = self.dialogMode.ui.dtEditDateRejeu.\
            dateTime().toPyDateTime()
        else:
            self.date_rejeu = None

        #initialisation du run modèles
        self.run = RunModeles(
                TR=self.TR,
                rejeu=self.rejeu,
                date_rejeu=self.date_rejeu,
                )
        
        #page de choix des stations
        self.mainView.setCurrentIndex(1)

    def ouvrir_dossier_save(self):
        u"""pilote la sélection et l'ouverture d'un dossier de sauvegarde
        
        """
        dossier = str(QFileDialog.getExistingDirectory(
                self, #parent
                directory=SAVEDIR,
                ))
        if dossier == "":
            return
        self.reinit()
        self.run = ChargementModeles(dossierSave=dossier)
        self.run.charger()
        #affichage résultats
        self.btnPdf.setEnabled(False)
        self.actionExport.setEnabled(True)
        QMessageBox.information(
                self, #parent
                u"Chargement",  #titre
                u"Chargement terminé.", #texte"
                QMessageBox.Ok,  #bouton
                QMessageBox.Ok,  #bouton par défaut (touche entrée)
                )            
        self.signalFinAcquis.emit()
           
    def check_all(self):
        u"""sélectionne toutes les stations pour l'acquisition
        déselection : déselectionne toutes les stations sauf celles
        sélectionnées au niveau du tronçon
        
        """

        checked = self.checkBoxAll.isChecked()

        if checked == True:
            for station in self.itemStation:
                self.listAcquisStations.setItemSelected(
                        self.itemStation[station],
                        True
                        )

        elif checked == False:
            for troncon in self.checkBoxStation:
                self.check_troncon(troncon)

    def check_none(self):
        u"""déselectionne toutes les stations pour l'acquisition
        
        """

        if not self.checkBoxNone.isChecked():
            return
        
        self.repaint() #pour voir le bouton coché
        #déselection
        for station in self.itemStation:
            self.listAcquisStations.setItemSelected(self.itemStation[station],
                                                    False)
        #décoche toutes les checkBoxes
        for checkBox in [self.checkBoxAll, self.checkBoxNone] \
                            + self.checkBoxStation.values():
            checkBox.setChecked(False)
            
        time.sleep(0.1) #temps de voir le bouton coché                    


    def check_troncon(self, troncon):
        u"""sélectionne ou désélectionneles stations du tronçon choisi
        pour l'acquisition
        """

        checked = self.checkBoxStation[troncon].isChecked()
        for station in STATIONS.loc[STATIONS["troncon"]==troncon].index:            
            self.listAcquisStations.setItemSelected(
                        self.itemStation[station],
                        checked
                        )

    def affiche_fiche_perf(self):
        u"""ouvre la fiche performance GRP de la station courante

        """

        station = self.comboBoxStations.itemData(
                    self.comboBoxStations.currentIndex())
        #gestion comportement différent de Python simple et IPython
        #IPython => type(station) == unicode. QtCore.QVariant sinon
        if type(station) == QVariant: 
            station = unicode(station.toString())
            
        chemin = self.run.repoPdf + self.run.fiches_pdf[station]
        try:
            subprocess.Popen(chemin, shell=True)
        except:
            print(u"impossible d'ouvrir la fiche contrôle pour la station : {}"
                  .format(station))

    def pilote_acquisition(self):
        u"""gère l'acquisition des données d'entrée pour les stations
        sélectionnées(run TR ou rejeu)
        
        suites acquisition :
            - émission signalFinAcquisBrute
        
        """

        #récupération des stations sélectionnées
        stations_ = [item.code
                         for item in self.listAcquisStations.selectedItems()]
        #gestion si pas de sélection
        if len(stations_) == 0:
            return
        #met les stations dans l'ordre
        stations = [station for station in STATIONS.index 
                    if station in stations_
                    ]

        #acquisition
        self.run.acquis(
                stations,
                profondeur=td(hours=self.depthEdit.value())
                )

        #initialisation des tableaux pour les scénarios de pluie manuels
        Pmanu_1 = pd.DataFrame(
                index=self.run.zonesBP,
                columns=[dt(self.run.t_prev.year,
                            self.run.t_prev.month,
                            self.run.t_prev.day
                            )
                         +td(days=i+1) for i in range(3)]
                )

        cols = [dt.strftime(j.date()-td(days=1), "%d-%m-%Y")
                for j in Pmanu_1.columns]
        self.formScManuels.tab_M1.newDF(
                Pmanu_1,
                rowHeader=self.headerBP,
                colHeader=cols)
        self.formScManuels.tab_M2.newDF(
                Pmanu_1.copy(),
                rowHeader=self.headerBP,
                colHeader=cols)
        self.mainView.setCurrentIndex(2)

            
    def pilote_traitement_donnees_entree(self):
        u"""pilote le traitement des données d'entrée :
            - ajout scénarios de pluie manuels, traitement pluie prévue
            - TODO prolongation donnée de débit obs
        
        suite :
            - émission signal signalFinAcquis
        
        """
        
        #lecture des données de pluie manuelle
        Pmanu_1 = self.formScManuels.tab_M1.data.stack()
        Pmanu_2 = self.formScManuels.tab_M2.data.stack()
        Pmanu = pd.DataFrame({"Manuel_1": Pmanu_1,
                              "Manuel_2": Pmanu_2}
                )        
        #supprime colonnes vides éventuelles
        Pmanu.dropna(axis="columns", how="all", inplace=True)
        if Pmanu.empty: Pmanu = None
        
        self.run.lance_traitement_donnees_entree(Pmanu)        
        self.signalFinAcquis.emit()

        
    def init_vue_resultats(self):
        u"""suite à l'acquisition, préparation des objets associés à la vue
        des résultats du nouveau run
        
        - remplissage boîtes stations / scenarios / désac QH si pas de CT
        - Phoeniks
        - Analog
        - GRP
        - fenêtre export
        - initialisation remplissage graphe 
                -PHO + ANA si run
                -GRP + PHO + ANA si chargement
        - basculement vers fenêtre résultat #tabGRP différent si run ou chargement
        
        """
        
        ### remplissage comboboxes stations et scénarios ###
        for station in self.run.stations:
            self.comboBoxStations.addItem(self.nomStation[station], station)
        self.comboBoxScenarios.addItems(self.run.scenarios)
        
        ### btnH désactivé si pas de CT ###
        self.btnH.setEnabled(bool(1-self.run.echecCT))

        ### initialisation des variables associées à la navigation ###
        self.QH = self.grandeurs[self.btnsQH.checkedId()]
        self.scenar = str(self.comboBoxScenarios.currentText())        
        self.station = self.comboBoxStations.itemData(
                        self.comboBoxStations.currentIndex())
        #gestion comportement différent de Python simple et IPython
        #IPython => type(station) == unicode ; QtCore.QVariant sinon
        if type(self.station) == QVariant: 
            self.station = unicode(self.station.toString())  

        ### initialisation graphe Phoeniks ###
        self.graphePHO.toolbar.update()
        self.graphePHO.graphe.new_run(
            scenarios=self.run.scenarios,
            t_prev=self.run.t_prev,
            )

        ### initialisation graphe Analog ###
        self.grapheANA.toolbar.update()
        self.grapheANA.graphe.new_run(
            scenarios=self.run.scenarios,
            t_prev=self.run.t_prev,
            )
        
        ### initialisation graphe GRP si chargement de save ###
        if self.run.chargement:
            self.grapheGRP.toolbar.update()
            self.grapheGRP.graphe.new_run(
                    scenarios=self.run.scenarios,
                    t_prev=self.run.t_prev,
                    )
            self.stackGRP.setCurrentIndex(1)
            
        ### construction tableau pour export des sorties de modèle ###        
        self.dialogExport.table.newDF(
                data=pd.DataFrame(
                        index=self.run.stationsGRP,
                        data={sc:"GRP" for sc in self.run.scenarios}),
                rowHeader=self.nomStation
                )
        self.initFinie = True
        
        
        ### affichage résultats ###
        self.new_station()
        
        self.mainView.setCurrentIndex(3)

    def affiche_dialog_export(self):
        u"""redimensionne la fenêtre de dialogue pour l'export des sorties de
        modèles suivant les dimensions du contenu puis ouvre la fenêtre
        """

        self.dialogExport.resize(
                50  + self.dialogExport.table.width(),
                min(165 + self.dialogExport.table.height(), 600),
                )
        self.dialogExport.exec_()        

    @threaded
    def lance_GRP(self):
        
        self.run.pilote_GRP()        
        #run GRP fini : émission d'un signal GRP_fini
        self.signalGRPFini.emit()
        
    def suite_run_GRP(self):
        u"""opérations en fin de run de GRP
        
        """
        
        #activation actions post run GRP : sauvegarde, export
        if self.run.chargement == False:
            self.actionSauvegarder.setEnabled(True)
        self.actionExport.setEnabled(True)
        
        #graphe 
        self.grapheGRP.toolbar.update()
        self.grapheGRP.graphe.new_run(
                scenarios=self.run.scenarios,
                t_prev=self.run.t_prev,
                )
        #initialisation graphe GRP
        self.new_station(GRPonly=True)
        self.stackGRP.setCurrentIndex(1)

        #dialog signale fin run        
        if self.run.TR:            
            self.sauvegarde(
                msg=u"Run GRP terminé.\n\nSauvegarder les résultats ?"
                )
        elif self.run.rejeu:
            QMessageBox.information(
                    self, #parent
                    u"GRP",  #titre
                    u"Run GRP terminé.", #texte"
                    QMessageBox.Ok,  #bouton
                    QMessageBox.Ok,  #bouton par défaut (touche entrée)
                    )

    def pilote_export(self):
        u"""exporte les sorties de modèles sélectionnée suivant les formats
        et le répertoire choisis
        
        """
        
        try:        
            #Vérif au moins un format coché
            formats = [k for (k,v) in self.dialogExport.chboxes.items() 
                       if v.isChecked()
                       ]
            if len(formats) == 0:
                QMessageBox.warning(
                        self, 
                        u"Export impossible",
                        trim(u"""Aucun format sélectionné.
                              Choisir au moins un format à exporter."""), 
                        QMessageBox.Ok,
                        QMessageBox.Ok,
                        )
                return                
    
            #Vérif répertoire existant
            if not os.path.isdir(self.dialogExport.repertoire):
                QMessageBox.warning(
                        self.dialogExport, 
                        u"Export impossible",
                        trim(u"""Le répertoire d'export est invalide.
                              Choisir un répertoire existant."""),
                        QMessageBox.Ok,
                        QMessageBox.Ok,
                        )
                return
    
            #récupération des sorties sélectionnées
            configs = ()
            for (i, station) in enumerate(self.dialogExport.table.data.index):
                for (j, scenario) in enumerate(self.dialogExport.table.data.columns):
                    item = self.dialogExport.table.item(i,j)
                    if item.isSelected():
                        configs += (station, scenario, "Q"),
                        if not self.run.echecCT:
                            configs += (station, scenario, "H"),
            #Vérif au moins une sortie de modèle sélectionnée
            if len(configs) == 0:
                QMessageBox.warning(
                        self.dialogExport, 
                        u"Export impossible",
                        trim(u"""Aucune sortie de modèle sélectionnée.
                             Choisir au moins une sortie de modèle."""),
                        QMessageBox.Ok,
                        QMessageBox.Ok,
                        )
                return                    
            
            #Export
            if "XML" in formats:
                self.run.export_xml(configs, self.dialogExport.repertoire)
            if "CSV" in formats:
                self.run.export_csv(configs, self.dialogExport.repertoire)
            
        #UI
        except Exception as e:
            print str(e)
            QMessageBox.critical(
                self, #parent
                u"Export impossible",  #titre
                u"Echec de l'export : erreur inattendue", #texte"
                QMessageBox.Ok,  #bouton
                QMessageBox.Ok,  #bouton par défaut (touche entrée)
                )            

        else:
            QMessageBox.information(
                    self, #parent
                    u"Export",  #titre
                    u"Export effectué avec succès.", #texte"
                    QMessageBox.Ok,  #bouton
                    QMessageBox.Ok,  #bouton par défaut (touche entrée)
                    )
            self.dialogExport.accept()


    def new_QH(self):
        u"""gestion bascule affichage des résultats entre hauteur et débit
        
        """
        
        self.QH = self.grandeurs[self.btnsQH.checkedId()]
        if self.station in self.run.nivVigi.index:
            nivVigi = dict(self.run.nivVigi.loc[self.station,self.QH])
        else:
            nivVigi = {}

        _obs = "{}obs".format(self.QH)
        _prev = "{}prev".format(self.QH)
        _10 = "{}10".format(self.QH.lower())
        _90 = "{}90".format(self.QH.lower())

        
        if self.run.GRPfini and self.station in self.run.stationsGRP:
            self.grapheGRP.graphe.new_QH(
                QH=self.QH,
                Qobs=self.run.GRPobs.loc[self.station,_obs],
                Qprev=self.run.GRPprev.loc[self.station,[_prev,_10,_90]],
                nivVigi=nivVigi)
            
        self.graphePHO.graphe.new_QH(
                QH=self.QH,
                Qobs=self.run.Qobs.loc[self.station,_obs],
                nivVigi=nivVigi,
                )

        self.grapheANA.graphe.new_QH(
                QH=self.QH,
                Qobs=self.run.Qobs.loc[self.station,_obs],
                nivVigi=nivVigi,
                )
        
        
    def new_scenario(self):
        u"""changements affichage des sorties de modèles au changement de 
        scénario de pluie
        
        """

        if not self.initFinie: return
        
        self.scenar = str(self.comboBoxScenarios.currentText())
        #GRP
        if self.run.GRPfini:
            self.grapheGRP.graphe.new_scenario(self.scenar)
        #PHO   
        self.graphePHO.graphe.new_scenario(self.scenar)
        #ANA
        self.grapheANA.graphe.new_scenario(self.scenar)

        
    def new_station(self, GRPonly=False):        
        u"""gère le changement de station affichée
        
        paramètres:
            - GRPonly, default False.
            si True màj du graphe de GRP seulement, pour initialisation du
            graphe GRP à la fin du run
        
        """
        if not self.initFinie: return

        self.station = self.comboBoxStations.itemData(
                        self.comboBoxStations.currentIndex())
        #gestion comportement différent de Python simple et IPython
        #IPython => type(station) == unicode ; QtCore.QVariant sinon
        if type(self.station) == QVariant: 
            self.station = unicode(self.station.toString())  
        if self.station in self.run.nivVigi.index :
            nivVigi = dict(self.run.nivVigi.loc[self.station,self.QH])
        else:
            nivVigi = {}

        _obs = "{}obs".format(self.QH)
        _prev = "{}prev".format(self.QH)
        _10 = "{}10".format(self.QH.lower())
        _90 = "{}90".format(self.QH.lower())

        ### GRP ###
        self.grapheGRP.setVisible(self.station in self.run.stationsGRP)
        if self.run.GRPfini and self.station in self.run.stationsGRP:
            self.grapheGRP.graphe.new_station(
                    station=self.station,
                    Qobs=self.run.GRPobs.loc[self.station,_obs],
                    Pobs=self.run.GRPobs.loc[self.station, "Pobs"],
                    Qprev=self.run.GRPprev.loc[
                          self.station,[_prev,_10,_90]],
                    Pprev=self.run.GRPprev.loc[self.station,"Pprev"]
                                                  .unstack(level="scenario"),
                    nivVigi=nivVigi)
            
        if GRPonly: return
        
        #Visibilité graphe PHO et ANA suivant station
        self.splitterPHO.setVisible(self.station in self.run.stationsPHO)
        self.splitterANA.setVisible(self.station in self.run.stationsPHO)
        if self.station not in self.run.stationsPHO:
            return
            
        ### PHOENIKS ###
        self.formPHO.table.clearContents()
        self.formPHO.editQ0.setValue(0)
        self.formPHO.editDeb.setDateTime(self.run.t_prev)
        self.formPHO.editFin.setDateTime(self.run.t_prev)
        self.formPHO.labelCG.setText(u"0 h")
        self.formPHO.label_tMax.setText(u"")
        
        self.configsPHO.setCurrentIndex(self.idxConfigPHO[self.station])
        
        self.graphePHO.graphe.new_station(
                station=self.station,
                Qobs=self.run.Qobs.loc[self.station,_obs],
                Pobs=self.run.Pobs.loc[self.station,"Pobs"],
                Pprev=self.run.Pprev.loc[self.station],
                nivVigi=nivVigi)
        
        ### ANALOG ###
        self.formANA.table.clearContents()
        self.formANA.editQ0.setValue(0)
        self.formANA.editDeb.setValue(0)
        self.formANA.editFin.setValue(0)
                
        self.grapheANA.graphe.new_station(
                station=self.station,
                Qobs=self.run.Qobs.loc[self.station,_obs],
                Pobs=self.run.Pobs.loc[self.station,"Pobs"],
                Pprev=self.run.Pprev.loc[self.station],
                nivVigi=nivVigi)

    def select_pluie_PHO(self, deb, fin):
        u"""retient et affiche la plage de pluie sélectionnée 
        sur le graphique Phoeniks
        
        """
        
        self.formPHO.editDeb.setDateTime(deb)
        self.formPHO.editFin.setDateTime(fin)
        #pendulum.period meilleur que datetime.timedelta pour la durée en h
        hCG = (pendulum.instance(fin) - pendulum.instance(deb)).in_hours()
        self.formPHO.labelCG.setText("{} h".format(hCG))
        
    def select_pluie_ANA(self, deb, fin):
        u"""retient et affiche les CG min et et max suivant les scénarios
        de pluie, sur la plage sélectionnée depuis le graphique Analog
        
        """

        sumPobs, sumPprev= self.run.calcul_sum_P(self.station, deb, fin)
        self.formANA.editDeb.setValue(sumPobs + sumPprev.min())
        self.formANA.editFin.setValue(sumPobs + sumPprev.max())
               
        
    def set_Q0(self, t0, modele):
        u"""retient et affiche le Q0 sélectionné sur le graphe (PHO, ANA)
        
        paramètres :
            - t0 : date du Qobs à attraper. 
            doit être une date valide de self.run.Qobs
            - modele : "PHO" ou "ANA"
        
        """
        
        Q0 = self.run.Qobs.loc[(self.station,t0), "Qobs"]
        
        if modele == "PHO":
            form = self.formPHO
        elif modele == "ANA":
            form = self.formANA
        form.editQ0.setValue(Q0)
        
    def affiche_PHO(self):
        u"""lance le calcul de Phoeniks à la station en cours et affiche les
        résultats sur le graphe et le tableau
        
        """

        try:
            PHOprev, t_max = self.run.pilote_Phoeniks(
                config=self.btnsPHO[self.station].checkedId(), 
                q0=self.formPHO.editQ0.value(), 
                t_deb=self.formPHO.editDeb.dateTime().toPyDateTime(),
                t_fin=self.formPHO.editFin.dateTime().toPyDateTime()
                )
        except Exception as e:
            print str(e)
            ptrim(u"Erreur Phoeniks. Vérifier les paramètres.")
            return

        self.formPHO.table.newDF(
                PHOprev.T, 
                rowHeader=self.headerPHO)
        self.formPHO.label_tMax.setText(
                u"Date du maximum : {}"
                .format(dt.strftime(t_max, "%d/%m/%Y %H:%M"))
                )
        self.graphePHO.graphe.new_calcul_PHO(PHOprev, t_max)

    def affiche_tab_ANA(self):
        u"""trie les événements Analog pour les paramètres choisis, affiche
        les résultats dans le tableau et supprime les courbes courantes
        
        associe les checkBoxes du tableau à la fonction d'affichage des sorties      
        
        """
        
        try:
            self.run.pilote_Analog(
                    station=self.station,
                    q0=self.formANA.editQ0.value(),
                    Pmin=self.formANA.editDeb.value(),
                    Pmax=self.formANA.editFin.value()
                    )
            
        except:
            ptrim(u"Erreur Analog. Vérifier les paramètres.")
            return
        
        self.grapheANA.graphe.new_run_modele()
        
        self.formANA.table.newDF(
                self.run.bddANA[self.station].loc[
                        self.run.evesANA,
                        ["Debut_montee","CumulRadar","Qdeb","Qfin"]
                        ])
                
        for box in self.formANA.table.tabCheckBoxes.values():
            box.stateChanged_.connect(self.afficheANA)
            
        self.courbesANA = OrderedDict()
    
    def afficheANA(self, afficher, evenement):
        u"""slot associé au cochage/décochage des checkBoxes de tabANA.
        gère l'acquisition des données de l'événement Analog en base Sacha
        et l'affichage graphique
        
        Paramètres :
            - afficher booléen,
                si True ajouter, si False enlever l'événement du graphe
            - row ligne du graphe dans formABA.tabANA 
            (correspond au rang dans run.evesANA)
        
        """

        if self.slotCheckBoxesTabANA == False:
            return        

        #cas box cochée     
        if afficher == True:
            #cas où il y a de la place pour la courbe
            if len(self.courbesANA) < self.grapheANA.graphe.nCourbes:
                #get 1ère courbe vide
                for nCourbe in range(self.grapheANA.graphe.nCourbes):
                    if nCourbe not in self.courbesANA.values():
                        break
                self.add_eve_ANA(evenement, nCourbe)

            #cas trop de courbes : remplacer la plus ancienne
            else:                
                (old, nCourbe) = self.courbesANA.popitem(last=False) #pop 1er item
                self.add_eve_ANA(evenement, nCourbe)
                #décoche checkBox anvien événement
                #bool pour désactiver slot
                self.slotCheckBoxesTabANA = False
                self.formANA.table.tabCheckBoxes[old].setChecked(False)                
                    
        #cas box décochée
        else:
            nCourbe = self.courbesANA.pop(evenement)
            
            self.grapheANA.graphe.suppr_evenement(nCourbe)
            #si l'événement décoché est la sélection courante
            if evenement == self.grapheANA.graphe.selection:
                self.grapheANA.graphe.suppr_selection()
            #TODO revenir à la sélection précédente plutôt que de tout supprimer
            
        self.slotCheckBoxesTabANA = True

    def add_eve_ANA(self, evenement, nCourbe):
        u"""Analog : ajoute au graphe la courbe de l'événement choisi
        + la courbe choisie est la nouvelle sélection (affichage Q, P sélection)
        
        """
        
        self.courbesANA[evenement] = nCourbe
        try:
            self.run.select_evenement(self.station, evenement)
        except AnalogError:
            QMessageBox.warning(
                    self,
                    u"Analog",
                    u"Pas de donnée en base Sacha pour cet événement",
                    QMessageBox.Ok,
                    QMessageBox.Ok)
            self.slotCheckBoxesTabANA = False
            self.formANA.table.tabCheckBoxes[evenement].setChecked(False)                
            self.slotCheckBoxesTabANA = True
            return           
            
        Qeve = self.run.sachaANA[self.station].loc[evenement,["Qobs","Hobs"]].copy()
        #décalage temporel pour l'affichage graphique :
        #t_prev en début de montée
        delta_t = self.run.t_prev - \
               self.run.bddANA[self.station].loc[evenement, "Debut_montee"]
        Qeve.index = [idx + delta_t for idx in Qeve.index]
        self.grapheANA.graphe.new_evenement(
                nCourbe,
                Qeve=Qeve,
                )
        self.selectANA(evenement)        
        
            
    def selectANA(self, evenement):
        u"""met en avant la courbe Q/H de l'événement sélectionné
        + affiche son histogramme de P
        
        """
        
        QPeve = self.run.sachaANA[self.station].loc[evenement].copy()
        #décalage temporel pour l'affichage graphique :
        #t_prev en début de montée
        debut_montee = self.run.bddANA[self.station].loc[evenement, "Debut_montee"]
        delta_t = self.run.t_prev - debut_montee
               
        QPeve.index = [idx + delta_t for idx in QPeve.index]
        self.grapheANA.graphe.new_selection(
                evenement,
                QPeve=QPeve,
                label=dt.strftime(debut_montee, "%d/%m/%Y")
                )        
            

    def sauvegarde(self, msg):
        u"""sauvegarde les résultats du run courant
        Demande de confirmation préalable + vérification que la sauvegarde
        n'est pas déjà faite
        
        Paramètres :
            - msg str
            message de la MessageBox de confirmation avant sauvegarde

        """

        #demande de confirmation
        confirmation = QMessageBox.question(
                self,
                u"Sauvegarde",
                msg,
                QMessageBox.Yes | QMessageBox.No,  #bouton
                QMessageBox.Yes,  #bouton par défaut (touche entrée)
                )
        if confirmation == QMessageBox.No:
            return            
        
        if self.run.isSaved == True:
            QMessageBox.information(
                    self,
                    u"Sauvegarde GRP",
                    u"Il existe déjà une sauvegarde pour ce run.",
                    QMessageBox.Ok,
                    QMessageBox.Ok)
            return            
        
        try:
            self.run.sauvegarde(saveMode="M")
        except:
            QMessageBox.critical(
                    self,
                    u"Sauvegarde GRP",
                    u"Echec de la sauvegarde : erreur inattendue",
                    QMessageBox.Ok,
                    QMessageBox.Ok)
        else:
            QMessageBox.information(
                    self,
                    u"Sauvegarde GRP",
                    u"Sauvegarde effectuée avec succès",
                    QMessageBox.Ok,
                    QMessageBox.Ok)
            
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #ligne pour permettre d'ouvrir plusieurs fenêtres à la suite avec IPython :
    app.aboutToQuit.connect(app.deleteLater)
    anatem = Anatem()
    anatem.showMaximized()
    sys.exit(app.exec_())