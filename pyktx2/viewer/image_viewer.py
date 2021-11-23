import pathlib
from typing import NamedTuple, Tuple, Optional, Dict
from PySide6 import QtWidgets, QtGui, QtCore
import pyktx2.parser


class Node(NamedTuple):
    data: Tuple[str, ...]
    children: Tuple['Node', ...]


class Ktx2Model(QtCore.QAbstractItemModel):
    def __init__(self, path: pathlib.Path, ktx2: pyktx2.parser.Ktx2, parent=None):
        super().__init__(parent)
        self.ktx2 = ktx2

        self. root = Node((), (
            Node(('vkFormat', ktx2.vkFormat.name), ()),
            Node(('typeSize', str(ktx2.typeSize)), ()),
            Node(('pixelWidth', str(ktx2.pixelWidth)), ()),
            Node(('pixelHeight', str(ktx2.pixelHeight)), ()),
            Node(('pixelDepth', str(ktx2.pixelDepth)), ()),
            Node(('layerCount', str(ktx2.layerCount)), ()),
            Node(('faceCount', str(ktx2.faceCount)), ()),
            Node(('levelCount', str(ktx2.levelCount)), ()),
            Node(('supercompressionScheme', ktx2.supercompressionScheme.name), ()),

            # dfdByteOffset: int
            # dfdByteLength: int
            # kvdByteOffset: int
            # kvdByteLength: int
            # sgdByteOffset: int
            # sgdByteLength: int
        ))

        self.map: Dict[Node, Tuple[int, Node]] = {
        }
        row = [1]

        def build_map(node: Node):
            for child in node.children:
                self.map[child] = (row[0], node)
                row[0] += 1
                build_map(child)
        build_map(self.root)

    def columnCount(self, parent: QtCore.QModelIndex) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role):
        if role == QtGui.Qt.DisplayRole:
            if index.isValid():
                item: Node = index.internalPointer()  # type: ignore
                return item.data[index.column()]

    # def flags(self, index):
    #     if not index.isValid():
    #         return QtCore.Qt.NoItemFlags
    #     return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section: int, orientation, role):
        match orientation, role:
            case QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole:
                # return self.rootItem.data(section)
                return ('name', 'value')[section]

    def index(self, row: int, column: int, parent: QtCore.QModelIndex) -> QtCore.QModelIndex:

        if not parent.isValid():
            parentItem = self.root
        else:
            parentItem: Node = parent.internalPointer()  # type: ignore
        childItem = parentItem.children[row]
        return self.createIndex(row, column, childItem)

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()
        childItem: Node = index.internalPointer()  # type: ignore
        if childItem == self.root:
            return QtCore.QModelIndex()
        row, parentItem = self.map[childItem]
        return self.createIndex(row, 0, parentItem)

    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        if not parent.isValid():
            parentItem = self.root
        else:
            parentItem: Node = parent.internalPointer()  # type: ignore
        return len(parentItem.children)


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

        # tree
        self.dock_left = QtWidgets.QDockWidget("ktx2", self)
        self.addDockWidget(QtGui.Qt.LeftDockWidgetArea, self.dock_left)
        self.tree = QtWidgets.QTreeView()
        self.dock_left.setWidget(self.tree)

    def load_file(self, path: pathlib.Path):
        import pyktx2.parser
        ktx2 = pyktx2.parser.parse_path(path)

        model = Ktx2Model(path, ktx2)
        self.tree.setModel(model)

        # reader = QtGui.QImageReader(path)
        # reader.setAutoTransform(True)
        # new_image = reader.read()
        # native_filename = QtCore.QDir.toNativeSeparators(path)
        # if new_image.isNull():
        #     error = reader.errorString()
        #     QtWidgets.QMessageBox.information(self, QtGui.QGuiApplication.applicationDisplayName(),
        #                                       f"Cannot load {native_filename}: {error}")
        #     return False

        # # set content to show center in label
        # self._set_image(new_image)
        # self.setWindowFilePath(path)

        # d = self._image.depth()
        # color_space = self._image.colorSpace()
        # description = color_space.description() if color_space.isValid() else 'unknown'
        message = f'Opened "{path}", {ktx2.pixelWidth}x{ktx2.pixelHeight}, format: {ktx2.vkFormat})'
        self.statusBar().showMessage(message)
        # return True

    def _set_image(self, new_image):
        self._image = new_image
        if self._image.colorSpace().isValid():
            self._image.convertToColorSpace(QtGui.QColorSpace.SRgb)
        self._image_label.setPixmap(QtGui.QPixmap.fromImage(self._image))

    @QtCore.Slot()  # type: ignore
    def _open(self):
        dialog = QtWidgets.QFileDialog(self, "Open File")
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setFilter(QtCore.QDir.Files)
        dialog.setNameFilters(['*.ktx2', '*'])
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return

        path = pathlib.Path(dialog.selectedFiles()[0])
        self.load_file(path)

    def _create_actions(self):
        file_menu = self.menuBar().addMenu("&File")

        self._open_act = file_menu.addAction("&Open...")
        self._open_act.triggered.connect(self._open)  # type: ignore
        self._open_act.setShortcut(QtGui.QKeySequence.Open)

        file_menu.addSeparator()

        self._exit_act = file_menu.addAction("E&xit")
        self._exit_act.triggered.connect(self.close)  # type: ignore
        self._exit_act.setShortcut("Ctrl+Q")
