#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# SOURCE: http://itnotesblog.ru/note.php?id=272#sthash.e5tCuHk0.dpbs


from PyQt5 import Qt
from mainwidget_ui import Ui_MainWidget
import cv2
import numpy as np


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    import traceback
    text += ''.join(traceback.format_tb(tb))

    print(text)
    Qt.QMessageBox.critical(None, 'Error', text)
    quit()


import sys
sys.excepthook = log_uncaught_exceptions


CONFIG_FILE_NAME = "config.ini"
WINDOW_TITLE = 'Color Detection Tool'
GRAY_COLOR_TABLE = [Qt.qRgb(i, i, i) for i in range(256)]


def numpy_array_to_QImage(numpy_array):
    if numpy_array.dtype != np.uint8:
        return

    height, width = numpy_array.shape[:2]

    if len(numpy_array.shape) == 2:
        img = Qt.QImage(numpy_array.data, width, height, numpy_array.strides[0], Qt.QImage.Format_Indexed8)
        img.setColorTable(GRAY_COLOR_TABLE)
        return img

    elif len(numpy_array.shape) == 3:
        if numpy_array.shape[2] == 3:
            img = Qt.QImage(numpy_array.data, width, height, numpy_array.strides[0], Qt.QImage.Format_RGB888)
            return img

        elif numpy_array.shape[2] == 4:
            img = Qt.QImage(numpy_array.data, width, height, numpy_array.strides[0], Qt.QImage.Format_ARGB32)
            return img


