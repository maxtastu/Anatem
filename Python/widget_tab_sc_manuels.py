# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:/PGRP/widget_tab_sc_manuels.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from widget_tabDF import TabDF
from global_ import *

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

class Ui_FormScManuels(object):
    def setupUi(self, FormScManuels):
        FormScManuels.setObjectName(_fromUtf8("FormScManuels"))
        
        self.gridLayout = QtGui.QGridLayout(FormScManuels)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))

        self.labelTitre = QtGui.QLabel(FormScManuels)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.labelTitre.setFont(font)
        self.labelTitre.setAlignment(QtCore.Qt.AlignLeft)
        self.labelTitre.setObjectName(_fromUtf8("labelTitre"))
        self.gridLayout.addWidget(self.labelTitre, 0, 0, 1, 1)
        
        self.labelSsTitre = QtGui.QLabel(FormScManuels)
        self.labelSsTitre.setObjectName(_fromUtf8("labelSsTitre"))
        self.gridLayout.addWidget(self.labelSsTitre, 1, 0, 1, 2)
        

        self.tab_M1 = TabDF(FormScManuels)
        self.tab_M1.setFixedSize(QtCore.QSize(326, 370))
        self.tab_M1.setAlternatingRowColors(True)
        self.tab_M1.setObjectName(_fromUtf8("tab_M1"))
        self.tab_M1.horizontalHeader().setDefaultSectionSize(70)
        self.gridLayout.addWidget(self.tab_M1, 3, 0, 1, 1)

        self.tab_M2 = TabDF(FormScManuels)
        self.tab_M2.setFixedSize(QtCore.QSize(224, 370))
        self.tab_M2.setAlternatingRowColors(True)
        self.tab_M2.setObjectName(_fromUtf8("tab_M2"))
        self.tab_M2.horizontalHeader().setDefaultSectionSize(70)
        self.tab_M2.verticalHeader().setVisible(False)
        self.tab_M2.verticalHeader().setStretchLastSection(False)
        self.gridLayout.addWidget(self.tab_M2, 3, 1, 1, 1)
        

        self.label_M1 = QtGui.QLabel(FormScManuels)        
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_M1.setFont(font)
        self.label_M1.setAlignment(QtCore.Qt.AlignCenter)
        self.label_M1.setObjectName(_fromUtf8("label_M1"))
        self.gridLayout.addWidget(self.label_M1, 2, 0, 1, 1)
        
        self.label_M2 = QtGui.QLabel(FormScManuels)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_M2.setFont(font)
        self.label_M2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_M2.setObjectName(_fromUtf8("label_M2"))
        self.gridLayout.addWidget(self.label_M2, 2, 1, 1, 1)
        self.label_M1.setBuddy(self.tab_M1)
        self.label_M2.setBuddy(self.tab_M2)
        
        self.hSpacer = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(self.hSpacer, 3, 2, 1, 1)
        self.vSpacer = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(self.vSpacer, 4, 0, 1, 1)

        self.retranslateUi(FormScManuels)
        QtCore.QMetaObject.connectSlotsByName(FormScManuels)
        FormScManuels.setTabOrder(self.tab_M1, self.tab_M2)

    def retranslateUi(self, FormScManuels):
        FormScManuels.setWindowTitle(_translate("FormScManuels", "Form", None))
        self.labelTitre.setText(_translate("FormScManuels",u"Scénarios de pluie manuels", None))
        self.labelSsTitre.setText(_translate(
                "FormScManuels",
                trim(u"""Entrer les cumuls de pluie journaliers (mm) pour les scénarios de pluie manuels éventuels. Jusqu'à 2 scénarios manuels.
                     """),
                None))
        self.label_M1.setText(_translate("FormScManuels", "Manuel 1", None))
        self.label_M2.setText(_translate("FormScManuels", "Manuel 2", None))

class FormScManuels(QtGui.QWidget, Ui_FormScManuels):
    def __init__(self,parent=None):
        super(FormScManuels, self).__init__(parent)
        self.setupUi(self)
        

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    form = FormScManuels()
    form.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    form.show()
    sys.exit(app.exec_())

