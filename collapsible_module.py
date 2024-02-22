import sys
from PyQt5.QtCore import Qt, QPropertyAnimation, QAbstractAnimation, QParallelAnimationGroup
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QToolButton, QFrame, QScrollArea, QSizePolicy


class Collapsible(QWidget):
    CONTENT_AREA_MAX_HEIGHT = 900
    CONTENT_AREA_MIN_HEIGHT = 0
    CONTENT_AREA_MAX_WIDTH = 0
    CONTENT_AREA_MIN_WIDTH = 0
    COLLAPSED_WIDTH = 50

    def __init__(self, title="", animationDuration=300, parent=None):
        super().__init__(parent)
        self.animationDuration = animationDuration

        self.mainLayout = QVBoxLayout()
        self.horizontalLayout = QHBoxLayout()
        self.toggleButton = QToolButton()
        self.headerLine = QFrame()
        self.toggleAnimation = QParallelAnimationGroup()
        self.contentArea = QScrollArea()

        self.initUI(title)

        

    def initUI(self, title):

        self.toggleButton.setStyleSheet("QToolButton { border: none; }")
        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.RightArrow)
        self.toggleButton.setText(title)
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(True)

        self.headerLine.setFrameShape(QFrame.HLine)
        self.headerLine.setFrameShadow(QFrame.Sunken)
        self.headerLine.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.contentArea.setStyleSheet("QScrollArea { background-color: white; border: none; }")
        self.contentArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.contentArea.setMaximumWidth(self.CONTENT_AREA_MAX_HEIGHT)
        self.contentArea.setMinimumHeight(self.CONTENT_AREA_MIN_HEIGHT)
        self.contentArea.setMinimumWidth(self.CONTENT_AREA_MIN_WIDTH)
        self.contentArea.show()

        for _ in range(3):
            self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"minimumWidth"))
            self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"maximumWidth"))

        self.mainLayout.addWidget(self.toggleButton)  
        self.horizontalLayout.addWidget(self.contentArea)
        self.mainLayout.addLayout(self.horizontalLayout)
        self.setLayout(self.mainLayout)
        self.toggleButton.clicked.connect(self.onToggle)

    def setContentLayout(self, contentLayout):
        # Check if there is an existing layout
        if self.contentArea.layout():
            self.contentArea.layout().deleteLater()

        # Set the new content layout
        self.contentArea.setLayout(contentLayout)
        self.contentArea.setMaximumWidth(contentLayout.sizeHint().width())
        self.contentArea.setMaximumHeight(self.CONTENT_AREA_MAX_HEIGHT)
        
        self.contentWidth = contentLayout.sizeHint().width()          

        for i in range(self.toggleAnimation.animationCount() - 1):
            spoilerAnimation = self.toggleAnimation.animationAt(i)
            spoilerAnimation.setDuration(self.animationDuration)
            spoilerAnimation.setStartValue(self.COLLAPSED_WIDTH)
            spoilerAnimation.setEndValue(self.COLLAPSED_WIDTH + self.contentWidth)

        contentAnimation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount() - 1)
        contentAnimation.setDuration(self.animationDuration)
        contentAnimation.setStartValue(0)
        contentAnimation.setEndValue(self.contentWidth)
        self.contentArea.update()


    def onToggle(self):
        """When called, this function will update the value of the checked boolean, and show the content area accordingly. It starts the animation and sets the animation direction"""
        checked = self.toggleButton.isChecked()
        if (checked):
            self.contentArea.show()
        else:
            self.contentArea.hide()

        self.toggleButton.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.toggleAnimation.setDirection(QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward)
        self.toggleAnimation.start()