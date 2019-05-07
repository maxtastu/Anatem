# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog_export.ui'
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

class DialogExport(QtGui.QDialog):
    def __init__(self, repertoire, parent=None):
        u"""repertoire : rep par défaut pour l'export
        
        """
        QtGui.QDialog.__init__(self, parent)
        self.repertoire = repertoire
        self.defaultRep = repertoire
        
        self.setObjectName(_fromUtf8("self"))
        self.resize(508, 366)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        
        self.labelMain = QtGui.QLabel(self)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.labelMain.setFont(font)
        self.labelMain.setObjectName(_fromUtf8("labelMain"))
        self.verticalLayout.addWidget(self.labelMain)
                
        self.frameOptions = QtGui.QFrame(self)
        self.frameOptions.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frameOptions.setFrameShadow(QtGui.QFrame.Raised)
        self.frameOptions.setObjectName(_fromUtf8("frameOptions"))
        self.gridLayout = QtGui.QGridLayout(self.frameOptions)    
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))

        self.chboxes = {}

        self.chboxes["XML"] = QtGui.QCheckBox(self.frameOptions)
        self.gridLayout.addWidget(self.chboxes["XML"], 0, 1, 1, 1, QtCore.Qt.AlignLeft)
        self.chboxes["XML"].setToolTip(u"pour EAO")
        
        self.chboxes["CSV"] = QtGui.QCheckBox(self.frameOptions)
        self.gridLayout.addWidget(self.chboxes["CSV"], 0, 2, 1, 1)
        self.chboxes["CSV"].setToolTip(u"pour traitement de données")
        
    
        self.labelFormat = QtGui.QLabel(self.frameOptions)
        self.labelFormat.setObjectName(_fromUtf8("labelFormat"))
        self.gridLayout.addWidget(self.labelFormat, 0, 0, 1, 1)
        
        self.labelDir = QtGui.QLabel(self.frameOptions)
        self.labelDir.setObjectName(_fromUtf8("labelDir"))
        self.gridLayout.addWidget(self.labelDir, 1, 0, 1, 1)
        
        self.editDir = QtGui.QLineEdit(self.frameOptions)
        self.editDir.setObjectName(_fromUtf8("editDir"))
        self.editDir.setFixedWidth(300)
        self.gridLayout.addWidget(self.editDir, 1, 1, 1, 3)
        
        self.btnParcourir = QtGui.QPushButton(self.frameOptions)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnParcourir.sizePolicy().hasHeightForWidth())
        self.btnParcourir.setSizePolicy(sizePolicy)
        self.btnParcourir.setObjectName(_fromUtf8("btnParcourir"))
        self.gridLayout.addWidget(self.btnParcourir, 1, 4, 1, 1)
                
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 4, 2, 1)
        self.verticalLayout.addWidget(self.frameOptions)

        self.table = TabDF(self, colWidth=70)
        self.table.setObjectName(_fromUtf8("table"))
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.verticalLayout.addWidget(self.table)
        
        self.frameBtns = QtGui.QFrame(self)
        self.frameBtns.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frameBtns.setFrameShadow(QtGui.QFrame.Raised)
        self.frameBtns.setObjectName(_fromUtf8("frameBtns"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.frameBtns)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        
        self.btnExport = QtGui.QPushButton(self.frameBtns)
        self.btnExport.setObjectName(_fromUtf8("btnExport"))
        self.horizontalLayout.addWidget(self.btnExport)
        
        self.btnFin = QtGui.QPushButton(self.frameBtns)
        self.btnFin.setObjectName(_fromUtf8("btnFin"))
        self.horizontalLayout.addWidget(self.btnFin)
        
        self.verticalLayout.addWidget(self.frameBtns)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        
        self.editDir.textEdited.connect(self.new_dir_manuel)
        self.btnParcourir.clicked.connect(self.get_dir)
        self.btnFin.clicked.connect(self.reject)

    def retranslateUi(self):
        self.setWindowTitle(_translate("DialogExport", "Export", None))
        self.labelMain.setText(_translate("DialogExport", "Choisir les sorties de modèles à exporter :", None))
        self.labelFormat.setText(_translate("DialogExport", "Format :", None))
        self.labelDir.setText(_translate("DialogExport", "Répertoire :", None))
        self.editDir.setText(_translate("DialogExport", self.repertoire, None))
        self.btnParcourir.setText(_translate("DialogExport", "Parcourir", None))
        self.chboxes["XML"].setText(_translate("DialogExport", "XML", None))
        self.chboxes["CSV"].setText(_translate("DialogExport", "CSV", None))
        self.btnExport.setText(_translate("DialogExport", "Exporter", None))
        self.btnFin.setText(_translate("DialogExport", "Terminé", None))

    def get_dir(self):
        u"""fonction associée au bouton Parcourir, pour récupérer et afficher
        le dossier choisi
        
        """
        
        rep = QtGui.QFileDialog.getExistingDirectory()
        if rep != '': #pour gérer le cas re vide (si annulation)
            self.repertoire = rep
            self.editDir.setText(str(self.repertoire))


    def new_dir_manuel(self, rep):
        u"""retient le répertoire entré manuellement
        
        """
        
        self.repertoire = rep

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    dialogExport = DialogExport(repertoire="D:\Anatem")
    dialogExport.show()
    sys.exit(app.exec_())
