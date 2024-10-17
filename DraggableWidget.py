from PyQt6 import QtWidgets, QtCore

class DraggableWidget(QtWidgets.QWidget):
    '''
    This class is used to make a widget draggable.  A class just needs to inherit this.
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mousePressPos = None
        self.mouseMoveActive = False

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Capture the global position where the mouse was pressed
            self.mousePressPos = event.globalPosition().toPoint()
            self.mouseMoveActive = True

    def mouseMoveEvent(self, event):
        if self.mouseMoveActive and self.mousePressPos:
            # Calculate how far the mouse moved
            delta = event.globalPosition().toPoint() - self.mousePressPos
            # Move the widget (or window) by the same amount
            self.parent().move(self.parent().pos() + delta)
            # Update the press position for the next movement calculation
            self.mousePressPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Reset when the left mouse button is released
            self.mousePressPos = None
            self.mouseMoveActive = False