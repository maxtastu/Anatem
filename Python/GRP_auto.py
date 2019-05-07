# -*- coding: utf-8 -*-
"""
Created on Mon Feb  4 16:01:17 2019

@author: m.tastu

gestion du run automatique quotidien de GRP
"""

import os
import socket
import smtplib
import io
import shutil
import pandas as pd
import pendulum.duration as td
from  datetime import datetime as dt
from scipy.interpolate import interp1d
from email.MIMEText import MIMEText
from ConfigParser import ConfigParser
from string import Template

import Pilote_Modeles
from global_ import *

def run_GRP_auto(t_lacune):
    u"""lance GRP sur toutes les stations et sauvegarde le run.
    Supprime les sauvegardes de runs automatiques anciennes
    Récupère les éléments à faire figurer dans le rapport envoyé par mail.
    
    Paramètres :
        - t_lacune format pendulum.duration
        profondeur à partir de la quelle mettre en évidence 
        les lacunes de Q et P (formattage dans rapport HTML)
    
    Sorties :
        - dicoRapportPlain éléments du rapport format plaintext
        - dicoRapportHTML  éléments du rapport format HTML
        - run.dossierSave  dossier de sauvegarde (pour enregistrer rapport)
    
    """

    #lancement modèle
    stations = STATIONS.index
    profondeur = td(hours=48)
    t_lancement = dt.utcnow()

    #formatage des éléments importants
    achtung = " color: #ff0000; font-weight:bold" #rouge + gras
    achtungStyle = """ style = "{}" """.format(achtung)
    
    #lancement de GRP et sauvegarde
    run = Pilote_Modeles.RunModeles(
            TR=True,
            rejeu=False,
            )
    run.acquis(stations, profondeur=profondeur)
    run.lance_traitement_donnees_entree(Pmanu=None)
    run.pilote_GRP()
    run.sauvegarde(saveMode="A")
    
    #suppression des sauvegardes de runs auto anciennes (+ de 30 jours)
    oldSaves = [save for save in os.listdir(SAVEDIR)
            #vérif save automatique  
            if save[-4]=="A"
            #vérif ancienneté
            and run.t_prev - dt.strptime(save[:10], "%Y_%m_%d") > td(days=30)
             ]
    for save in oldSaves:
        try:
            shutil.rmtree(os.path.join("Sauvegardes",save))
        except:
            pass


    #récupération heure dernier Q obs pour chaque station
    qobs = run.Qobs.reset_index()
    qobs.set_index("station", inplace=True)
    Qlast = pd.DataFrame(
            index=run.stationsGRP,
            data={"Heure (TU)":[qobs.loc[station, "date"].max()
                          for station in run.stationsGRP]} 
            )
    Qlast.rename(index=NOMS, inplace=True)
    Qlast.sort_values("Heure (TU)", inplace=True)   

    #mise en évidence lacune éventuelle de Q
    def highlight_lacunes_Q(s):
        t = s.loc["Heure (TU)"]
        return [achtung] if run.t_prev-t >= t_lacune else [""]        
    Qstyle = Qlast.style.apply(highlight_lacunes_Q, axis=1)  \
           .format(lambda d: d.strftime("%d/%m/%Y %H:%M"))

    
    #Pobs : récupération une seule date
    #sauf anomalie même date pour toutes les pluies, ici je prends le min
    pobs = run.Pobs.reset_index()
    pobs.set_index("station", inplace=True)
    PLast = min([pobs.loc[station, "date"].max() 
                          for station in run.stationsGRP])

    #dates de production des données de pluie prévue ou échec éventuel
    bilanBP, bilanRR3 = {}, {}
    if run.echecBP == False:
        bilanBP["txt" ] = trim(
        u"""Heure de production des prévisions BP (TU) :
            {}""".format(
            "\n".join((k+":"+ v.strftime("%d/%m/%Y %H:%M")) 
                        for (k,v) in run.dtesBP.items()
                        )
            )
            )
        bilanBP["html"] = \
        u"""Heure de production des prévisions BP (TU) :<dd>{}""".format(
            "<dd>".join((k+":"+ v.strftime("%d/%m/%Y %H:%M")) 
                        for (k,v) in run.dtesBP.items()
                        )
            )
    else:
        bilanBP["txt" ] = u"échec de l'acquisition des prévisions BP."
        bilanBP["html"] = u"<dd>échec de l'acquisition des prévisions BP."
        
    if run.echecRR3 == False:
        bilanRR3["txt" ] = trim(
        u"""Heure de production des prévisions RR3 (TU) : 
            {}""".format(
                run.dteNetWorkRR3.strftime("%d/%m/%Y %H:%M")
                )
            )
        bilanRR3["html"] = \
        u"""Heure de production des prévisions RR3 (TU) : <dd>{}""".format(
                run.dteNetWorkRR3.strftime("%d/%m/%Y %H:%M")
                )
    else:
        bilanRR3["txt" ] = u"échec de l'acquisition des prévisions RR3."
        bilanRR3["html"] = u"<dd>échec de l'acquisition des prévisions RR3."
    
    #détection niveaux de vigilance
    if run.echecCT == True:
        warningCT = trim(
            u"""La base support des courbes de tarage n'a pas pu être lue.
            Sans conversion des sorties de GRP en hauteur, la lecture des
            niveaux de vigilance est impossible.
                         """)
    else:
        #choix du scénario de pluie à tester. MoyMax sauf échec acquisition.
        if run.echecBP == False:
            scenar = "MoyMax"
        elif run.echecRR3 == False:
            scenar = "RR3"
        else:
            scenar = "Pluie_nulle"
        #vigiPrev : série avec en index les stations avec niveau de vigilance,
        #en valeur les hauteurs max prévues
        vigiPrev = run.GRPprev.loc[
                (run.nivVigi.index.get_level_values("station").unique(),
                 scenar,
                 slice(None)
                 ),
                "Hprev"
                ].unstack(level=0).max().to_frame("Hmax")
        #vigiH : DF avec en index les stations avec niveau de vigilance,
        #en colonnes les niveaux de vigilance, valeurs en hauteur
        vigiH = run.nivVigi["H"].unstack(level=1)
        strNiveaux = {
                "V" : u"Vert",
                "JB": u"Transition vert-jaune",
                "JH": u"Jaune",
                "OB": u"Transition jaune-orange",
                "OH": u"Orange",
                "RB": u"Transition orange-rouge",
                "RH": u"Rouge"
                }
        vigiH.rename(columns=strNiveaux, inplace=True)
        niveaux = {}
        f = {}
        for station in vigiPrev.index:
            #dictionnaire clés : h des nv à la station, valeurs : intitulé 
            niveaux[station] = {v:k for (k,v) in 
                                vigiH.loc[station].to_dict().items()
                                }
            niveaux[station][0] = strNiveaux["V"]
            #fonction créneau
            f[station] = interp1d(
                    niveaux[station].keys(), 
                    niveaux[station].keys(),
                    kind="previous",
                    bounds_error=False,
                    fill_value="extrapolate"
                    )
        
        vigiPrev["Vigilance"] = vigiPrev.apply(
            lambda row: niveaux[station][float(f[row.name](row.loc["Hmax"]))],
            axis=1,
            )
        vigiPrev.rename(index=NOMS, inplace=True)
        vigiPrev.index.name = None #pour ne pas afficher le nom dans le mail

        #mise en évidence niveau de vigilance prévu        
        vigiStyle = vigiPrev.Vigilance.to_frame() \
                    .style.apply(highlight_vigilance)
        

    #construction du dictionnaire pour compléter template de rapport
    #éléments communs format plaintext et html
    dicoRapportCommun = dict(
            t_lancement   = t_lancement.strftime("%d/%m/%Y %H:%M (TU)"),
            t_prev        = run.t_prev.strftime("%d/%m/%Y %H:%M (TU)"),
            profondeur    = profondeur.in_hours(),
            nb_stationsGRP= len(run.stationsGRP),
            datePlast     = PLast.strftime("%d/%m/%Y %H:%M (TU)"),
            scenar        = scenar,
            dossierSave   = os.path.join(os.getcwd(), run.dossierSave),
            )
    #éléments spécifiques au format PlainText
    dicoRapportPlain = dict(
        nb_lacunesQ   = len(run.lacunesQ),               
        lacunesQ      = ";".join(run.lacunesQ),
        tabQlast      = Qlast.to_string(
                        formatters=[lambda d: d.strftime("%d/%m/%Y %H:%M")]),
        scenarios     = ";".join(run.scenarios),
        bilanBP       = bilanBP["txt"],
        bilanRR3      = bilanRR3["txt"],
        tabVigilance  = vigiPrev.to_string() if not run.echecCT else warningCT,
        )
    dicoRapportPlain.update(dicoRapportCommun)

    #éléments spécifiques au format HTML
    dicoRapportHTML = dict(
        nb_lacunesQ   =     ("<b>"  if len(run.lacunesQ)>0 else "")   
                          + str(len(run.lacunesQ))   #gras si lacunes                 
                          + ("</b>" if len(run.lacunesQ)>0 else ""),
        achtung       = achtungStyle,
        lacunesQ      = "<dd>".join([NOMS[station]
                                    for station in run.lacunesQ]),
        tabQlast      = Qstyle.render(),
        formatPlast   = achtungStyle if run.t_prev-PLast >= t_lacune 
                        else "",
        scenarios     = "<dd>".join([""]+run.scenarios),
        bilanBP       = bilanBP["html"],
        bilanRR3      = bilanRR3["html"],
        tabVigilance  = vigiStyle.render() if not run.echecCT else warningCT,
        )
    dicoRapportHTML.update(dicoRapportCommun)
          
    return dicoRapportPlain, dicoRapportHTML, run.dossierSave

