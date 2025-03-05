try:
    from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QPoint, QAbstractAnimation, QParallelAnimationGroup
    from PyQt6.QtWidgets import QWidget, QPushButton, QGridLayout, QHBoxLayout
    AlignLeft = Qt.AlignmentFlag.AlignLeft
    AlignRight = Qt.AlignmentFlag.AlignRight
    AnimForward = QAbstractAnimation.Direction.Forward
    AnimBackward = QAbstractAnimation.Direction.Backward

except ImportError:
    from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QPoint, QAbstractAnimation, QParallelAnimationGroup
    from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QHBoxLayout
    AlignLeft = Qt.AlignLeft
    AlignRight = Qt.AlignRight
    AnimForward = QAbstractAnimation.Forward
    AnimBackward = QAbstractAnimation.Backward


class PyQtSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.__initVal()
        self.__initUi()

    def __initVal(self):
        self.__circle_diameter = 20
        self.__animationEnabledFlag = False
        self.__pointAnimation = ''
        self.__colorAnimation = ''

    def __initUi(self):
        self.__circle = QPushButton()
        self.__circle.setCheckable(True)
        self.__circle.toggled.connect(self.__toggled)

        self.__layForBtnAlign = QHBoxLayout()
        self.__layForBtnAlign.setAlignment(AlignLeft)
        self.__layForBtnAlign.addWidget(self.__circle)
        self.__layForBtnAlign.setContentsMargins(0, 0, 0, 0)

        innerWidgetForStyle = QWidget()
        innerWidgetForStyle.setLayout(self.__layForBtnAlign)

        lay = QGridLayout()
        lay.addWidget(innerWidgetForStyle)
        lay.setContentsMargins(0, 0, 0, 0)

        self.setLayout(lay)

        self.__setStyle()

    def __setStyle(self):
        self.__circle.setFixedSize(self.__circle_diameter, self.__circle_diameter)
        self.setStyleSheet(
            f'QWidget {{ border: {self.__circle_diameter // 20}px solid #AAAAAA; '
            f'border-radius: {self.__circle_diameter // 2}px; }}')
        self.setFixedSize(self.__circle_diameter * 2, self.__circle_diameter)

    def setAnimation(self, f: bool):
        self.__animationEnabledFlag = f
        if self.__animationEnabledFlag:
            self.__colorAnimation = QPropertyAnimation(self, b'point')
            self.__colorAnimation.valueChanged.connect(self.__circle.move)
            self.__colorAnimation.setDuration(100)
            self.__colorAnimation.setStartValue(QPoint(0, 0))
            self.__colorAnimation.setEndValue(QPoint(self.__circle_diameter, 0))

            self.__pointAnimation = QPropertyAnimation(self, b'color')
            self.__pointAnimation.valueChanged.connect(self.__setColor)
            self.__pointAnimation.setDuration(100)
            self.__pointAnimation.setStartValue(255)
            self.__pointAnimation.setEndValue(200)

            self.__animationGroup = QParallelAnimationGroup()
            self.__animationGroup.addAnimation(self.__colorAnimation)
            self.__animationGroup.addAnimation(self.__pointAnimation)

    def mousePressEvent(self, e):
        self.__circle.toggle()
        return super().mousePressEvent(e)

    def __toggled(self, f):
        if self.__animationEnabledFlag:
            if f:
                self.__animationGroup.setDirection(AnimForward)
                self.__animationGroup.start()
            else:
                self.__animationGroup.setDirection(AnimBackward)
                self.__animationGroup.start()
        else:
            if f:
                self.__circle.move(self.__circle_diameter, 0)
                self.__layForBtnAlign.setAlignment(AlignRight)
                self.__setColor(200)
            else:
                self.__circle.move(0, 0)
                self.__layForBtnAlign.setAlignment(AlignLeft)
                self.__setColor(255)
        self.toggled.emit(f)

    def __setColor(self, f: int):
        self.__circle.setStyleSheet(f'QPushButton {{ background-color: rgb({f}, {f}, 255); }}')

    def setCircleDiameter(self, diameter: int):
        self.__circle_diameter = diameter
        self.__setStyle()
        self.__colorAnimation.setEndValue(QPoint(self.__circle_diameter, 0))

    def setChecked(self, f: bool):
        self.__circle.setChecked(f)
        self.__toggled(f)

    def isChecked(self):
        return self.__circle.isChecked()