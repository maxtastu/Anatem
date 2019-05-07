#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Gestion graphe matplotlib dans pilote
"""

import pandas as pd
import numpy as np
import pendulum
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from datetime import datetime as dt, timedelta as td
from PyQt4 import QtGui, QtCore
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor
from matplotlib.backends.backend_qt4agg \
    import FigureCanvasQTAgg as FigureCanvas, \
           NavigationToolbar2QT as NavigationToolbar
from global_ import *

import matplotlib.style; matplotlib.style.use('ggplot')

        
class GrapheWidget(QtGui.QFrame):
    u"""classe de Widget incluant graphe + barre d'outils + boutons H/Q.
    
    """
    def __init__(self,
                 classGraphe,
                 parent=None):
        QtGui.QFrame.__init__(self)
        self.setParent(parent)
        self.layout = QtGui.QVBoxLayout(self)

        self.graphe = classGraphe(self)
        self.layout.addWidget(self.graphe)

        self.frameToolbar = QtGui.QFrame(self)
        self.layoutToolbar = QtGui.QHBoxLayout(self.frameToolbar)
        self.layout.addWidget(self.frameToolbar)

        self.toolbar = NavigationToolbar(self.graphe, self)
        self.toolbar.setFixedWidth(500)
        self.layoutToolbar.addWidget(self.toolbar, alignment=QtCore.Qt.AlignLeft)
        self.layoutToolbar.addStretch(1)
    
        self.frameToolbar.setSizePolicy(QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Fixed))
        self.setSizePolicy(QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding))
        
class Graphe(FigureCanvas):
    u"""
    classe de widget graphe pour la visualisation des sorties de modèles

    """

    #signaux utilisés pour passer CG de pluie et Q0
    signalSelectPluie = QtCore.pyqtSignal(dt, dt)
    signalQ0 = QtCore.pyqtSignal(dt, str)

            
    def __init__(self,
                 parent=None,
                 titre=u"Titre graphe",
                 xtitre=u"Date (TU)",
                 ytitreP=u"Pluie horaire (mm)"):
        u"""
        construction du graphe

        """

        ###Construction de la figure et des deux subplots axQ, axP
        self.fig = Figure()
#        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        super(Graphe, self).__init__(self.fig)
        self.setParent(parent)        
        
        self.QH = "Q"

        self.setMinimumSize(QtCore.QSize(400, 300))

        gs = gridspec.GridSpec(4,1)
        self.axQ = self.fig.add_subplot(gs[1:,0])
        self.axP = self.fig.add_subplot(gs[0,0], sharex = self.axQ)

        self.axP.xaxis.tick_top()
        self.axP.invert_yaxis()

        #pour afficher la date dans la toolbar
        self.axQ.fmt_xdata = mdates.DateFormatter('%d/%m/%y %Hh%M')
        self.axP.fmt_xdata = mdates.DateFormatter('%d/%m/%y %Hh%M')

        #gestion des titres
        self.ytitreQH = {"Q": u"Débit (m3/s)",
                         "H": u"Hauteur (cm)"}
        self.unit = {"Q": u"m3/s",
                     "H": u"cm"}
        self.fig.suptitle(titre)
        self.axQ.xaxis.set_label_text(xtitre)
        self.axQ.yaxis.set_label_text(self.ytitreQH[self.QH])
        self.axP.yaxis.set_label_text(ytitreP)

        #forme des courbes
        self.colors = {    
                "obs"      : "#045a8d", #bleu#
                "Pluie_nulle": "#999999", #gris moyen
                #scenérios de pluie
                #palette : http://colorbrewer2.org 8-class dark2
                "RR3"      : "#666666", #gris foncé
                "MoyMin"   : "#1b9e77", #vert turquoise
                "MoyMoy"   : "#7570b3", #mauve
                "MoyMax"   : "#d95f02", #orange
                "LocMin"   : "#66a61e", #vert clair
                "LocMax"   : "#e7298a", #rose
                "Manuel_1" : "#e6ab02", #ocre clair
                "Manuel_2" : "#a6761d", #ocre foncé
                #seuils de vigilance
                "JB": "gold",
                "JH": "gold",
                "OB": "orange",
                "OH": "orange",
                "RB": "red",
                "RH": "red",
                }
        self.linestyles = {
                #seuils de vigilance
                "JB": "--",
                "JH": "-",
                "OB": "--",
                "OH": "-",
                "RB": "--",
                "RH": "-",
                }

        self.yQprevMin, self.yQprevMax = 0, 0
        self.yPselectMax = None   

        self.cursor = MultiCursor(self.fig.canvas,
                                  (self.axQ,self.axP),
                                  horizOn=True,
                                  vertOn=True,
                                  useblit=True,
                                  linestyle=":",
                                  color="gray",
                                  )

        #bulle suivant le pointeur de souris
        self.textCursorQ = self.axQ.text(
                0,
                0,
                "texte pointeur",
                ha="right",
                va="top",
                size=10,
                bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.7),
                zorder=200,
                )
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        
        self.x0 = None
        self.x1 = None
        self.CGselect = False
        self.textCumulP = self.axP.text(
                0,
                0,
                "texte cumul pluie",
                ha="right",
                va="top",
                size=10,
                bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.7),
                zorder=200,
                )
        self.fig.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
                
        #initialisation des courbes
        #Qobs
        self.cQobs, = self.axQ.plot_date(
                [0,0],
                [0,0],
                linestyle='-',
                marker=None,
                color=self.colors["obs"],
                label=u"observé",
                linewidth=2,
                zorder=100)        

        #niveaux de vigilance
        self.cNivVigi = {}
        for seuil in ["JB","JH","OB","OH","RB","RH"]:
            self.cNivVigi[seuil], = self.axQ.plot_date(
                    [0,0],
                    [0,0],                        
                    linestyle = self.linestyles[seuil],
                    linewidth=2,
                    marker=None,
                    color=self.colors[seuil],
                    label=None,
                    zorder=20
                    )

        #ligne verticale à tPrev
        self.ctprevQ, = self.axQ.plot(
                (0, 0),
                (0, 500),
                color='grey',
                linestyle='-',
                zorder=40)
        self.ctprevP, = self.axP.plot(
                (0, 0),
                (0, 100),
                color='grey',
                linestyle='-',
                zorder=40)

        #curseurs verticaux marquant le cumul de pluie sélectionné
        self.lineCursorDeb, = self.axP.plot(
                [0,0],
                [0,0],
                color = "blue",
                linestyle=":",
                zorder=120)                
        self.lineCursorFin, = self.axP.plot(
                [0,0],
                [0,0],
                color = "blue",
                linestyle=":",
                zorder=120)
        
        self.modele = None
        
    def new_run(self,
                scenarios,
                t_prev=None,
                ):
        u"""charge les paramètres du run : t_prev et scenarios de pluie
        adapte le graphe au nouveau t_prev.
        Réinitialise les courbes.

        Paramètres :
            - scenarios: liste des scénarios de pluie, dans l'ordre de SC_ORDRE
            - t_prev: date du lancement, par défaut dt.utcnow() si None

        """

        if t_prev:
            self.t_prev = t_prev
        else:
            self.t_prev = dt.utcnow()
        self.scenarios = scenarios
        self.scenar = self.scenarios[0] 
        #(les scénarios de pluie doivent être passés dans l'ordre pour ceci)
        
        #màj curseur vertical à t_prev
        self.ctprevQ.set_xdata([self.t_prev, self.t_prev])
        self.ctprevP.set_xdata([self.t_prev, self.t_prev])

        #retour à l'affichage en Q
        self.QH = "Q"
        
        #efface sélection de pluie
        self.lineCursorDeb.set_data(
                [0,0],
                [0,0],
                )
        self.lineCursorFin.set_data(
                [0,0],
                [0,0],
                )
        if hasattr(self, "plageSelectPluie"):
            self.plageSelectPluie.remove()        
        
        
        #spécificités du modèle
        self.new_run_modele()

        #étiquettes de l'axe des x :
        #h ttes les 6h + date sur la 1ère h du jour
        h_prev = dt(self.t_prev.year,
                    self.t_prev.month,
                    self.t_prev.day,
                    (self.t_prev.hour-self.t_prev.hour%6))
        #étiquettes de -48h à + 72h
        l_xticks = [h_prev + i*td(hours=6) for i in range(-8,13)]
        l_xticklabels = []
        for date in l_xticks:
            if date.hour in range(6) :
                label = dt.strftime(date, "%Hh\n%d/%m/%y")
            else:
                label = dt.strftime(date, "%Hh")
            l_xticklabels += [label]

        for ax in [self.axQ, self.axP]:
            ax.set_xticks(l_xticks)
            ax.set_xticklabels(l_xticklabels)
        #xlim : de -48h à +48h
            ax.set_xlim(self.t_prev-td(hours=48),self.t_prev+td(hours=48))

        
    def new_QH(self, QH, Qobs, nivVigi, Qprev=None):
        u"""changement d'affichage Q ou H
        
        mise à jour de :
            - valeurs courbes Q (ou H) obs, prev et niveaux de vigilance
            - échelle verticale Q
            - titre axe y
            
        paramètres :
            - QH grandeur en cours "Q" ou "H"
            - Qobs série avec date en index, Q (ou H) en valeur
            - Qprev (facultatif, pour GRP)
            - nivVigi dict des niveaux de vigilance de la station (QH courant)
                    
        """
        
        self.QH = QH
        self.Qobs = Qobs
        if Qprev is not None: self.Qprev = Qprev
        self.nivVigi = nivVigi
        
        #Qobs
        self.cQobs.set_xdata(self.Qobs.index.values)
        self.cQobs.set_ydata(self.Qobs.values)
        
        #Qprev
        self.new_QH_modele()
        
        #niveaux de vigilance        
        # WIP self.nivVigi dictionnaire des niveaux de vigilance courants
        for seuil in self.nivVigi:
            self.cNivVigi[seuil].set_xdata([self.t_prev-td(hours=48),
                                            self.t_prev+td(hours=72)])
            self.cNivVigi[seuil].set_ydata([self.nivVigi[seuil], 
                                            self.nivVigi[seuil]])
                
        #ajustement échelle verticale
        self.change_scale(Q=True)
        
        #màj titre axe y
        self.axQ.yaxis.set_label_text(self.ytitreQH[self.QH])

        self.draw()
        
    def new_scenario(self, scenar):
        u"""changement d'affichage suivant le scénario de pluie sélectionné
        
        mise à jour de :
            - affichage Pprev scénario principal
            - affichage Qprev --> incercitude sur scénario principal
            - légende Qprev
            - échelle verticale Q
            
        paramètres :
            - scenar scénario principal choisi
        
        """
        
        self.scenar = scenar
    
        #Pobs, Pprev   
        self.update_hist_pluie()
        
        #affichage sorties de modèle
        self.new_scenario_modele()
        
        #échelle verticale
        self.change_scale(Q=True)

        self.update_legend()
        self.draw()
        
    def new_station(self, station, Qobs, Pobs, Pprev, nivVigi, Qprev=None):
        u"""changement d'affichage suivant la station sélectionnée
        
        mise à jour de :
            - toutes les courbes affichées (Qobs, Qprev, Pobs, Pprev, nivVigi)
            - échelle verticale et horizontale
        
        paramètres :
            - station code hydro 3 nouvelle station
            - Qobs série avec date en index, Q (ou H) en valeur
            - Pobs série avec date en index, P en valeur
            - Qprev DataFrame forme suivant modèle (à compléter)
            - Pprev DataFrame date en index, scénarios de pluie en colonnes
            - nivVigi dict des niveaux de vigilance de la station (QH courant)
        les séries et DF doivent être ordonnés
                
        """
        
        self.station = station
        self.Qobs, self.Pobs, self.Pprev = Qobs, Pobs, Pprev
        self.nivVigi = nivVigi
        if Qprev is not None: self.Qprev = Qprev
        
        #Qobs
        self.cQobs.set_xdata(self.Qobs.index.values)
        self.cQobs.set_ydata(self.Qobs.values)

        #Qprev
        self.new_station_modele()

        #Pobs, Pprev   
        self.update_hist_pluie()
        self.lineCursorDeb.set_data(None,None)
        self.lineCursorFin.set_data(None,None)
        if hasattr(self, "plageSelectPluie"):
            try: 
                self.plageSelectPluie.remove()
            except ValueError:
                pass
            
        #niveaux de vigilance
        for seuil in self.cNivVigi:
            if seuil in self.nivVigi:
                self.cNivVigi[seuil].set_xdata([self.t_prev-td(hours=48),
                                                self.t_prev+td(hours=72)])
                self.cNivVigi[seuil].set_ydata([self.nivVigi[seuil],
                                                self.nivVigi[seuil]])
            else:
                self.cNivVigi[seuil].set_xdata([0,0])
                self.cNivVigi[seuil].set_ydata([0,0])

        self.change_scale(Q=True, P=True, t=True)        
        self.update_legend()
        self.draw()

    def new_run_modele(self):        
        return
    def new_station_modele(self):        
        return
    def new_scenario_modele(self):        
        return
    def new_QH_modele(self):        
        return
    
    def update_hist_pluie(self):
        u"""supprime et redessine les histogrammes de pluie avec les
        valeurs courantes de self.Pobs et self.Pprev[self.scenar]
        
        """        
        
        #suppression des tracés sur l'ax des pluies
#        self.axP.lines = []
        self.axP.containers = []
        self.axP.patches = []

        #nouveaux tracés Pobs, Pprev
        self.axP.bar(
                left=self.Pobs.index.values,
                height=self.Pobs.values,
                width=-1/24.,
                color=self.colors["obs"],
                zorder=100,
                )
        
        if self.scenarios != ["Pluie_nulle"]:
            self.axP.bar(
                    left=self.Pprev.index.values,
                    height=self.Pprev[self.scenar].values,
                    width=-1/24.,
                    color=self.colors[self.scenar],
                    zorder=100,
                    )
        
    def change_scale(self, Q=False, P=False, t=False):
        u"""change les échelles sur les deux graphes Q et P
        
        paramètres :
            - Q bool, default False. Si True chgt d'échelle verticale pr l'axQ
            - P bool, default False. Si True chgt d'échelle verticale pr l'axP
            - t bool, default False. Si True chgt d'échelle horizontale
        
        """
        
        ### débits ###
        if Q:
            self.yQmax = max(
                    self.Qobs.max(), 
                    self.yQprevMax,
                    self.nivVigi["JH"] if self.nivVigi else None)
                
            yQdelta = self.yQmax*0.05
            self.yQmax = self.yQmax + yQdelta
            self.yQmin = min(
                    self.Qobs.min() - yQdelta,
                    self.yQprevMin - yQdelta,
                    0)            
            self.axQ.set_ylim(self.yQmin, self.yQmax)
            
        ### pluie ###
        if P:
            self.yPmax = max(
                    self.Pobs.max(), 
                    self.Pprev.max().max(),
                    self.yPselectMax)
            self.axP.set_ylim(self.yPmax, 0)

        ### échelle horizontale ###
        if t:
            for ax in [self.axQ, self.axP]:
                ax.set_xlim(self.t_prev-td(hours=48),self.t_prev+td(hours=48))

    def update_legend(self):
        u"""met à jour la légende
        
        """    
        
        #TODO gestion plus robuste des légendes dynamiques (sc principal)
        legend = self.axQ.legend(
                loc='upper left',
                framealpha=0.9,
                numpoints=1,
                )
        legend.set_zorder(200)
        

    def on_press(self, event):
        u"""fonction rattachée au clic souris
        - supprime l'affichage de la précédente sélection de cumul de pluie
        - mémorise les infos pour passer à fct de on_click_and_drag_P
        
        """
        if event.inaxes == self.axP:
            self.x0 = event.xdata
            self.CGselect = True
            self.lineCursorDeb.set_data(None,None)
            self.lineCursorFin.set_data(None,None)
            if hasattr(self, "plageSelectPluie"):
                try: 
                    self.plageSelectPluie.remove()
                except ValueError:
                    pass

    def on_dbclick(self, event):
        u"""fonction associée au double-clic pour récupérer le débit de base
        associé
        
        """
        
        #si pas de double-clic renvoi à la fonction on_press classique
        #TO DO : plus élégant, gérer ces cas avec des signaux distincts
        if not event.dblclick:
            self.on_press(event)
            return
        if event.inaxes != self.axQ:
            return

        date = mdates.num2date(event.xdata)
        #retour à une date naïve
        date = date + td(minutes=30)
        date = dt(date.year,
                  date.month,
                  date.day,
                  date.hour,
                  date.minute
                  )
        
        #trouver idx de self.Qobs le plus proche de date
        t0 = min(self.Qobs.index, key = lambda d: abs(d - date))
        self.t0=t0
        Q0 = self.Qobs[t0]
        
        #afficher point de coordonnées (t0, Q0)
        self.cQ0.set_xdata([t0, t0])
        self.cQ0.set_ydata([Q0, Q0])
        
        #passer la valeur Q0
        self.signalQ0.emit(t0.to_pydatetime(),self.modele)
        
        self.Q0select = True

        
    def on_click_and_drag_P(self):
        u"""fonction gérant la sélection dynamique de la plage de pluie
        
        """                

        #dates de début et de fin de la sélection, dans l'ordre,
        #tronquées à l'heure
        self.deb = mdates.num2date(min(self.x0, self.x1))
        self.fin = mdates.num2date(max(self.x0, self.x1))
        self.deb = dt(self.deb.year, 
                      self.deb.month, 
                      self.deb.day, 
                      self.deb.hour)
        self.fin = dt(self.fin.year, 
                      self.fin.month, 
                      self.fin.day, 
                      self.fin.hour)
        self.debNum = mdates.date2num(self.deb)
        self.finNum = mdates.date2num(self.fin)

        #affichage de la plage sélectionnée
        #TODO voir à remplacer par un rectangle

        self.lineCursorDeb.set_data(
                [self.debNum, self.debNum],
                [0, 100])
        self.lineCursorFin.set_data(
                [self.finNum, self.finNum],
                [0, 100])
        if hasattr(self, "plageSelectPluie"):
            try: 
                self.plageSelectPluie.remove()
            except ValueError:
                pass
        self.plageSelectPluie = self.axP.fill_between(
                [self.debNum, self.finNum],
                0,
                100,
                color="skyblue",
                alpha=.5)
                
        #calcul des cumuls de pluie entre self.deb (exclu) et self.fin (inclus)
        sumPobs, sumPprev = 0, 0            
        if self.deb < self.t_prev:
            sumPobs  = self.Pobs[self.deb+td(hours=1):self.fin].sum()
        if self.fin > self.t_prev:
            if self.scenarios == ["Pluie_nulle"]:
                sumPprev = 0
            else:
                sumPprev = self.Pprev.loc[self.deb+td(hours=1):self.fin,
                                          self.scenar].sum()    

        #affichage bulle
        self.textCumulP.set_position([self.debNum,0])
        self.textCumulP.set_text(trim(
                u"""{} h
                cumul obs : {:.2f} mm
                cumul prévu : {:.2f} mm
                total : {:.2f} mm""".format(
                ( pendulum.instance(self.fin) 
                - pendulum.instance(self.deb)).in_hours(),
                sumPobs,
                sumPprev,
                sumPobs+sumPprev)))

        self.draw()
        
    def on_release(self, event):
        u"""fonction rattachée au clic souris relâché, pour fin de
        sélection cumul de pluie
        émission signal signalSelectPluie pour sélection du CG (PHO et ANA)        
        
        """

        
        if self.CGselect == True:
            self.signalSelectPluie.emit(self.deb, self.fin)

        self.CGselect = False
        self.textCumulP.set_text("")
     
    def on_mouse_move(self, event):
        u"""gestion des événements liés aux mouvements de la souris :
            - fenêtre de texte
                - déplacement
                - affichage données
            - si mouse_pressed (bool self.selectP) : selection cumul pluie

        """

        ### infobulle pluie sélectionne ###
        #indicateur de si une sélection de pluie est en cours
        if self.CGselect == True: 
            self.x1 = event.xdata
            self.on_click_and_drag_P()
            return

        ### infobulle Q suivant pointeur souris ###

        #suppression infobulle si souris hors du graphe Q
        if event.inaxes != self.axQ:
            self.textCursorQ.set_text("")
            self.draw()
            return
        else:
            pass

        date = mdates.num2date(event.xdata)
        #retour à une date naïve pour comparer avec t_prev (date naïve)
        # + troncage à l'heure pour correspondre au pas de temps de la donnée
        #décalage de 30 min pour aller à l'heure la plus proche
        date = date + td(minutes=30)
        date = dt(date.year,
                  date.month,
                  date.day,
                  date.hour,
                  )

        num = mdates.date2num(date)

        #cas hors des plages de données :
        #affichage date seule
        if (date <= self.t_prev and date not in self.Qobs.index) or \
           (date >= self.t_prev and date not in
                    self.Pprev.index):
            self.textCursorQ.set_text(trim(date.strftime("%d/%m/%y %Hh%M")))

        #cas plage de Qobs:
        #affichage date + Qobs
        elif date <= self.t_prev:
            self.textCursorQ.set_text(trim(
            u"""{}
                {}obs: {:.2f} {}"""
            .format(date.strftime("%d/%m/%y %Hh%M"),
                    self.QH,
                    self.Qobs[date],
                    self.unit[self.QH])
            ))
                
        else:
            self.on_mouse_move_prev(date)
 
        #infobulle
        self.textCursorQ.set_position([num,event.ydata])

        self.draw()

    def on_mouse_move_prev(self, date):
        u"""fonction non implémentée à ce niveau
        gestion prévisions affichées dans l'étiquette qui suit la souris
        
        """        
        return


class GraphePhoeniks(Graphe):
    u"""graphe résultats Phoeniks
    
    """

    def __init__(self,
                 parent=None,
                 titre=u"Phoeniks",
                 xtitre=u"Date (TU)",
                 ytitreP=u"Pluie horaire (mm)"):

        Graphe.__init__(self, parent, titre, xtitre, ytitreP)
        self.modele = "PHO"
        
        self.courbesPHO = {}
        self.fig.canvas.mpl_connect("button_press_event", self.on_dbclick)

        #initialisation des courbes spécifiques à Phoeniks        
        #Q0
        self.cQ0, = self.axQ.plot(
                    (0, 0),
                    (0, 0),
                    color="black",
                    marker="o",
                    zorder=120)
        #pour chaque scénario de pluie
        self.cQprev = {}
        for sc in SC_ORDRE:
            self.cQprev[sc], = self.axQ.plot_date(
                     [0,0],
                     [0,0],
                     linestyle="",
                     color=self.colors[sc],
                     label=None,
                     zorder=80)            
        
        #indicateur de si un Q0 est affiché sur le graphe, pour
        #conversion QH
        self.Q0select = True
        #indicateur de l'existence d'un calcul à la station courante
        self.calcul = False

    def new_run_modele(self):
        u"""réinitialise les éléments du graphe spécifiques de Phoeniks
        
        """
        
        #efface cQ0 et les cQprev
        for courbe in [self.cQ0] + self.cQprev.values():
            courbe.set_xdata([0,0])
            courbe.set_ydata([0,0])

        #affichage légende suivant scénario principal initial
        self.new_scenario_modele()        

    def new_QH_modele(self):
        u"""conversion des Qprev et Q0 de Phoeniks avec la CT
        
        """

        _prev = "{}prev".format(self.QH)
        
        if self.Q0select:
            Q0 = self.Qobs[self.t0]
            self.cQ0.set_ydata([Q0, Q0])            

        if self.calcul:
            for sc in self.scenarios:
                Qprev = self.PHOprev.loc[sc,_prev]
                self.cQprev[sc].set_ydata((Qprev, Qprev))
            self.yQprevMax = self.PHOprev[_prev].max()
            self.yQprevMin = self.PHOprev[_prev].min()
        
    def new_station_modele(self):
        
        #réinitialisation booléens indicateurs
        self.Q0select = False
        self.calcul = False
        self.yQprevMax, self.yQprevMin = 0, 0

        #réinitialisation Q0 et Qprev
        self.cQ0.set_xdata([0, 0])
        self.cQ0.set_ydata([0, 0])
        for sc in self.cQprev:
            self.cQprev[sc].set_xdata([0, 0])
            self.cQprev[sc].set_ydata([0, 0])

    def new_scenario_modele(self):
        u"""gestion changement de scénario pour Phoeniks :
            - modif visuel point nouveau scénario principal
            - màj légende
        
        """
        for sc in self.scenarios:
            self.cQprev[sc].set_marker("D" if sc==self.scenar else "o")
            self.cQprev[sc].set_markersize(8 if sc==self.scenar else 6)
            
    def new_calcul_PHO(self, PHOprev, t_max):
        u"""affichage prévisions de Phoeniks
        
        """
        
        _prev = "{}prev".format(self.QH)
        #affichage résultat
        for sc in self.scenarios:
            Qprev = PHOprev.loc[sc,_prev]
            self.cQprev[sc].set_xdata((t_max, t_max))
            self.cQprev[sc].set_ydata((Qprev, Qprev))
        #légende
            self.cQprev[sc].set_label(sc)
        self.new_scenario_modele()
        self.update_legend()
            
        self.calcul = True
        self.PHOprev = PHOprev
        
        #échelle verticale Q
        self.yQprevMax = PHOprev[_prev].max()
        self.yQprevMin = PHOprev[_prev].min()        
        self.change_scale(Q=True)
        
        self.draw()
        
    def on_mouse_move_prev(self,date):
        u"""gestion infobulle suivant le curseur : spécificités du modèle
        
        pour l'instant pas d'affichage dans le prévu pour Phoeniks
        TODO harmoniser avec affichage GRP
        
        """

        self.textCursorQ.set_text("")
        

class GrapheANA(Graphe):
    u"""graphe visualisation Analog

    """
    
    def __init__(self,
                 parent=None,
                 titre=u"Analog",
                 xtitre=u"Date (TU)",
                 ytitreP=u"Pluie horaire (mm)"):
        
        Graphe.__init__(self, parent, titre, xtitre, ytitreP)
        self.modele = "ANA"
        self.nCourbes = 5 #nb de courbes cQeve à afficher au maximum

        self.fig.canvas.mpl_connect("button_press_event", self.on_dbclick)
        
        #initialisation des variables spécifiques à Analog
        #Q0
        self.cQ0, = self.axQ.plot(
                    (0, 0),
                    (0, 0),
                    color="black",
                    marker="o",
                    zorder=120)
        
        #Qeve 
        self.cQeve = {}
        self.dataQeve = {} #données Q et H mémorisée pour conversion QH
        for nCourbe in range(self.nCourbes):
            self.cQeve[nCourbe], = self.axQ.plot_date(
                     [0,0],
                     [0,0],
                     linestyle='--',
                     marker=None,
                     color="grey",
                     zorder=79,
                     )
            
        #Qselect
        self.cQselect, =  self.axQ.plot_date(
                     [0,0],
                     [0,0],
                     linestyle='-',
                     marker=None,
                     color="brown",
                     linewidth=2,
                     zorder=80,
                     )
        
        
        self.yQeveMax = {}
        self.yQselectMax = 0
        self.selection = None
        
    def new_run_modele(self):
        u"""réinitialise les éléments du graphe spécifiques d'Analog
        
        """
        
        #cQO
        self.cQ0.set_xdata([0,0])
        self.cQ0.set_ydata([0,0])

        #cQeve
        courbes = self.dataQeve.keys()
        for nCourbe in courbes:
            self.suppr_evenement(nCourbe)
        #cQselect
        self.suppr_selection()
    
    def new_evenement(self, nCourbe, Qeve):
        u"""Affiche la courbe Q/H de l'événement choisi.
            
        Paramètres :
            - Qeve DF avec dates en index, Qobs (et Hobs éventuel) en valeur
        
        """
        
        _obs = "{}obs".format(self.QH)
                                
        #valeurs courbe Q
        self.cQeve[nCourbe].set_xdata(Qeve.index.values)
        self.cQeve[nCourbe].set_ydata(Qeve[_obs].values)
        self.dataQeve[nCourbe] = Qeve
        
        #échelle verticale
        self.yQeveMax[nCourbe] = Qeve[_obs].max()
        self.yQprevMax = max(max(self.yQeveMax.values()), self.yQselectMax)        
        self.change_scale(Q=True)
        
        self.draw()

    def suppr_evenement(self, nCourbe):
        u"""masque la courbe de l'événement choisi et efface les données
        mémorisées associées

        Paramètres :
            - nCourbe rang de la courbe à remplacer (dans range(self.n))
        
        """

        self.cQeve[nCourbe].set_xdata([0,0])
        self.cQeve[nCourbe].set_ydata([0,0])
        del self.dataQeve[nCourbe]

        self.yQeveMax[nCourbe] = None
        self.yQprevMax = max(max(self.yQeveMax.values()), self.yQselectMax)        
        self.change_scale(Q=True)
        self.draw()
        
    def new_selection(self, evenement, QPeve, label):
        u"""affiche et met en avant Q/H et P de l'événement choisi
        Paramètres :
            - evenement rang de l'événement en base
            - QPeve DF avec index dates
                            colonnes [Qobs, Pobs, Hobs éventuel]
            - label étiquette de la légende pour l'événement
            
        """

        _obs = "{}obs".format(self.QH)
        self.QPeve = QPeve

        self.selection = evenement
        self.cQselect.set_xdata(self.QPeve.index.values)
        self.cQselect.set_ydata(self.QPeve[_obs].values)
        self.cQselect.set_label(label)
        self.update_legend()
        
        self.update_hist_pluie()
        self.axP.bar(
                left=self.QPeve.index.values,
                height=self.QPeve["Pobs"].values,
                width=-1/24.,
                color="brown",
                zorder=101,
                alpha=.5
                )

        self.yQprevMax = max(max(self.yQeveMax.values()), self.yQselectMax)               
        self.yPselectMax = self.QPeve["Pobs"].max()
        self.change_scale(Q=True, P=True)
        
        self.draw()
        
    def suppr_selection(self):
        u"""supprime l'événement sélectionné et ses courbes
        
        """
        
        if self.selection is None:
            return
        
        self.selection = None
        self.cQselect.set_label(None)
        self.update_legend()
        self.cQselect.set_xdata([0,0])
        self.cQselect.set_ydata([0,0])
        self.update_hist_pluie()
        self.yQselectMax = None
        self.yQprevMax = max(max(self.yQeveMax.values()), self.yQselectMax)               
        self.yPselectMax = None
        self.change_scale(Q=True, P=True)

        self.draw()
        

    def new_QH_modele(self):
        u"""changement de grandeur Q ou H sur l'affichage graphique
        
        """
        
        _obs = "{}obs".format(self.QH)
        
        #conversion cQeve
        for nCourbe in self.dataQeve:
            self.cQeve[nCourbe].set_ydata(self.dataQeve[nCourbe][_obs].values)
            self.yQeveMax[nCourbe] = self.dataQeve[nCourbe][_obs].max()

        
        #conversion cQselect
        if self.selection is not None:
            self.cQselect.set_xdata(self.QPeve.index.values)
            self.cQselect.set_ydata(self.QPeve[_obs].values)
            self.yQselectMax = self.QPeve[_obs].max()
            
        #gestion échelle verticale
        self.yQprevMax = max(
                max(self.yQeveMax.values()) if self.yQeveMax else None, 
                self.yQselectMax
                )        
        self.change_scale(Q=True)
    
    def new_station_modele(self):
        u"""réinitialise les variables Analog au changement de station
        
        """
        
        courbes = self.dataQeve.keys()
        for nCourbe in courbes:
            self.suppr_evenement(nCourbe)
        self.yQevemax = {}
        self.suppr_selection()
        self.cQ0.set_xdata([0, 0])
        self.cQ0.set_ydata([0, 0])

    
    def new_scenario_modele(self):
        u"""au changement de scénario de pluie, réaffiche l'histogramme de pluie
        de l'événement sélectionné
        
        """
        
        if self.selection is not None:
            self.axP.bar(
                    left=self.QPeve.index.values,
                    height=self.QPeve["Pobs"].values,
                    width=-1/24.,
                    color="brown",
                    zorder=101,
                    alpha=.5
                    )

        
            
class GrapheGRP(Graphe):
    u"""graphe résultats GRP

    """    

    def __init__(self,
                 parent=None,
                 titre=u"GRP",
                 xtitre=u"Date (TU)",
                 ytitreP=u"Pluie horaire (mm)"):

        Graphe.__init__(self, parent, titre, xtitre, ytitreP)
        self.modele = "GRP"

        #ligne verticale à l'horizon de prévision
        self.cHrzQ, = self.axQ.plot(
                (0, 0),
                (0, 500),
                color='red',
                linestyle='-',
                zorder=40)
        self.cHrzP, = self.axP.plot(
                (0, 0),
                (0, 100),
                color='red',
                linestyle='-',
                zorder=40)
        
        #initialisation des courbes pour chaque scénario de pluie
        self.cQprev = {}
        for sc in SC_ORDRE:
            self.cQprev[sc], = self.axQ.plot_date(
                     [0,0],
                     [0,0],
                     linestyle="--",
                     marker=None,
                     color=self.colors[sc],
                     label=sc,
                     #MoyMax devant Loc si ce sont les mêmes courbes
                     zorder=79 if sc in ["LocMin","LocMax"] else 80,
                     )

    def new_errorbars_Q(self):
        u"""plot nouvelles barres d'incertitude pour les prévisions de GRP
        
        """

        #Gestion passage Débit/Hauteur
        _prev = "{}prev".format(self.QH)
        _10 = "{}10".format(self.QH.lower())
        _90 = "{}90".format(self.QH.lower())
        
        #supprimer errorbar courant
        self.axQ.containers = []
        if hasattr(self, "cInc"):
            self.cInc[0].remove()
            for line in self.cInc[1]+self.cInc[2]:
                line.remove()
            
        #plot nouveau errorbar
        qprev = self.Qprev.loc[self.scenar]
        self.cInc = self.axQ.errorbar(
                        qprev.index.values,
                        qprev[_prev].values,
                        yerr=np.array(
                        [qprev[_prev].values - qprev[_10  ].values,
                         qprev[_90  ].values - qprev[_prev].values]),
                        color=self.colors[self.scenar],
                        label=None,
                        linestyle='-',
                        marker=None,
                        linewidth=2,
                        zorder=100,
        #                capsize=0
                        )
        
    def new_QH_modele(self):
        u"""gère les spécificités de GRP lors du changement de grandeur
        
        """
        
        #c/c de new_station_modele

        #tracé des sorties de modèles
        
        #Gestion passage Débit/Hauteur
        self._prev = "{}prev".format(self.QH)
        self._10 = "{}10".format(self.QH.lower())
        self._90 = "{}90".format(self.QH.lower())
        
        #sorties déterministes
        for scenar in self.scenarios:
            qprev = self.Qprev.loc[scenar]
            self.cQprev[scenar].set_xdata(qprev.index.values)
            self.cQprev[scenar].set_ydata(qprev[self._prev].values)
        #errorbars scénario principal
        self.new_errorbars_Q()

        #scénarios en trop
        for scenar in [sc for sc in self.cQprev if sc not in self.scenarios]:
            self.cQprev[scenar].set_xdata([0,0])
            self.cQprev[scenar].set_ydata([0,0])        

        self.yQprevMax = self.Qprev.max().max()
        self.yQprevMin = self.Qprev.min().min()


    def new_run_modele(self):
        u"""spécificité de l'affichage graphique de GRP lors d'un nouveau run
        
        """
        
        #gestion de la légende 
        for sc in self.cQprev:
            #afficher seulement scénarios en cours
            self.cQprev[sc].set_label(sc if sc in self.scenarios else "")
            #mise en évidence scénario principal
            self.cQprev[sc].set_linestyle("-" if sc==self.scenar else "--")
            self.cQprev[sc].set_linewidth(2   if sc==self.scenar else 1)


    def new_scenario_modele(self):
        u"""gère les spécificités de GRP lors du changement de scénario :
        affichage barres d'incertitude scénario principal
        + sc principal mis en évidence dans la légende
        
        """

        #errorbars scénario principal
        self.new_errorbars_Q()

        for sc in self.cQprev:
            self.cQprev[sc].set_linestyle("-" if sc==self.scenar else "--")
            self.cQprev[sc].set_linewidth(2   if sc==self.scenar else 1)


    def new_station_modele(self): #, horizon):
        u"""gère les spécificités de GRP lors du changement de station :
            - màj courbe horizon du modèle
            - màj courbes sorties de modèles
        
        """
        
#        #tracé horizon de calage du modèle
#        self.cHrzQ.set_xdata((self.t_prev+horizon, self.t_prev+horizon))
#        self.cHrzP.set_xdata((self.t_prev+horizon, self.t_prev+horizon))
        
        #tracé des sorties de modèles

        #Gestion passage Débit/Hauteur
        self._prev = "{}prev".format(self.QH)
        self._10 = "{}10".format(self.QH.lower())
        self._90 = "{}90".format(self.QH.lower())
        
        #psorties déterministes seulement, pas d'errorbars
        for scenar in self.scenarios:
            qprev = self.Qprev.loc[scenar]
            self.cQprev[scenar].set_xdata(qprev.index.values)
            self.cQprev[scenar].set_ydata(qprev[self._prev].values)
        #scénarios en trop
        for scenar in [sc for sc in self.cQprev if sc not in self.scenarios]:
            self.cQprev[scenar].set_xdata([0,0])
            self.cQprev[scenar].set_ydata([0,0])
        #errorbars scénario principal
        self.new_errorbars_Q()
            
        self.yQprevMax = self.Qprev.max().max()
        self.yQprevMin = self.Qprev.min().min()
                 
    def on_mouse_move_prev(self, date):
        u"""gestion affichage texte associé au curseur sur la plage
        de prévision de GRP

        """
        #cas plage de Qprev sans incertitude:
        #affichage date + scenario + Qprev
        if np.isnan(self.Qprev.loc[(self.scenar,date),self._90]):
            self.textCursorQ.set_text(trim(
                u"""{}
                    scénario {}

                    {}prev: {:.2f} {unit}
                     """
                .format(
                    date.strftime("%d/%m/%y %Hh%M"),
                    str(self.scenar),
                    self.QH,
                    self.Qprev.loc[(self.scenar,date),self._prev],
                    unit=self.unit[self.QH])
                ))
        #cas plage de Qprev avec incertitude:
        #affichage date + scenario + q90 + Qprev + q10
        else:
            self.textCursorQ.set_text(trim(
                u"""{}
                    scénario {}
                    q90: {:.2f} {unit}
                    {}prev: {:.2f} {unit}
                    q10 {:.2f} {unit}"""
                .format(
                    date.strftime("%d/%m/%y %Hh%M"),
                    str(self.scenar),
                    self.Qprev.loc[(self.scenar,date),self._90],
                    self.QH,
                    self.Qprev.loc[(self.scenar,date),self._prev],
                    self.Qprev.loc[(self.scenar,date),self._10],
                    unit=self.unit[self.QH])
                ))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    widget = GrapheWidget(GrapheGRP)
    widget.show()
    sys.exit(app.exec_())