def envoi_mail(dicoRapportPlain, dicoRapportHTML, dossierSave):
    u"""enregistre le rapport en plaintext dans le dossier spécifié
    et envoie le rapport HTML par mail, si le PC est configuré pour.
    
    Paramètres :
        - dicoRapportPlain éléments pour compléter le template de rapport
        en plaintext,
        - dicoRapportHTML idem format HTML
        - dossierSave dossier où enregistrer le rapport
    
    """
    
    # rapport en plaintext pour sauvegarde locale
    #lecture du template plaintext
    with io.open(PYDIR+"GRP_auto_template_plaintext", 
                 "r", 
                 encoding="utf-8"
                 ) as f:
        templatePlain = Template(f.read())
    rapportPlain = templatePlain.substitute(dicoRapportPlain)
   #ajout du texte du mail dans le dossier de sauvegarde
    with open(os.path.join(dossierSave, "rapport_GRP_auto.txt"), 
              "w"
              ) as f:
        f.write(rapportPlain.encode("utf8"))
    
    #lecture configuration réseau pour vérifier si envoi de mail sur ce poste 
    config = ConfigParser()
    config.read(CONFIGDIR+'config.ini')
    poste = {}
    for Mx in ["M1","M2","M3"]:        
        poste[config.get("Reseau", Mx)] = Mx
    envoi = config.get("Reseau", "envoi").split(",")    
    ip = socket.gethostbyname(socket.gethostname())    

    if poste[ip] not in envoi:
        return

    #lecture du template HTML et construction du rapport HTML
    with io.open(PYDIR+"GRP_auto_template_html", 
                 "r", 
                 encoding="utf-8"
                 ) as f:
        templateHTML = Template(f.read())
    rapportHTML = templateHTML.substitute(dicoRapportHTML)
    
    #envoi du mail
    if poste[ip] in envoi:
        adresse = config.get("Reseau","mail")
        mail = MIMEText(rapportHTML, "html", _charset="utf-8")
        mail['From'] = adresse
        mail['Subject'] = u"[GRP {}] Rapport de run automatique".format(Mx)
        mail['To'] = adresse
        smtp = smtplib.SMTP('smtp.melanie2.i2',25)
        smtp.starttls()
        smtp.login(
                config.get("Reseau","username"),
                config.get("Reseau","pwd"))        
        smtp.sendmail(
                adresse,    #from
                [adresse],  #to
                mail.as_string())
        smtp.close()


def highlight_vigilance(s):
    u"""met en évidence les lignes du tableau des niveaux de vigilance
        si niveau > vert, gras + bgcolor suivant le niveau
    
    """
    bgcolors = {
            u"Transition vert-jaune" : "#ceff41",
            u"Jaune" :                 "#ffe966",
            u"Transition jaune-orange":"#ffb605",
            u"Orange" :                "#ffb605",
            u"Transition orange-rouge":"#ff4141",
            u"Rouge" :                 "#ff4141", 
                }
    return ["background-color: {}; font-weight:bold".format(bgcolors[niveau]) 
            if niveau in bgcolors else "" for niveau in s]


if __name__ == "__main__":
    (dicoRapportPlain, 
    dicoRapportHTML,  
    dossierSave) = run_GRP_auto(t_lacune=td(hours=18))
    mail = envoi_mail(dicoRapportPlain, dicoRapportHTML, dossierSave)
