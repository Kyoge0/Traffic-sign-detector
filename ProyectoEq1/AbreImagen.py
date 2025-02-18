import cv2
import sys
import numpy as np
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtWidgets import QHBoxLayout, QMessageBox


class MiEtiqueta(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.Lista = []
        self.setStyleSheet("border: 1px solid black;")

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
        self.OpenCV_image3 = None
        self.OpenCV_image = None
        self.OpenCV_image2 = None
        self.center()

        self._path = None

        self.viewer = MiEtiqueta()
        self.viewer2 = MiEtiqueta()
        self.viewer.setFixedSize(440, 380)
        self.viewer2.setFixedSize(440, 380)
        self.viewer.setScaledContents(True)
        self.viewer2.setScaledContents(True)

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
        self.botonProcesaReservado = QtWidgets.QPushButton("Buscar Señales de Trafico")
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
        if self.OpenCV_image2 is not None:
            defaultname = "example.png"

            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", defaultname,
                                                                "Images(*.jpg *.png)")

            if fileName:
                if not fileName.endswith(('.png', '.jpg')):
                    fileName += ".png"
                cv2.imwrite(fileName, self.OpenCV_image2)
        else:
            QMessageBox.warning(self, "Error", "No hay nada que guardar aun")

    def handleOpen(self):
        start = "."

        path = QtWidgets.QFileDialog.getOpenFileName(self, "Choose File", start, "Images(*.jpg *.png)")[0]
        #self.FilePath = path + ".txt"
        if path:
            self._path = path
            self.ActualizarImagen()
        else:
            print("non") #añadir una advertencia que el path no vale verga

    import cv2
    import numpy as np

    def detectSigns(self):
        if self.OpenCV_image is None:
            QMessageBox.warning(self, "Error", "Aún no has cargado una imagen")
            return

        self.OpenCV_image2 = self.OpenCV_image.copy()
        hsv = cv2.cvtColor(self.OpenCV_image2, cv2.COLOR_BGR2HSV)

        # Define color ranges for segmentation
        lower_red1, upper_red1 = np.array([0, 120, 70]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([170, 120, 70]), np.array([180, 255, 255])
        lower_blue, upper_blue = np.array([100, 150, 50]), np.array([140, 255, 255])
        lower_yellow, upper_yellow = np.array([15, 100, 100]), np.array([35, 255, 255])

        # Create masks
        kernel = np.ones((5, 5), np.uint8)
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)

        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)

        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask_yellow = cv2.dilate(mask_yellow, kernel, iterations=1)

        # Edge detection
        gray = cv2.cvtColor(self.OpenCV_image2, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(gray)
        edges = cv2.Canny(gray_clahe, 50, 150)
        #cv2.imshow("Clahe", gray_clahe)
        #cv2.imshow("Edges", edges)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:
                continue

            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            vertices = len(approx)

            shape = None
            if vertices == 3:
                shape = "triangulo"
            elif vertices == 4:
                angle = cv2.minAreaRect(approx)[-1]
                if 40 < angle < 50:
                    shape = "rombo"
                else:
                    shape = "cuadrado"
            elif 6 <= vertices <= 8:
                shape = "octagono"
            else:
                continue

            # Check color overlap
            contour_mask = np.zeros_like(gray)
            cv2.drawContours(contour_mask, [contour], -1, 255, -1)

            color_detected = None
            color_thresholds = {"red": 0.1, "blue": 0.7, "yellow": 0.7}

            for color_name, color_mask in [("red", mask_red), ("blue", mask_blue), ("yellow", mask_yellow)]:
                overlap = cv2.bitwise_and(contour_mask, color_mask)
                overlap_area = cv2.countNonZero(overlap)

                if overlap_area / area > color_thresholds[color_name]:
                    color_detected = color_name
                    break

            if color_detected:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])

                    cv2.circle(self.OpenCV_image2, (cX, cY), 5, (0, 0, 255), -1)
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(self.OpenCV_image2, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    print(f"Detected: {color_detected} {shape} at ({cX}, {cY}) area: {area}")

        self.ActualizarPixMap2(self.OpenCV_image2)

    def ActualizarPixMap(self):
        display_width = self.viewer.width()
        display_height = self.viewer.height()
        resized = cv2.resize(self.OpenCV_image3, (display_width, display_height), interpolation=cv2.INTER_LINEAR)
        QImageTemp = QtGui.QImage(
            cv2.cvtColor(resized, cv2.COLOR_BGR2RGB),
            resized.shape[1],
            resized.shape[0],
            resized.shape[1] * 3,
            QtGui.QImage.Format.Format_RGB888
        )
        self.viewer.setPixmap(QtGui.QPixmap(QImageTemp))

    def ActualizarPixMap2(self, image):
        display_width = self.viewer2.width()
        display_height = self.viewer2.height()
        resized_image = cv2.resize(image, (display_width, display_height), interpolation=cv2.INTER_LINEAR)
        qimage = QtGui.QImage(
            cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB),
            resized_image.shape[1],
            resized_image.shape[0],
            resized_image.shape[1] * 3,
            QtGui.QImage.Format.Format_RGB888
        )
        self.viewer2.setPixmap(QtGui.QPixmap(qimage))

    def ActualizarImagen(self):
        self.OpenCV_image = cv2.imread(self._path)
        self.OpenCV_image3 = self.OpenCV_image.copy()
        displaysize = (self.viewer.width(), self.viewer.height())
        self.OpenCV_image3 = cv2.resize(self.OpenCV_image3, displaysize, interpolation=cv2.INTER_LINEAR)
        QImageTemp = QtGui.QImage(
            cv2.cvtColor(self.OpenCV_image3, cv2.COLOR_BGR2RGB),
            self.OpenCV_image3.shape[1],
            self.OpenCV_image3.shape[0],
            self.OpenCV_image3.shape[1] * 3,
            QtGui.QImage.Format.Format_RGB888
        )
        pixmap = QtGui.QPixmap(QImageTemp)
        self.viewer.setPixmap(pixmap)
        self.viewer2.setPixmap(pixmap)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setWindowTitle("Traffic Sign Detector")
    window.show()
    sys.exit(app.exec())

