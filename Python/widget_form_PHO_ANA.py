# -*- coding: utf-8 -*-
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from widget_tabDF import TabDF

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

class FormPHO(QtGui.QWidget):
    u"""classe de formulaire avec les paramètres de Phoeniks + tableau de
    résultats
    
    """
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        
        self.setObjectName(_fromUtf8("Form"))
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        fixed = QtGui.QSizePolicy(
                QtGui.QSizePolicy.Fixed, 
                QtGui.QSizePolicy.Fixed
                )

        #1ère colonne : paramètres
        self.gpBoxParams = QtGui.QGroupBox(self)
        self.gpBoxParams.setSizePolicy(fixed)
        self.gpBoxParams.setFixedHeight(107)
        self.gpBoxParams.setFixedWidth(212)
        self.gpBoxParams.setObjectName(_fromUtf8("gpBoxParams"))
        
        self.gridLayout = QtGui.QGridLayout(self.gpBoxParams)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        
        self.labelDeb = QtGui.QLabel(self.gpBoxParams)
        self.labelDeb.setObjectName(_fromUtf8("labelDeb"))
        self.gridLayout.addWidget(self.labelDeb, 0, 0, 1, 1)
        self.editDeb = QtGui.QDateTimeEdit(self.gpBoxParams)
        self.editDeb.setAlignment(QtCore.Qt.AlignCenter)
        self.editDeb.setObjectName(_fromUtf8("editDeb"))
        self.gridLayout.addWidget(self.editDeb, 0, 1, 1, 1)

        self.labelFin = QtGui.QLabel(self.gpBoxParams)
        self.labelFin.setObjectName(_fromUtf8("labelFin"))
        self.gridLayout.addWidget(self.labelFin, 1, 0, 1, 1)
        self.editFin = QtGui.QDateTimeEdit(self.gpBoxParams)
        self.editFin.setAlignment(QtCore.Qt.AlignCenter)
        self.editFin.setObjectName(_fromUtf8("editFin"))
        self.gridLayout.addWidget(self.editFin, 1, 1, 1, 1)

        self.labelCG = QtGui.QLabel(self.gpBoxParams)
        self.labelCG.setObjectName(_fromUtf8("labelCG"))
        self.labelCG.setFixedWidth(20)
        self.gridLayout.addWidget(self.labelCG, 0, 2, 2, 1)

        self.labelQ0 = QtGui.QLabel(self.gpBoxParams)
        self.labelQ0.setObjectName(_fromUtf8("labelQ0"))
        self.gridLayout.addWidget(self.labelQ0, 2, 0, 1, 1)        
        self.editQ0 = QtGui.QDoubleSpinBox(self.gpBoxParams)
        self.editQ0.setMaximum(1000)
        self.editQ0.setSuffix(u" m3/s")
        self.editQ0.setAlignment(QtCore.Qt.AlignCenter)
        self.editQ0.setObjectName(_fromUtf8("editQ0"))
        self.gridLayout.addWidget(self.editQ0, 2, 1, 1, 1)        
        
        self.horizontalLayout.addWidget(self.gpBoxParams)
                
        #2ème colonne : bouton lancement +choix de la config
        self.frameGo = QtGui.QFrame(self)
        self.frameGo.setSizePolicy(fixed)
        self.frameGo.setFixedHeight(107)
        self.frameGo.setFixedWidth(243)
        self.frameGo.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frameGo.setFrameShadow(QtGui.QFrame.Raised)
        self.frameGo.setObjectName(_fromUtf8("frameGo"))
        
        self.verticalLayout = QtGui.QVBoxLayout(self.frameGo)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        
        self.btnGo = QtGui.QPushButton(self.frameGo)
        self.btnGo.setObjectName(_fromUtf8("btnGo"))
        self.btnGo.setSizePolicy(fixed)
        self.verticalLayout.addWidget(self.btnGo, alignment=QtCore.Qt.AlignHCenter)

        self.vSpacer = QtGui.QSpacerItem(
                5, 5, 
                QtGui.QSizePolicy.Minimum, 
                QtGui.QSizePolicy.Expanding
                )
        self.horizontalLayout.addItem(self.vSpacer)
                
        self.btnGo.raise_()
        self.horizontalLayout.addWidget(self.frameGo)    
        
        #3ème colonne : tableau des résultats
        self.frameResults = QtGui.QFrame(self)
        self.layoutResults = QtGui.QVBoxLayout(self.frameResults)
        
        self.label_tMax = QtGui.QLabel(self.frameResults)
        self.label_tMax.setText(u"")
        self.layoutResults.addWidget(
                self.label_tMax, 
                alignment=QtCore.Qt.AlignLeft)
        
        self.table = TabDF(self.frameResults, colWidth=70)

        self.table.setObjectName(_fromUtf8("table"))
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.layoutResults.addWidget(self.table)
        
        self.horizontalLayout.addWidget(self.frameResults)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        self.setWindowTitle(_translate("Form", "Form", None))
        self.gpBoxParams.setTitle(_translate("Form", "Paramètres", None))
        self.labelDeb.setText(_translate("Form", "Début CG", None))
        self.editDeb.setDisplayFormat(_translate("Form", "dd/MM/yyyy HH:00", None))
        self.labelFin.setText(_translate("Form", "Fin CG", None))
        self.editFin.setDisplayFormat(_translate("Form", "dd/MM/yyyy HH:00", None))
        self.labelQ0.setText(_translate("Form", "Q0", None))
        self.labelCG.setText(_translate("Form", "0 h", None))
        self.btnGo.setText(_translate("Form", "Calculer", None))

    def sizeHint(self):
            return QtCore.QSize(768, 123) 

