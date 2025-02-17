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
        self.viewer.setFixedSize(840, 680)
        self.viewer2.setFixedSize(840, 680)
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

    def detectSigns(self):
        if self.OpenCV_image is None:
            QMessageBox.warning(self, "Error", "Aún no has cargado una imagen")
            return

        self.OpenCV_image2 = self.OpenCV_image.copy()
        hsv = cv2.cvtColor(self.OpenCV_image2, cv2.COLOR_BGR2HSV)

        # Improved color ranges with better sensitivity
        lower_red1, upper_red1 = np.array([0, 100, 100]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([160, 100, 100]), np.array([180, 255, 255])
        lower_blue = np.array([85, 100, 50])
        upper_blue = np.array([130, 255, 255])
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([40, 255, 255])

        # Enhanced morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)

        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)

        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel)

        # Combine masks for better edge detection
        combined_mask = cv2.bitwise_or(mask_red, cv2.bitwise_or(mask_blue, mask_yellow))

        # Improved edge detection with blurring
        gray = cv2.cvtColor(self.OpenCV_image2, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(gray)
        edges = cv2.Canny(gray_clahe, 50, 150)

        # Combine edges with color information
        combined_edges = cv2.bitwise_and(edges, combined_mask)

        # Find contours from combined edges
        contours, _ = cv2.findContours(combined_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Shape detection parameters
        min_area = 500
        max_area = 50000
        aspect_ratio_range = (0.8, 1.2)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area or area > max_area:
                continue

            # Contour approximation with dynamic epsilon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            vertices = len(approx)

            # Shape classification with aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)

            shape = "unknown"
            if vertices == 3:
                shape = "triangle"
            elif vertices == 4:
                if 0.8 <= aspect_ratio <= 1.2:
                    shape = "square"
                else:
                    shape = "rectangle"
            elif 6 <= vertices <= 10:
                shape = "octagon"


            # Color detection with improved thresholding
            contour_mask = np.zeros_like(gray)
            cv2.drawContours(contour_mask, [contour], -1, 255, -1)

            color_scores = {
                "red": cv2.countNonZero(cv2.bitwise_and(mask_red, contour_mask)) / area,
                "blue": cv2.countNonZero(cv2.bitwise_and(mask_blue, contour_mask)) / area,
                "yellow": cv2.countNonZero(cv2.bitwise_and(mask_yellow, contour_mask)) / area
            }

            color_detected = max(color_scores, key=color_scores.get)
            min_color_threshold = 0.1  # Adjusted threshold

            if color_scores[color_detected] < min_color_threshold:
                continue

            # Final verification
            if shape == "unknown":
                continue

            # Draw results
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

                cv2.drawContours(self.OpenCV_image2, [approx], -1, (0, 255, 0), 2)
                label = f"{color_detected} {shape}"
                cv2.putText(self.OpenCV_image2, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

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

