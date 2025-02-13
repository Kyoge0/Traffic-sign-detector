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
        self.OpenCV_image = None
        self.OpenCV_image2 = None
        self.setGeometry(10, 10, 1200, 900)
        self.center()

        self._path = None

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

    def detectSigns(self):
        global color_detected, color_thresholds
        color_detected = ""
        color_thresholds = ""
        if self.OpenCV_image is None:
            QMessageBox.warning(self, "Error", "Aun no has cargado una imagen")
            return

        self.OpenCV_image2 = self.OpenCV_image.copy()
        hsv = cv2.cvtColor(self.OpenCV_image, cv2.COLOR_BGR2HSV)

        lower_red1, upper_red1 = np.array([0, 120, 70]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([170, 120, 70]), np.array([180, 255, 255])
        lower_blue, upper_blue = np.array([100, 150, 50]), np.array([140, 255, 255])
        lower_yellow, upper_yellow = np.array([15, 100, 100]), np.array([35, 255, 255])

        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # formas & filtros
        gray = cv2.cvtColor(self.OpenCV_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        cv2.imshow("Gray", gray)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        th, dst= cv2.threshold(blurred,27,255, 1)

        cv2.imshow("thresh", dst)
        edges = cv2.Canny(dst, 50, 150)
        cv2.imshow("imagen", edges)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            flag = False
            if area <= 50:
                continue

            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            vertices = len(approx)

            # check forma
            shape = None
            if vertices == 3:
                shape = "triangulo"
            elif vertices == 4:
                x, y, w, h = cv2.boundingRect(approx)
                shape = "rombo/cuadrado"
            elif 8 <= vertices <= 10:
                shape = "octagonon"
            else:
                shape = "unknown"
                print(vertices)
                #continue

            contour_mask = np.zeros_like(gray)
            cv2.drawContours(contour_mask, [contour], -1, 255, -1)

            # Calcular superposición con máscaras de color
            if  area < 300:  # Figuras pequeñas (naranja)
                flag = True
                color = (0, 165, 255)  # Naranja en BGR
            else:
                color_detected = None

            color_thresholds = {
                "red": 0.1,
                "blue": 0.7,
                "yellow": 0.7,
                "bluetooth": 0.2,
                "red2": 0.001  # perramadre
            }

            for color_name, color_mask in [("red", mask_red), ("blue", mask_blue), ("yellow", mask_yellow), ("bluetooth", mask_blue), ("red2", mask_red)]:
                overlap = cv2.bitwise_and(contour_mask, color_mask)
                overlap_area = cv2.countNonZero(overlap)

                if overlap_area / area > color_thresholds[color_name]:
                    color_detected = color_name
                    break

            # if color_detected:
            #     M = cv2.moments(contour)
            #     if M["m00"] != 0:
            #         cX = int(M["m10"] / M["m00"])
            #         cY = int(M["m01"] / M["m00"])
            #
            #         # punto central & cuadradiño
            #         cv2.circle(self.OpenCV_image2, (cX, cY), 5, (0, 0, 255), -1)
            #         x, y, w, h = cv2.boundingRect(contour)
            #         cv2.rectangle(self.OpenCV_image2, (x, y), (x + w, y + h), (0, 255, 0), 2)
            #
            #         print(f"Detected: {color_detected} {shape} at ({cX}, {cY})")
            if color_detected and not flag:  # Coincide con un color permitido (verde)
                color = (0, 255, 0)  # Verde en BGR
            elif not color_detected and not flag:  # No coincide con ningún color permitido (rojo)
                color = (0, 0, 255)  # Rojo en BGR

            # Dibujar el contorno y etiquetar la forma
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(self.OpenCV_image2, (x, y), (x + w, y + h), color, 2)
            cv2.putText(self.OpenCV_image2, shape, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

        self.ActualizarPixMap2(self.OpenCV_image2)

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

