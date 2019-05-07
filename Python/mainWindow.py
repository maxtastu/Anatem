# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainWindow.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

u"""construction de la fenêtre principale

"""
import sys
from PyQt4 import QtCore, QtGui

from global_ import *
from widget_graphe import GrapheWidget, GrapheGRP, GraphePhoeniks, GrapheANA
from widget_tab_sc_manuels import FormScManuels
from widget_form_PHO_ANA import FormPHO, FormANA

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_mainWindow(object):
    u"""ui de la fenêtre principale
    
    """
    def setupUi(self, mainWindow):
        u"""construction de l'ui
        
        """
        mainWindow.setObjectName(_fromUtf8("mainWindow"))
        mainWindow.resize(1200, 850)
        self.stations = ["Vire","Eure"]

        #widget central
        self.centralwidget = QtGui.QWidget(mainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.centralLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.centralLayout.setObjectName(_fromUtf8("centralLayout"))

        #panneau lateral
        self.panneauStatus = QtGui.QPlainTextEdit(self.centralwidget)
        self.panneauStatus.setReadOnly(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.panneauStatus.sizePolicy().hasHeightForWidth())
        self.panneauStatus.setSizePolicy(sizePolicy)
        self.panneauStatus.setMinimumSize(QtCore.QSize(250, 0))
        self.panneauStatus.setObjectName(_fromUtf8("panneauStatus"))
        self.centralLayout.addWidget(self.panneauStatus)

        #widget vue principal (stackedWidget)
        self.mainView = QtGui.QStackedWidget(self.centralwidget)
        self.mainView.setObjectName(_fromUtf8("mainView"))

        #page 0 : pageOuverture
        self.pageOuverture = QtGui.QWidget()
        self.pageOuverture.setObjectName(_fromUtf8("pageOuverture"))
        self.mainView.addWidget(self.pageOuverture)

        #page 1 : pageAcquisStations vue sélection des stations
        self.pageAcquisStations = QtGui.QWidget()
        self.pageAcquisStations.setObjectName(_fromUtf8("pageAcquisStations"))
        self.layoutAcquisStations = QtGui.QGridLayout(self.pageAcquisStations)
        self.layoutAcquisStations.setObjectName(_fromUtf8("layoutAcquisStations"))

        self.btnValiderAcquisStations = QtGui.QPushButton(self.pageAcquisStations)
        self.btnValiderAcquisStations.setObjectName(_fromUtf8("btnValiderAcquisStations"))
        self.layoutAcquisStations.addWidget(self.btnValiderAcquisStations, 2, 0, 1, 1, QtCore.Qt.AlignLeft)

        boldFont = QtGui.QFont()
        boldFont.setBold(True)
        boldFont.setWeight(75)

        self.labelAcquisStations = QtGui.QLabel(self.pageAcquisStations)
        self.labelAcquisStations.setFont(boldFont)
        self.labelAcquisStations.setObjectName(_fromUtf8("labelAcquisStations"))
        self.layoutAcquisStations.addWidget(self.labelAcquisStations, 0, 0, 1, 1, QtCore.Qt.AlignLeft)

        self.listAcquisStations = QtGui.QListWidget(self.pageAcquisStations)
        self.listAcquisStations.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.listAcquisStations.setObjectName(_fromUtf8("listAcquisStations"))
        self.layoutAcquisStations.addWidget(self.listAcquisStations, 1, 0, 1, 1)

        self.frameAcquisStations = QtGui.QFrame(self.pageAcquisStations)
        self.frameAcquisStations.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frameAcquisStations.setFrameShadow(QtGui.QFrame.Raised)
        self.frameAcquisStations.setObjectName(_fromUtf8("frameAcquisStations"))
        self.layoutFrameAcquisStations = QtGui.QVBoxLayout(self.frameAcquisStations)
        self.layoutFrameAcquisStations.setObjectName(_fromUtf8("layoutFrameAcquisStations"))

        self.checkBoxAll = QtGui.QCheckBox(self.frameAcquisStations)
        self.checkBoxAll.setObjectName(_fromUtf8("checkBoxAll"))
        self.layoutFrameAcquisStations.addWidget(self.checkBoxAll, QtCore.Qt.AlignTop)

        self.checkBoxNone = QtGui.QCheckBox(self.frameAcquisStations)
        self.checkBoxNone.setObjectName(_fromUtf8("checkBoxNone"))
        self.layoutFrameAcquisStations.addWidget(self.checkBoxNone, QtCore.Qt.AlignTop)

        vSpacer0 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.layoutFrameAcquisStations.addItem(vSpacer0)

        self.checkBoxStation = {}
        for troncon in STATIONS['troncon'].unique():
            self.checkBoxStation[troncon] = QtGui.QCheckBox(self.frameAcquisStations)
            self.checkBoxStation[troncon].setText((troncon))
            self.layoutFrameAcquisStations.addWidget(self.checkBoxStation[troncon])
  
        vSpacer1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.layoutFrameAcquisStations.addItem(vSpacer1)

        self.labelDepth = QtGui.QLabel(self.frameAcquisStations)
        self.labelDepth.setFont(boldFont)
        self.labelDepth.setText(u"Profondeur des données \nobservées :")
        self.layoutFrameAcquisStations.addWidget(self.labelDepth, alignment=QtCore.Qt.AlignBottom)

        self.layoutDepthEdit = QtGui.QHBoxLayout()        
        
        self.depthEdit = QtGui.QSpinBox(self.frameAcquisStations)
        self.depthEdit.setValue(48)
        self.depthEdit.setMinimum(1)
        self.depthEdit.setMaximum(10000)
        self.layoutDepthEdit.addWidget(self.depthEdit, alignment=QtCore.Qt.AlignLeft)
        
        self.labelDepthEdit = QtGui.QLabel(self.frameAcquisStations)
        self.labelDepthEdit.setText(u"heures")
        self.layoutDepthEdit.addWidget(self.labelDepthEdit, alignment=QtCore.Qt.AlignLeft)

        self.layoutFrameAcquisStations.addLayout(self.layoutDepthEdit)

        self.layoutAcquisStations.addWidget(self.frameAcquisStations, 1, 1, 1, 1, QtCore.Qt.AlignTop)
        self.mainView.addWidget(self.pageAcquisStations)

        #page 2 : pageAcquisScenarios vue sélection des scénarios de pluie
        self.pageAcquisScenarios = QtGui.QWidget()
        self.pageAcquisScenarios.setObjectName(_fromUtf8("pageAcquisScenarios"))
        self.layoutAcquisScenarios = QtGui.QGridLayout(self.pageAcquisScenarios)
        self.layoutAcquisScenarios.setObjectName(_fromUtf8("layoutAcquisScenarios"))
        #bouton valider
        self.btnValiderAcquisScenarios = QtGui.QPushButton(self.pageAcquisScenarios)
        self.btnValiderAcquisScenarios.setObjectName(_fromUtf8("btnValiderAcquisScenarios"))
        self.layoutAcquisScenarios.addWidget(self.btnValiderAcquisScenarios, 2, 0, 1, 1, QtCore.Qt.AlignLeft)

        #tableau des scénarios manuels
        self.formScManuels = FormScManuels(self.pageAcquisScenarios)
        self.layoutAcquisScenarios.addWidget(self.formScManuels, 0, 0, 1, 1)

        self.mainView.addWidget(self.pageAcquisScenarios)


        #page 3 : pageResults vue des résultats, un onglet / modèle
        self.pageResults = QtGui.QWidget()
        self.pageResults.setObjectName(_fromUtf8("pageResults"))
        self.layoutResults = QtGui.QVBoxLayout(self.pageResults)
        self.layoutResults.setObjectName(_fromUtf8("layoutResults"))

        self.frameSelectResults = QtGui.QFrame(self.pageResults)
        self.layoutSelectResults = QtGui.QGridLayout(self.frameSelectResults)
        self.layoutResults.addWidget(self.frameSelectResults)

        self.comboBoxStations = QtGui.QComboBox(self.frameSelectResults)
        self.comboBoxStations.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.comboBoxStations.setObjectName(_fromUtf8("comboBoxStations"))
        self.layoutSelectResults.addWidget(self.comboBoxStations, 1,0, QtCore.Qt.AlignLeft)
        self.labelStations = QtGui.QLabel(self.frameSelectResults)
        self.labelStations.setObjectName(_fromUtf8("labelStations"))
        self.labelStations.setText(_fromUtf8("Station :"))
        self.layoutSelectResults.addWidget(self.labelStations, 0,0, QtCore.Qt.AlignLeft)

        self.comboBoxScenarios = QtGui.QComboBox(self.frameSelectResults)
        self.comboBoxScenarios.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.comboBoxScenarios.setObjectName(_fromUtf8("comboBoxScenarios"))
        self.layoutSelectResults.addWidget(self.comboBoxScenarios, 1,1, QtCore.Qt.AlignLeft)
        self.labelScenarios = QtGui.QLabel(self.frameSelectResults)
        self.labelScenarios.setObjectName(_fromUtf8("labelStations"))
        self.labelScenarios.setText(_fromUtf8(u"Scénario de pluie :"))
        self.layoutSelectResults.addWidget(self.labelScenarios, 0,1, QtCore.Qt.AlignLeft)

        self.btnQ = QtGui.QRadioButton(self.frameSelectResults)
        self.btnQ.setText(u"Débit")
        self.btnQ.setChecked(True)
        self.layoutSelectResults.addWidget(self.btnQ,0, 2, alignment=QtCore.Qt.AlignLeft)
        self.btnH = QtGui.QRadioButton(self.frameSelectResults)
        self.btnH.setText(u"Hauteur")
        self.layoutSelectResults.addWidget(self.btnH,1, 2, alignment=QtCore.Qt.AlignLeft)
        self.btnsQH = QtGui.QButtonGroup(self.frameSelectResults)
        self.btnsQH.addButton(self.btnQ,0)
        self.btnsQH.addButton(self.btnH,1)
        self.grandeurs = {0: "Q",
                          1: "H"}

        self.tabWidget = QtGui.QTabWidget(self.pageResults)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))

        self.tabGRP = QtGui.QWidget()
        self.tabGRP.setObjectName(_fromUtf8("tabGRP"))
        self.tabWidget.addTab(self.tabGRP, _fromUtf8(""))

        self.tabPHO = QtGui.QWidget()
        self.tabPHO.setObjectName(_fromUtf8("tabPHO"))
        self.tabWidget.addTab(self.tabPHO, _fromUtf8(""))

        self.tabANA = QtGui.QWidget()
        self.tabANA.setObjectName(_fromUtf8("tabANA"))
        self.tabWidget.addTab(self.tabANA, _fromUtf8(""))

        self.layoutResults.addWidget(self.tabWidget)
        self.mainView.addWidget(self.pageResults)

        self.centralLayout.addWidget(self.mainView)
        mainWindow.setCentralWidget(self.centralwidget)

        #tabGRP vue des resultats de GRP
        self.stackGRP = QtGui.QStackedWidget(self.tabGRP)
        self.layoutTabGRP = QtGui.QVBoxLayout(self.tabGRP)
        self.layoutTabGRP.addWidget(self.stackGRP)
        #vue0 : bouton lancement de GRP
        self.vueLancementGRP = QtGui.QWidget()
        self.layoutLancementGRP = QtGui.QVBoxLayout(self.vueLancementGRP)
        self.btnGRP = QtGui.QPushButton(self.vueLancementGRP)
        self.btnGRP.setText(u"Calcul GRP")
        self.layoutLancementGRP.addWidget(self.btnGRP, alignment=QtCore.Qt.AlignLeft)
        self.stackGRP.addWidget(self.vueLancementGRP)    
        #vue1 : résultats de GRP
        self.vueResultsGRP = QtGui.QWidget()
        self.layoutResultsGRP = QtGui.QVBoxLayout(self.vueResultsGRP)
        self.grapheGRP = GrapheWidget(parent=self.vueResultsGRP,classGraphe=GrapheGRP)
        self.layoutResultsGRP.addWidget(self.grapheGRP)        
        self.btnPdf = QtGui.QPushButton(self.grapheGRP.frameToolbar)
        self.btnPdf.setText(u"Voir Fiche Contrôle")
        self.grapheGRP.layoutToolbar.addWidget(self.btnPdf,alignment=QtCore.Qt.AlignRight)

        self.stackGRP.addWidget(self.vueResultsGRP)
  
        #tabPHO vue des resultats de Phoeniks
        self.layoutPHO = QtGui.QVBoxLayout(self.tabPHO)
        self.splitterPHO = QtGui.QSplitter(QtCore.Qt.Vertical)
      
        self.graphePHO = GrapheWidget(
                parent=self.tabPHO,
                classGraphe=GraphePhoeniks
                )
        self.linePHO = QtGui.QFrame(self.tabPHO) #ligne verticale au-dessus du cadre
        self.linePHO.setFixedHeight(1)
        self.linePHO.setFrameShape(QtGui.QFrame.StyledPanel) 
        
        self.formPHO = FormPHO(self.graphePHO)
        
        self.splitterPHO.addWidget(self.graphePHO)
        self.splitterPHO.addWidget(self.linePHO)
        self.splitterPHO.addWidget(self.formPHO)
        self.splitterPHO.setHandleWidth(1)
        self.splitterPHO.setStretchFactor(0,5)
        self.splitterPHO.setStretchFactor(1,1)
        self.splitterPHO.setStretchFactor(2,1)
        self.splitterPHO.setCollapsible(0,False)
        self.splitterPHO.setCollapsible(1,False)
        
        #ajout des radioboutons de choix de config : 1 stackedlayout / station
        self.configsPHO = QtGui.QStackedWidget(self.formPHO)
        self.formPHO.verticalLayout.addWidget(self.configsPHO)
        self.configPHO = {} #dictionnaire des stackedwidgets avec configs
        self.btnsPHO = {}   #dict des buttonGroups
        self.layoutConfigPHO = {}  #dict des layouts
        self.idxConfigPHO = {}
        for (i, station) in enumerate(PHOENIKS.stations.unique()):
            self.configPHO[station] = QtGui.QFrame()
            self.layoutConfigPHO[station] = QtGui.QVBoxLayout(self.configPHO[station])
            self.btnsPHO[station]   = QtGui.QButtonGroup(self.configPHO[station])
            self.configsPHO.addWidget(self.configPHO[station])
            self.idxConfigPHO[station] = i
        for idx in PHOENIKS.index:
            station = PHOENIKS.at[idx,"stations"]
            btn = QtGui.QRadioButton(self.configPHO[station])
            btn.setText(PHOENIKS.loc[idx, "nom_modele"])
            self.btnsPHO[station].addButton(btn, idx)
            self.layoutConfigPHO[station].addWidget(btn)
            btn.setSizePolicy(QtGui.QSizePolicy(
                QtGui.QSizePolicy.Minimum, 
                QtGui.QSizePolicy.Minimum)
                )
        self.layoutPHO.addWidget(self.splitterPHO)
            
        #tabANA vue des Analog
        self.layoutANA = QtGui.QVBoxLayout(self.tabANA)
        self.splitterANA = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.grapheANA = GrapheWidget(parent=self.tabANA,classGraphe=GrapheANA)
        #ligne verticale au-dessus du cadre
        self.lineANA = QtGui.QFrame(self.tabANA)
        self.lineANA.setFixedHeight(1)
        self.lineANA.setFrameShape(QtGui.QFrame.StyledPanel)        
        
        self.formANA = FormANA(self.grapheANA)
        
        self.splitterANA.addWidget(self.grapheANA)        
        self.splitterANA.addWidget(self.lineANA)
        self.splitterANA.addWidget(self.formANA)
        self.splitterANA.setHandleWidth(1)
        self.splitterANA.setStretchFactor(0,5)
        self.splitterANA.setStretchFactor(1,1)
        self.splitterANA.setStretchFactor(2,1)
        self.splitterANA.setCollapsible(0,False)
        self.splitterANA.setCollapsible(1,False)
        self.layoutANA.addWidget(self.splitterANA)
            
        #barre de menu
        self.menubar = QtGui.QMenuBar(mainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1200, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFichier = QtGui.QMenu(self.menubar)
        self.menuFichier.setObjectName(_fromUtf8("menuFichier"))
        mainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(mainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        mainWindow.setStatusBar(self.statusbar)
        self.actionNouveau_lancement = QtGui.QAction(mainWindow)
        self.actionNouveau_lancement.setObjectName(_fromUtf8("actionNouveau_lancement"))
        self.actionCharger = QtGui.QAction(mainWindow)
        self.actionCharger.setObjectName(_fromUtf8("actionCharger"))
        self.actionSauvegarder = QtGui.QAction(mainWindow)
        self.actionSauvegarder.setEnabled(False)
        self.actionSauvegarder.setObjectName(_fromUtf8("actionSauvegarder"))
        self.actionExport = QtGui.QAction(mainWindow)
        self.actionQuitter = QtGui.QAction(mainWindow)
        self.actionQuitter.setObjectName(_fromUtf8("actionQuitter"))
        self.menuFichier.addAction(self.actionNouveau_lancement)
        self.menuFichier.addAction(self.actionCharger)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.actionSauvegarder)
        self.menuFichier.addAction(self.actionExport)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.actionQuitter)
        self.menubar.addAction(self.menuFichier.menuAction())
        self.labelAcquisStations.setBuddy(self.listAcquisStations)

        self.retranslateUi(mainWindow)
        self.mainView.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

        self.mainWindow = mainWindow
        self.actionQuitter.triggered.connect(self.close_app)


    def close_app(self):
        choice = QtGui.QMessageBox.question(self.mainWindow,'',
                    'Voulez-vous vraiment quitter ?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            sys.exit()
        else:
            pass

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(_translate("mainWindow", "mainWindow", None))
        self.btnValiderAcquisStations.setText(_translate("mainWindow", "Valider", None))
        self.btnValiderAcquisScenarios.setText(_translate("mainWindow", "Valider", None))
        self.labelAcquisStations.setText(_translate("mainWindow", "Sélection des stations :", None))
        self.checkBoxAll.setText(_translate("mainWindow", "Tout sélectionner", None))
        self.checkBoxNone.setText(_translate("mainWindow", "Tout déselectionner", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabGRP), _translate("mainWindow", "GRP", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabPHO), _translate("mainWindow", "Phoeniks", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabANA), _translate("mainWindow", "Analog", None))
        self.menuFichier.setTitle(_translate("mainWindow", "Fichier", None))
        self.actionNouveau_lancement.setText(_translate("mainWindow", "Nouveau run", None))
        self.actionCharger.setText(_translate("mainWindow", "Charger", None))
        self.actionSauvegarder.setText(_translate("mainWindow", "Sauvegarder", None))
        self.actionExport.setText(_translate("mainWindow", "Exporter", None))
        self.actionQuitter.setText(_translate("mainWindow", "Quitter", None))

        self.actionNouveau_lancement.setShortcut(_translate("mainWindow", "Ctrl+N", None))
        self.actionCharger.setShortcut(_translate("mainWindow", "Ctrl+O", None))
        self.actionSauvegarder.setShortcut(_translate("mainWindow", "Ctrl+S", None))
        self.actionExport.setShortcut(_translate("mainWindow", "Ctrl+E", None))
        self.actionQuitter.setShortcut(_translate("mainWindow", "Ctrl+Q", None))

class StationListWidgetItem(QtGui.QListWidgetItem):
    def __init__(self, _type=0, parent=None, code='code_item'):
        QtGui.QWidgetItem.__init__(self, parent, _type)
        self.code = code
        #que fait le type ? à chercher

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    mainWindow = QtGui.QMainWindow()
    mainWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec_())