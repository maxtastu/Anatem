# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 11:42:45 2019

@author: spc.sacn
"""

from PyQt4 import QtGui, QtCore
from datetime import datetime as dt
from functools import partial
import itertools
import pandas as pd
import numpy as np

class TabDF(QtGui.QTableWidget):
    u"""classe de tableau conçu pour être rempli avec un DataFrame à simple idx

    Paramètres :     
        - checkCol, bool default False
          si True, ajoute une 1ère colonne de TabCheckBoxes au tableau,
          rattachées à l'index du data0 courant
        - colWidth, default None. Accepte int.
        si int, toutes les colonnes prennent la largeur colWidth
        si None, les colonnes sont redimensionnées suivant le contenu.
    
    """
    def __init__(self, parent=None, checkCol=False, colWidth=None):
        QtGui.QTableWidget.__init__(self, parent)

        self.checkCol = checkCol
        self.colWidth = colWidth
        self.setAlternatingRowColors(True)                
        self.itemChanged.connect(self.editDF)

    def newDF(self, 
              data, 
              rowHeader=None, 
              colHeader=None,
              fillna=u""):
        u"""efface le contenu du tableau et le remplace par data
        
        paramètres :
            - data : DataFrame pandas à simple index
            - rowHeader, default None
            titres de lignes à afficher (liste ou dictionnaire)
            si None, affiche les index de lignes de data
            - colHeader, default None
            titres de colonnes à afficher (liste ou dictionnaire)
            si None, affiche les index de colonnes de data
            - fillna, default u""
            valeur de remplacement des NaN
        
        """
        self.data0 = data
        self.data = self.data0
        
        self.construction = True
        
        #ràz contenu et dimensions du tableau
        self.clear()
        shp = self.data0.shape
        self.setRowCount(shp[0])
        self.setColumnCount(shp[1] + self.checkCol)
        
        #remplissage tableau
        #(supporterait d'être optimisé en considérant un type par colonne)
        for (row, col) in itertools.product(range(shp[0]),range(shp[1])):
            value = self.data0.iloc[row,col]
            #gestion type de donnée
            #date
            if type(value) == pd.Timestamp:
                value = dt.strftime(value.to_pydatetime(), "%d/%m/%Y %H:%M")
                item = QtGui.QTableWidgetItem(value)
            #str
            elif type(value) == str or type(value) == unicode :
                pass
            #nan
            elif np.isnan(value):
                value = fillna
            #float
            elif type(value) == float or type(value) == np.float64:
                value = "{:.2f}".format(value)          
            #cas général
            else:
                value = str(value)
            item = QtGui.QTableWidgetItem(value)           
            self.setItem(row, col+self.checkCol, item)
        
        #étiquettes de lignes et de colonnes
        if type(rowHeader) == list:
            self.rowHeader = rowHeader
        elif type(rowHeader) == dict:
            self.rowHeader = [rowHeader[row] for row in self.data0.index]
        elif rowHeader==None:
            self.rowHeader = [str(row) for row in self.data0.index]
            
        if type(colHeader) == list:
            self.colHeader = colHeader
        elif type(colHeader) == dict:
            self.colHeader = [colHeader[col] for col in list(self.data0)]
        elif colHeader==None:
            self.colHeader = [str(col) for col in list(self.data0)]
        if self.checkCol:
            self.colHeader = ["Voir"] + self.colHeader
        
        #si checkCol, construction des checkBoxes dans la 1ère colonne
        if self.checkCol:
            self.tabCheckBoxes = {}
            for (row,idx) in enumerate(self.data0.index):
                item = TabCheckBox(idx)
                self.setCellWidget(row,0,item)
                self.tabCheckBoxes[idx] = item
            
        self.setHorizontalHeaderLabels(self.colHeader)
        self.setVerticalHeaderLabels(self.rowHeader)

        #dimensionnement du tableau
        self.resizeRowsToContents()        
        if self.colWidth is not None:
            for col in range(shp[1]):
                self.setColumnWidth(col, self.colWidth)
        else:
            self.resizeColumnsToContents()           

        self.construction = False
        
        
    def editDF(self, item, typ=float):
        u"""remplace la valeur du DataFrame self.data sur l'élément en cours
        
        slot associé au signal itemChanged
        
        Arguments :
            - item QTableWidgetItem modifié
            - typ, défaut float. type de la donnée
        (TODO voir à intégrer ceci comme donnée du widget directement)
        
        """

        #évite déclenchements pendant le remplissage du tableau
        if self.construction == True:
            return

        row = item.row()
        col = item.column() - self.checkCol
        value = item.data(0)
        if type(value) == QtCore.QVariant: 
            value = unicode(value.toString())
        if value == "": #cas valeur effacée
            value = 0
        else:
            value = typ(value)
        
        self.data.iat[row, col] = value

    def height(self):
        u"""retourne hauteur du tableau
        
        """
        
        height = self.horizontalHeader().height()  \
                 + self.verticalHeader().length()  \
                 + self.frameWidth()*2        
        return height

    def width(self):
        u"""retourne largeur du tableau
        
        """

        width = self.verticalHeader().width()      \
                + self.horizontalHeader().length() \
                + self.frameWidth()*2
        #TODO
        #verticalHeader().width() ne donne pas la valeur attendue
        #bug de Qt : https://stackoverflow.com/questions/8766633
        #answered Aug 4 '16 at 15:24
        #voir à contourner ce bug ou à changer de version de Qt        
                     
        return width
        
        
class TabCheckBox(QtGui.QCheckBox):
    u"""classe de CheckBox à insérer dans une colonne de TabWidget.
    signal stateChanged surchargé en stateChanged_ pour passer self.idx
    
    """
    
    stateChanged_ = QtCore.pyqtSignal(bool, int)
    
    def __init__(self, idx, parent=None):
        QtGui.QCheckBox.__init__(self, parent)
        self.idx = idx
        
        super(TabCheckBox, self).stateChanged.connect(self.on_stateChanged)
        #pour centrer le bouton dans la colonne
        self.setStyleSheet("margin-left:50%; margin-right:50%;")

    def on_stateChanged(self):
        self.stateChanged_.emit(self.isChecked(), self.idx)
        

if __name__ == "__main__":
    import sys
    
    df = pd.DataFrame.from_dict({"A":[1,2,3],
                                 "B":[4,5,6],
                                 "C":[7,9,9]})
    
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    form = TabDF(checkCol=False, colWidth=70)
    form.setAttribute(QtCore.Qt.WA_DeleteOnClose)
#    form.newDF(df,
#               colHeader=[u"AH",u"Béh", u"Céh"], #list
#               colHeader={"A":u"zéro","B":u"un","C":u"deux"}, #dict
#               rowHeader={0:u"zéro",1:u"un",2:u"deux"}, #dict
#               )
    from global_ import *
    nomStation = {}
    for station in STATIONS.index:
        nomStation_ = u"{} - {}".format(
                STATIONS.loc[station,'troncon'].upper(),
                STATIONS.loc[station,'nom']
                )
        affluent = STATIONS.loc[station,'affluent']
        if type(affluent) == unicode:
            nomStation_ += u" ({})".format(affluent)
        nomStation[station] = nomStation_
    form.newDF(
                data=pd.DataFrame(
                        index=STATIONS.index,
                        data={sc:"GRP" for sc in ["RR3","MoyMin","MoyMoy","MoyMax"]}),
                rowHeader=nomStation
                )    
    form.resize(form.width(),form.height())
    form.show()
    sys.exit(app.exec_())