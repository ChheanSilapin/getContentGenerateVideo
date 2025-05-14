# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'untitledFOJDmj.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_dialog(object):
    def setupUi(self, dialog):
        if not dialog.objectName():
            dialog.setObjectName(u"dialog")
        dialog.resize(620, 485)
        font = QFont()
        font.setPointSize(11)
        font.setBold(False)
        font.setItalic(False)
        dialog.setFont(font)
        dialog.setStyleSheet(u"font: 11pt \"Cascadia Code\";")
        self.tabWidget = QTabWidget(dialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(10, 10, 611, 481))
        self.tabWidget.setStyleSheet(u"font: 11pt \"Cascadia Code\";\n"
"selection-background-color: rgb(0, 85, 255);")
        self.Input = QWidget()
        self.Input.setObjectName(u"Input")
        self.label = QLabel(self.Input)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 311, 21))
        self.label.setFont(font)
        self.label.setStyleSheet(u"font: 11pt \"Cascadia Code\";\n"
"selection-background-color: rgb(0, 85, 255);")
        self.txtPrompt = QLineEdit(self.Input)
        self.txtPrompt.setObjectName(u"txtPrompt")
        self.txtPrompt.setGeometry(QRect(10, 40, 581, 211))
        self.txtPrompt.setFont(font)
        self.txtPrompt.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"font: 11pt \"Cascadia Code\";")
        self.label_3 = QLabel(self.Input)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 260, 191, 31))
        self.label_3.setStyleSheet(u"font: 11pt \"Poppins\";\n"
"selection-background-color: rgb(0, 85, 255);")
        self.txtUrl = QLineEdit(self.Input)
        self.txtUrl.setObjectName(u"txtUrl")
        self.txtUrl.setGeometry(QRect(10, 300, 311, 22))
        self.lineEdit_local_folder = QLineEdit(self.Input)
        self.lineEdit_local_folder.setObjectName(u"lineEdit_local_folder")
        self.lineEdit_local_folder.setEnabled(True)
        self.lineEdit_local_folder.setGeometry(QRect(10, 340, 311, 22))
        self.lineEdit_local_folder.setAutoFillBackground(False)
        self.lineEdit_local_folder.setReadOnly(True)
        self.btnUrl = QPushButton(self.Input)
        self.btnUrl.setObjectName(u"btnUrl")
        self.btnUrl.setGeometry(QRect(320, 299, 75, 24))
        self.btnFolder = QPushButton(self.Input)
        self.btnFolder.setObjectName(u"btnFolder")
        self.btnFolder.setGeometry(QRect(320, 339, 75, 24))
        self.btnStart = QPushButton(self.Input)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setGeometry(QRect(380, 390, 61, 41))
        self.btnStart.setStyleSheet(u"background-color: rgb(0, 255, 0);")
        self.btnStop = QPushButton(self.Input)
        self.btnStop.setObjectName(u"btnStop")
        self.btnStop.setGeometry(QRect(450, 390, 61, 41))
        self.btnStop.setStyleSheet(u"background-color: rgb(223, 0, 0);")
        self.label_5 = QLabel(self.Input)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(470, 290, 51, 31))
        self.label_5.setStyleSheet(u"font: 11pt \"Cascadia Code\";\n"
"selection-background-color: rgb(0, 85, 255);")
        self.cbCpuGpu = QComboBox(self.Input)
        self.cbCpuGpu.addItem("")
        self.cbCpuGpu.addItem("")
        self.cbCpuGpu.setObjectName(u"cbCpuGpu")
        self.cbCpuGpu.setGeometry(QRect(530, 296, 61, 22))
        self.progressBar_converting = QProgressBar(self.Input)
        self.progressBar_converting.setObjectName(u"progressBar_converting")
        self.progressBar_converting.setGeometry(QRect(10, 400, 351, 23))
        self.progressBar_converting.setValue(0)
        self.label_6 = QLabel(self.Input)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(10, 367, 111, 31))
        self.label_6.setStyleSheet(u"font: 11pt \"Cascadia Code\";\n"
"selection-background-color: rgb(0, 85, 255);")
        self.btnClear = QPushButton(self.Input)
        self.btnClear.setObjectName(u"btnClear")
        self.btnClear.setGeometry(QRect(530, 390, 61, 41))
        self.btnClear.setStyleSheet(u"background-color: rgb(170, 255, 255);\n"
"font: 11pt \"Cascadia Code\";")
        self.tabWidget.addTab(self.Input, "")
        self.Image = QWidget()
        self.Image.setObjectName(u"Image")
        self.Image.setStyleSheet(u"font: 11pt \"Cascadia Code\";")
        self.lineEdit_select_image = QLineEdit(self.Image)
        self.lineEdit_select_image.setObjectName(u"lineEdit_select_image")
        self.lineEdit_select_image.setGeometry(QRect(10, 40, 581, 341))
        self.lineEdit_select_image.setReadOnly(True)
        self.label_2 = QLabel(self.Image)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(14, 10, 131, 21))
        self.label_2.setStyleSheet(u"font: 11pt \"Poppins\";\n"
"selection-background-color: rgb(0, 85, 255);")
        self.label_7 = QLabel(self.Image)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(343, 401, 171, 20))
        self.label_7.setStyleSheet(u"font: 11pt \"Poppins\";")
        self.btnClean = QPushButton(self.Image)
        self.btnClean.setObjectName(u"btnClean")
        self.btnClean.setGeometry(QRect(520, 390, 61, 41))
        self.btnClean.setStyleSheet(u"background-color: rgb(170, 255, 255);\n"
"font: 11pt \"Cascadia Code\";")
        self.tabWidget.addTab(self.Image, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.lineEdit_log = QLineEdit(self.tab)
        self.lineEdit_log.setObjectName(u"lineEdit_log")
        self.lineEdit_log.setGeometry(QRect(-10, -10, 621, 461))
        self.lineEdit_log.setStyleSheet(u"color: rgb(0, 0, 0);")
        self.tabWidget.addTab(self.tab, "")

        self.retranslateUi(dialog)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(dialog)
    # setupUi

    def retranslateUi(self, dialog):
        dialog.setWindowTitle(QCoreApplication.translate("dialog", u"GenerateVideo", None))
        self.label.setText(QCoreApplication.translate("dialog", u"Enter Text for Voice Generation: ", None))
        self.label_3.setText(QCoreApplication.translate("dialog", u"Choose image source:", None))
        self.txtUrl.setPlaceholderText(QCoreApplication.translate("dialog", u"InputWebUrl", None))
        self.lineEdit_local_folder.setPlaceholderText(QCoreApplication.translate("dialog", u"SelectFolder", None))
        self.btnUrl.setText(QCoreApplication.translate("dialog", u"URL", None))
        self.btnFolder.setText(QCoreApplication.translate("dialog", u"Folder", None))
        self.btnStart.setText(QCoreApplication.translate("dialog", u"Start", None))
        self.btnStop.setText(QCoreApplication.translate("dialog", u"Stop", None))
        self.label_5.setText(QCoreApplication.translate("dialog", u"Reder:", None))
        self.cbCpuGpu.setItemText(0, QCoreApplication.translate("dialog", u"CPU", None))
        self.cbCpuGpu.setItemText(1, QCoreApplication.translate("dialog", u"GPU", None))

        self.label_6.setText(QCoreApplication.translate("dialog", u"Converting", None))
        self.btnClear.setText(QCoreApplication.translate("dialog", u"Clear", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Input), QCoreApplication.translate("dialog", u"Input ", None))
        self.label_2.setText(QCoreApplication.translate("dialog", u"Select Image ", None))
        self.label_7.setText(QCoreApplication.translate("dialog", u"Clean all select image", None))
        self.btnClean.setText(QCoreApplication.translate("dialog", u"Clean", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Image), QCoreApplication.translate("dialog", u"Image ", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("dialog", u"Log", None))
    # retranslateUi

