import cv2
import sys
import numpy as np
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtWidgets import QHBoxLayout


class MiEtiqueta(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.Lista = []
        self.setStyleSheet("border: 1px solid black;")

    clicked = pyqtSignal()

    def mousePressEvent(self, e):
        self.x = e.position().x()
        self.y = e.position().y()
        # self.center = e.pos()
        # self.Lista.append(e.pos())
        # print (type(e.pos()), str(self.x)+","+str(self.y))
        # self.Lista.append([self.x,self.y])
        self.Lista.append((self.x, self.y))

        print(self.Lista)
        self.clicked.emit()

class Window(QtWidgets.QWidget):

    def center(self):
        """
        Centra la Ventada SI o SI
        """
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def __init__(self):
        super().__init__()
        self.OpenCV_image = None
        self.OpenCV_image2 = None
        self.setGeometry(10, 10, 900, 600)
        self.center()

        self._path = None
        self.LastPoint = None

        self.viewer = MiEtiqueta()
        self.viewer2 = MiEtiqueta()
        self.buttonOpen = QtWidgets.QPushButton("Open Image")
        BUTTON_SIZE = QSize(200, 50)
        self.buttonOpen.setMinimumSize(BUTTON_SIZE)
        self.buttonOpen.clicked.connect(self.handleOpen)

        self.elements = []

        self.procesarImagenEntrada = QtWidgets.QPushButton("Procesar")
        self.procesarImagenEntrada.setMinimumSize(BUTTON_SIZE)
        self.procesarImagenEntrada.clicked.connect(self.ProcesarImage)

        self.guardarImagen = QtWidgets.QPushButton("Guardar")
        self.guardarImagen.setMinimumSize(BUTTON_SIZE)
        self.guardarImagen.clicked.connect(self.handleSaveFile)

        layout = QtWidgets.QGridLayout(self)
        self.botonProcesaReservado = QtWidgets.QPushButton("Reserved")
        # self.botonProcesaReservado.setText("Marker Ratio")
        # self.botonProcesaReservado.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.botonProcesaReservado.setMinimumSize(BUTTON_SIZE)
        self.botonProcesaReservado.clicked.connect(self.detectSigns)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.buttonOpen)
        #button_layout.addWidget(self.procesarImagenEntrada)
        button_layout.addWidget(self.botonProcesaReservado)
        button_layout.addWidget(self.guardarImagen)

        layout.addLayout(button_layout, 0, 0, 1, 4)
        layout.addWidget(self.viewer, 1, 0, 1, 2)
        layout.addWidget(self.viewer2, 1, 2, 1, 2)

        Tamano = (self.viewer.size().width(), self.viewer.size().height())

        print(self.viewer.size(), type(self.viewer.size()), Tamano)

    def ProcesarImage(self):
        pass

    def handleSaveFile(self):
        # options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        if self._path is not None:
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", ".", "Images(*.jpg *.png)")
            print(fileName)
            cv2.imwrite(fileName + ".png", self.OpenCV_image2,)


    def handleOpen(self):
        start = "."

        path = QtWidgets.QFileDialog.getOpenFileName(self, "Choose File", start, "Images(*.jpg *.png)")[0]
        #self.FilePath = path + ".txt"
        print(path)
        if path is not None:
            self._path = path
            self.ActualizarImagen()
    
    def detectSigns(self):
        if self.OpenCV_image is None:
            return

        self.OpenCV_image2 = self.OpenCV_image.copy()
        
        hsv = cv2.cvtColor(self.OpenCV_image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for traffic signs (red, blue, yellow)
        lower_red1, upper_red1 = np.array([0, 120, 70]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([170, 120, 70]), np.array([180, 255, 255])
        lower_blue, upper_blue = np.array([100, 150, 50]), np.array([140, 255, 255])
        lower_yellow, upper_yellow = np.array([15, 100, 100]), np.array([35, 255, 255])
        
        # Create masks
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Find contours for each color
        self.findContoursAndDraw(mask_red, (0, 0, 255))  # Red
        self.findContoursAndDraw(mask_blue, (255, 0, 0))  # Blue
        self.findContoursAndDraw(mask_yellow, (0, 255, 255))  # Yellow
        
        self.ActualizarPixMap2(self.OpenCV_image2)

    def findContoursAndDraw(self, mask, color):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filter out small noise
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(self.OpenCV_image2, (x, y), (x+w, y+h), color, 2)

    def ActualizarPixMap(self):
        QImageTemp = QtGui.QImage(cv2.cvtColor(self.OpenCV_image, cv2.COLOR_BGR2RGB), self.OpenCV_image.shape[1],
                                  self.OpenCV_image.shape[0], self.OpenCV_image.shape[1] * 3,
                                  QtGui.QImage.Format.Format_RGB888)

        pixmap = QtGui.QPixmap(QImageTemp)
        self.viewer.setPixmap(pixmap)

    def ActualizarPixMap2(self, image):
        QImageTemp = QtGui.QImage(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), image.shape[1], image.shape[0],
                                  image.shape[1] * 3, QtGui.QImage.Format.Format_RGB888)

        pixmap = QtGui.QPixmap(QImageTemp)
        self.viewer2.setPixmap(pixmap)

    def ActualizarImagen(self):

        self.OpenCV_image = cv2.imread(self._path)
        Tamano = (self.viewer.size().width(), self.viewer.size().height())
        print(self.viewer.size(), type(self.viewer.size()), Tamano)
        self.OpenCV_image = cv2.resize(self.OpenCV_image, Tamano, interpolation=cv2.INTER_LINEAR)

        # for i in self.viewer.Lista:
        #    print (i)

        QImageTemp = QtGui.QImage(cv2.cvtColor(self.OpenCV_image, cv2.COLOR_BGR2RGB), self.OpenCV_image.shape[1],
                                  self.OpenCV_image.shape[0], self.OpenCV_image.shape[1] * 3,
                                  QtGui.QImage.Format.Format_RGB888)

        pixmap = QtGui.QPixmap(QImageTemp)
        self.viewer.setPixmap(pixmap)
        self.viewer2.setPixmap(pixmap)

        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setWindowTitle("Traffic Sign Detector")
    window.show()
    sys.exit(app.exec())

