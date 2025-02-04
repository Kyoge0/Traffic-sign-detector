import cv2
import numpy as np
from PyQt6 import QtWidgets, QtGui

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(10, 10, 900, 600)
        self.viewer = QtWidgets.QLabel(self)
        self.viewer.setStyleSheet("border: 1px solid black;")
        
        self.buttonOpen = QtWidgets.QPushButton("Open Image", self)
        self.buttonOpen.clicked.connect(self.handleOpen)
        
        self.processButton = QtWidgets.QPushButton("Detect Signs", self)
        self.processButton.clicked.connect(self.detectSigns)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.buttonOpen)
        layout.addWidget(self.processButton)
        layout.addWidget(self.viewer)
        
        self.image = None
    
    def handleOpen(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose File", "", "Images (*.jpg *.png)")
        if path:
            self.image = cv2.imread(path)
            self.displayImage(self.image)
    
    def detectSigns(self):
        if self.image is None:
            return
        
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        
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
        
        self.displayImage(self.image)
    
    def findContoursAndDraw(self, mask, color):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filter out small noise
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(self.image, (x, y), (x+w, y+h), color, 2)
    
    def displayImage(self, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        self.viewer.setPixmap(QtGui.QPixmap.fromImage(q_image))
        
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setWindowTitle("Traffic Sign Detector")
    window.show()
    sys.exit(app.exec())

