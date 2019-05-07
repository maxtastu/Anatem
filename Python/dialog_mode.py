# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\PGRP\dialog_Mode.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from datetime import datetime as dt

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

class Ui_dialogMode(object):
    def setupUi(self, dialogMode):
        dialogMode.setObjectName(_fromUtf8("dialogMode"))
#        dialogMode.resize(253, 134)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dialogMode.sizePolicy().hasHeightForWidth())
        dialogMode.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(dialogMode)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        
        self.labelMode = QtGui.QLabel(dialogMode)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.labelMode.setFont(font)
        self.labelMode.setObjectName(_fromUtf8("labelMode"))
        self.verticalLayout.addWidget(self.labelMode)
        
        self.btnModeTR = QtGui.QRadioButton(dialogMode)
        self.btnModeTR.setChecked(True)
        self.btnModeTR.setObjectName(_fromUtf8("btnModeTR"))
        self.verticalLayout.addWidget(self.btnModeTR)
        
        self.btnModeTD = QtGui.QRadioButton(dialogMode)
        self.btnModeTD.setObjectName(_fromUtf8("btnModeTD"))
        self.verticalLayout.addWidget(self.btnModeTD)
        
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        
        self.labelDateRejeu = QtGui.QLabel(dialogMode)
        self.labelDateRejeu.setEnabled(False)
        self.labelDateRejeu.setObjectName(_fromUtf8("labelDateRejeu"))
        self.horizontalLayout.addWidget(self.labelDateRejeu)
        
        self.dtEditDateRejeu = QtGui.QDateTimeEdit(dialogMode)
        self.dtEditDateRejeu.setEnabled(False)
        self.dtEditDateRejeu.setTimeSpec(QtCore.Qt.UTC)
        self.dtEditDateRejeu.setObjectName(_fromUtf8("dtEditDateRejeu"))
        self.dtEditDateRejeu.setDateTime(
                dt(year=dt.utcnow().year, month=1, day=1)
                )
        self.horizontalLayout.addWidget(self.dtEditDateRejeu)
        
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.vSpacer = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(self.vSpacer)
        
        self.buttonBox = QtGui.QDialogButtonBox(dialogMode)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        

        self.retranslateUi(dialogMode)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), dialogMode.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), dialogMode.reject)
        QtCore.QObject.connect(self.btnModeTD, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.labelDateRejeu.setEnabled)
        QtCore.QObject.connect(self.btnModeTD, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.dtEditDateRejeu.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(dialogMode)
        dialogMode.setTabOrder(self.btnModeTR, self.btnModeTD)
        dialogMode.setTabOrder(self.btnModeTD, self.dtEditDateRejeu)
        dialogMode.setTabOrder(self.dtEditDateRejeu, self.buttonBox)

    def retranslateUi(self, dialogMode):
        dialogMode.setWindowTitle(_translate("dialogMode", "Paramètres du lancement", None))
        self.labelMode.setText(_translate("dialogMode", "Lancer les modèles en mode :", None))
        self.btnModeTR.setText(_translate("dialogMode", "Temps réel", None))
        self.btnModeTD.setText(_translate("dialogMode", "Rejeu", None))
        self.labelDateRejeu.setText(_translate("dialogMode", "Date du rejeu (TU) :", None))
        self.dtEditDateRejeu.setDisplayFormat(_translate("dialogMode", "dd/MM/yyyy HH:00", None))

class DialogMode(QtGui.QDialog):
    def __init__(self, parent=None):
        super(DialogMode, self).__init__(parent)
        self.ui = Ui_dialogMode()
        self.ui.setupUi(self)

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    dialogMode = DialogMode()
    dialogMode.show()
    sys.exit(app.exec_())