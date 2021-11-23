from PySide6 import QtWidgets, QtGui, QtCore


class ImageViewer(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._first_file_dialog = True
        self._image_label = QtWidgets.QLabel()
        self._image_label.setBackgroundRole(QtGui.QPalette.Base)
        self._image_label.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                        QtWidgets.QSizePolicy.Ignored)
        self._image_label.setScaledContents(True)

        self.setCentralWidget(self._image_label)

        self._create_actions()

        self.resize(QtGui.QGuiApplication.primaryScreen(
        ).availableSize() * 3 / 5)  # type: ignore

    def load_file(self, fileName):
        reader = QtGui.QImageReader(fileName)
        reader.setAutoTransform(True)
        new_image = reader.read()
        native_filename = QtCore.QDir.toNativeSeparators(fileName)
        if new_image.isNull():
            error = reader.errorString()
            QtWidgets.QMessageBox.information(self, QtGui.QGuiApplication.applicationDisplayName(),
                                              f"Cannot load {native_filename}: {error}")
            return False

        # set content to show center in label
        self._set_image(new_image)
        self.setWindowFilePath(fileName)

        w = self._image.width()
        h = self._image.height()
        d = self._image.depth()
        color_space = self._image.colorSpace()
        description = color_space.description() if color_space.isValid() else 'unknown'
        message = f'Opened "{native_filename}", {w}x{h}, Depth: {d} ({description})'
        self.statusBar().showMessage(message)
        return True

    def _set_image(self, new_image):
        self._image = new_image
        if self._image.colorSpace().isValid():
            self._image.convertToColorSpace(QtGui.QColorSpace.SRgb)
        self._image_label.setPixmap(QtGui.QPixmap.fromImage(self._image))

    @QtCore.Slot()  # type: ignore
    def _open(self):
        dialog = QtWidgets.QFileDialog(self, "Open File")
        while (dialog.exec() == QtWidgets.QDialog.Accepted
               and not self.load_file(dialog.selectedFiles()[0])):
            pass

    def _create_actions(self):
        file_menu = self.menuBar().addMenu("&File")

        self._open_act = file_menu.addAction("&Open...")
        self._open_act.triggered.connect(self._open)  # type: ignore
        self._open_act.setShortcut(QtGui.QKeySequence.Open)

        file_menu.addSeparator()

        self._exit_act = file_menu.addAction("E&xit")
        self._exit_act.triggered.connect(self.close)  # type: ignore
        self._exit_act.setShortcut("Ctrl+Q")