class MainWindow(Qt.QWidget):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWidget()
        self.ui.setupUi(self)

        self.setWindowTitle(WINDOW_TITLE)

        self.ui.rbResult.setChecked(True)

        self.ui.chOnlyExternal.clicked.connect(self.refresh_HSV)

        # TODO: поместить перед пружиной (spacer)
        self.cbResultHSV = Qt.QCheckBox('HSV')
        self.cbResultHSV.clicked.connect(self.refresh_HSV)

        self.ui.horizontalLayout_2.addWidget(self.cbResultHSV)

        # TODO: добавить флаг, который покажет картинку в HSV цвете, ведь в этом цвете и осуществляется поиск

        # TODO: вынести виджеты в UI
        # TODO: поддержать возможность сохранения состояния для cbPenStyle, sbPenWidth, pen_color и ui.chOnlyExternal
        # TODO: Result и OnlyExternal (флаг HSV) объединить в groupbox'е
        self.lbHsvMin = Qt.QLabel()
        self.lbHsvMin.setFrameShape(Qt.QFrame.Box)
        self.lbHsvMin.setMinimumHeight(10)
        self.lbHsvMin.setScaledContents(True)

        self.lbHsvMax = Qt.QLabel()
        self.lbHsvMax.setFrameShape(Qt.QFrame.Box)
        self.lbHsvMax.setMinimumHeight(10)
        self.lbHsvMax.setScaledContents(True)

        self.ui.gridLayout_2.addWidget(self.lbHsvMin, 3, 0, 1, 3)
        self.ui.gridLayout_2.addWidget(self.lbHsvMax, 3, 3, 1, 3)

        self.cbPenStyle = Qt.QComboBox()
        self.cbPenStyle.addItem('Solid', Qt.Qt.SolidLine)
        self.cbPenStyle.addItem('Dash', Qt.Qt.DashLine)
        self.cbPenStyle.addItem('Dot', Qt.Qt.DotLine)
        self.cbPenStyle.addItem('Dash Dot', Qt.Qt.DashDotLine)
        self.cbPenStyle.addItem('Dash Dot Dot', Qt.Qt.DashDotDotLine)
        self.cbPenStyle.currentIndexChanged.connect(self.refresh_HSV)

        self.sbPenWidth = Qt.QDoubleSpinBox()
        self.sbPenWidth.setRange(1.0, 20.0)
        self.sbPenWidth.valueChanged.connect(self.refresh_HSV)

        self.pen_color = Qt.Qt.green

        self.pbPenColor = Qt.QToolButton()
        self.pbPenColor.setMinimumWidth(100)
        palette = self.pbPenColor.palette()
        palette.setColor(Qt.QPalette.Button, self.pen_color)
        self.pbPenColor.setPalette(palette)
        self.pbPenColor.setAutoFillBackground(True)
        self.pbPenColor.setAutoRaise(True)
        self.pbPenColor.clicked.connect(self._choose_color)

        gb_pen_layout = Qt.QHBoxLayout()

        gb_pen_layout.addWidget(Qt.QLabel('Style:'))
        gb_pen_layout.addWidget(self.cbPenStyle)

        gb_pen_layout.addWidget(Qt.QLabel('Width:'))
        gb_pen_layout.addWidget(self.sbPenWidth)

        gb_pen_layout.addWidget(Qt.QLabel('Color:'))
        gb_pen_layout.addWidget(self.pbPenColor)

        gb_pen_layout.addStretch()

        self.gbPen = Qt.QGroupBox('Сontour:')
        self.gbPen.setLayout(gb_pen_layout)

        self.ui.gridLayout_2.addWidget(self.gbPen, 4, 0, 1, 6)

        self.settings = Qt.QSettings(CONFIG_FILE_NAME, Qt.QSettings.IniFormat)
        self.last_load_path = self.settings.value("lastLoadPath", ".")

        self.image_source = None
        self.result_img = None

        for w in self.findChildren(Qt.QSlider):
            w.sliderMoved.connect(self.refresh_HSV)

            name = w.objectName()
            w.setValue(int(self.settings.value(name, w.value())))
            sp = self.findChild(Qt.QSpinBox, "sp" + name[2:])
            if sp:
                sp.setMinimum(w.minimum())
                sp.setMaximum(w.maximum())
                sp.setValue(w.value())
                sp.valueChanged.connect(self.refresh_HSV)

        for w in self.findChildren(Qt.QSpinBox):
            w.valueChanged.connect(self.refresh_HSV)

        for w in self.findChildren(Qt.QRadioButton):
            w.clicked.connect(self.refresh_HSV)

        self.ui.bnLoad.clicked.connect(self.on_load)

        self.refresh_HSV()

    def on_load(self):
        image_filters = "Images (*.jpg *.jpeg *.png *.bmp)"
        file_name = Qt.QFileDialog.getOpenFileName(self, "Load image", self.last_load_path, image_filters)[0]
        if not file_name:
            return

        self.last_load_path = Qt.QFileInfo(file_name).absolutePath()

        # Load image as bytes
        with open(file_name, 'rb') as f:
            img_data = f.read()

        nparr = np.frombuffer(img_data, np.uint8)
        self.image_source = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        height, width, channels = self.image_source.shape
        self.setWindowTitle(WINDOW_TITLE + '. {}x{} ({} channels). {}'.format(width, height, channels, file_name))

        # Трансформация BGR->RGB если 3 канала. У картинок с прозрачностью каналов 4 и для них почему
        if channels == 3:
            self.image_source = cv2.cvtColor(self.image_source, cv2.COLOR_BGR2RGB)

        self.refresh_HSV()

    def show_result(self):
        if not self.result_img:
            return

        size = self.ui.lbView.size()
        pixmap = Qt.QPixmap.fromImage(self.result_img).scaled(size, Qt.Qt.KeepAspectRatio, Qt.Qt.SmoothTransformation)
        self.ui.lbView.setPixmap(pixmap)

    def _choose_color(self):
        color = Qt.QColorDialog.getColor(self.pen_color)
        if not color.isValid():
            return

        self.pen_color = color

        palette = self.pbPenColor.palette()
        palette.setColor(Qt.QPalette.Button, self.pen_color)
        self.pbPenColor.setPalette(palette)

        self.refresh_HSV()

    def _draw_contours(self, result_img, contours):
        line_size = self.sbPenWidth.value()
        line_type = self.cbPenStyle.currentData()
        line_color = self.pen_color

        p = Qt.QPainter(result_img)
        p.setPen(Qt.QPen(line_color, line_size, line_type))

        for c in contours:
            x, y, width, height = cv2.boundingRect(c)
            p.drawRect(x, y, width, height)

        p.end()

    def refresh_HSV(self):
        hue_from = self.ui.slHueFrom.value()
        hue_to = max(hue_from, self.ui.slHueTo.value())

        saturation_from = self.ui.slSaturationFrom.value()
        saturation_to = max(saturation_from, self.ui.slSaturationTo.value())

        value_from = self.ui.slValueFrom.value()
        value_to = max(value_from, self.ui.slValueTo.value())

        hsv_min = hue_from, saturation_from, value_from
        hsv_max = hue_to, saturation_to, value_to

        color_hsv_min = Qt.QColor.fromHsv(*hsv_min)
        color_hsv_max = Qt.QColor.fromHsv(*hsv_max)

        pixmap = Qt.QPixmap(1, 1)
        pixmap.fill(color_hsv_min)
        self.lbHsvMin.setPixmap(pixmap)

        pixmap = Qt.QPixmap(1, 1)
        pixmap.fill(color_hsv_max)
        self.lbHsvMax.setPixmap(pixmap)

        if self.image_source is None:
            return

        if self.ui.rbOriginal.isChecked():
            self.result_img = numpy_array_to_QImage(self.image_source)

        else:
            thresholded_image = cv2.cvtColor(self.image_source, cv2.COLOR_RGB2HSV)

            # Отфильтровываем только то, что нужно, по диапазону цветов
            thresholded_image = cv2.inRange(
                thresholded_image,
                np.array(hsv_min, np.uint8),
                np.array(hsv_max, np.uint8)
            )

            # Убираем шум
            thresholded_image = cv2.erode(
                thresholded_image,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            )
            thresholded_image = cv2.dilate(
                thresholded_image,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            )

            # Замыкаем оставшиеся крупные объекты
            thresholded_image = cv2.dilate(
                thresholded_image,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            )
            thresholded_image = cv2.erode(
                thresholded_image,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            )

            if self.ui.rbCanny.isChecked():
                # Визуально выделяем границы
                thresholded_image = cv2.Canny(thresholded_image, 100, 50, 5)

            if self.ui.rbResult.isChecked():
                mode = cv2.RETR_EXTERNAL if self.ui.chOnlyExternal.isChecked() else cv2.RETR_TREE

                # Находим контуры
                contours = cv2.findContours(
                    thresholded_image,
                    mode,
                    cv2.CHAIN_APPROX_SIMPLE
                )[1]

                result_img = self.image_source.copy()

                # Конвертирование цвета в HSV
                if self.cbResultHSV.isChecked():
                    result_img = cv2.cvtColor(result_img, cv2.COLOR_RGB2HSV)

                self.result_img = numpy_array_to_QImage(result_img)
                self._draw_contours(self.result_img, contours)

            else:
                self.result_img = numpy_array_to_QImage(thresholded_image)

        self.show_result()

    def resizeEvent(self, e):
        super().resizeEvent(e)

        self.show_result()

    def closeEvent(self, e):
        for w in self.findChildren(Qt.QSlider):
            name = w.objectName()
            self.settings.setValue(name, w.value())

        self.settings.setValue("lastLoadPath", self.last_load_path)


if __name__ == '__main__':
    app = Qt.QApplication([])

    mw = MainWindow()
    mw.show()

    app.exec()