class FormANA(QtGui.QFrame):
    u"""classe de formulaire avec les paramètres d'Analog + tableau de
    résultats
    
    """
    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent)
        
        self.setObjectName(_fromUtf8("Form"))
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        fixed = QtGui.QSizePolicy(
                QtGui.QSizePolicy.Fixed, 
                QtGui.QSizePolicy.Fixed
                )

        #1ère colonne : paramètres
        self.gpBoxParams = QtGui.QGroupBox(self)
        self.gpBoxParams.setSizePolicy(fixed)
        self.gpBoxParams.setFixedWidth(212)
        self.gpBoxParams.setFixedHeight(107)
        self.gpBoxParams.setObjectName(_fromUtf8("gpBoxParams"))
        
        self.gridLayout = QtGui.QGridLayout(self.gpBoxParams)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        
        self.labelDeb = QtGui.QLabel(self.gpBoxParams)
        self.labelDeb.setObjectName(_fromUtf8("labelDeb"))
        self.gridLayout.addWidget(self.labelDeb, 0, 0, 1, 1)
        self.editDeb = QtGui.QDoubleSpinBox(self.gpBoxParams)
        self.editDeb.setMaximum(1000)
        self.editDeb.setSuffix(u" mm")
        self.editDeb.setAlignment(QtCore.Qt.AlignCenter)
        self.editDeb.setObjectName(_fromUtf8("editDeb"))
        self.gridLayout.addWidget(self.editDeb, 0, 1, 1, 1)

        self.labelFin = QtGui.QLabel(self.gpBoxParams)
        self.labelFin.setObjectName(_fromUtf8("labelFin"))
        self.gridLayout.addWidget(self.labelFin, 1, 0, 1, 1)
        self.editFin = QtGui.QDoubleSpinBox(self.gpBoxParams)
        self.editFin.setMaximum(1000)
        self.editFin.setSuffix(u" mm")
        self.editFin.setAlignment(QtCore.Qt.AlignCenter)
        self.editFin.setObjectName(_fromUtf8("editFin"))
        self.gridLayout.addWidget(self.editFin, 1, 1, 1, 1)

        self.labelQ0 = QtGui.QLabel(self.gpBoxParams)
        self.labelQ0.setObjectName(_fromUtf8("labelQ0"))
        self.gridLayout.addWidget(self.labelQ0, 2, 0, 1, 1)        
        self.editQ0 = QtGui.QDoubleSpinBox(self.gpBoxParams)
        self.editQ0.setMaximum(1000)
        self.editQ0.setSuffix(u" m3/s")
        self.editQ0.setAlignment(QtCore.Qt.AlignCenter)
        self.editQ0.setObjectName(_fromUtf8("editQ0"))
        self.gridLayout.addWidget(self.editQ0, 2, 1, 1, 1)        
        
        self.horizontalLayout.addWidget(self.gpBoxParams)
                
        #2ème colonne : bouton lancement +choix de la config
        self.frameGo = QtGui.QFrame(self)
        self.frameGo.setSizePolicy(fixed)
        self.frameGo.setFixedWidth(243)
        self.frameGo.setFixedHeight(107)
        self.frameGo.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frameGo.setFrameShadow(QtGui.QFrame.Raised)
        self.frameGo.setObjectName(_fromUtf8("frameGo"))
        
        self.verticalLayout = QtGui.QVBoxLayout(self.frameGo)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        
        self.btnGo = QtGui.QPushButton(self.frameGo)
        self.btnGo.setObjectName(_fromUtf8("btnGo"))
        self.btnGo.setSizePolicy(fixed)
        self.verticalLayout.addWidget(self.btnGo, alignment=QtCore.Qt.AlignHCenter)

        self.vSpacer = QtGui.QSpacerItem(
                5, 300, 
                QtGui.QSizePolicy.Minimum, 
                QtGui.QSizePolicy.Expanding
                )
        self.verticalLayout.addItem(self.vSpacer)
                
        self.horizontalLayout.addWidget(self.frameGo)    
        
        #3ème colonne : tableau des résultats
        self.table = TabDF(self, checkCol=True)
        self.table.setObjectName(_fromUtf8("table"))
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
#        self.table.setFixedSize(QtCore.QSize(500, 100))
        
        self.horizontalLayout.addWidget(self.table)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        self.setWindowTitle(_translate("Form", "Form", None))
        self.gpBoxParams.setTitle(_translate("Form", "Paramètres", None))
        self.labelDeb.setText(_translate("Form", "CG min", None))
        self.labelFin.setText(_translate("Form", "CG max", None))
        self.labelQ0.setText(_translate("Form", "Q0", None))
        self.btnGo.setText(_translate("Form", "Voir les Analogs", None))

    def sizeHint(self):
            return QtCore.QSize(768, 123) 


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    #ligne pour permettre d'ouvrir plusieurs fenêtres à la suite avec IPython :
    app.aboutToQuit.connect(app.deleteLater)
    formPHO = FormPHO()
#    formPHO.tabResults.setColumnCount(0)
#    formPHO.tabResults.setColumnCount(3)
#    formPHO.tabResults.setHorizontalHeaderLabels(["ga","zo","bu"])
#    df = pd.DataFrame.from_dict(data = {'col1':[1,2.123456,dt.utcnow()],
#                                        'col2':['4','5','6'],
#                                        'col3':['7','8','9']})
#    formPHO.tabResults.newDF(df,rowHeader=["ah","jej","bedum tss","!!!"])
#    formPHO.tabResults.newDF(pd.concat([df,df],axis=1))
#    formPHO.show()
    formANA = FormANA()
    formPHO.show()
    sys.exit(app.exec_())
