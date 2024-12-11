from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from checkable_combo import CheckableComboBox  # Import your CheckableComboBox class

def test_checkable_combo():
    import sys
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    combo = CheckableComboBox()
    combo.addItems(['Option 1', 'Option 2', 'Option 3'])

    def print_selected():
        print("Selected items:", combo.currentData())

    combo.model().dataChanged.connect(print_selected)

    layout.addWidget(combo)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_checkable_combo()
