import pathlib
from typing import NamedTuple, Tuple, Dict, List, Any
from PySide6 import QtWidgets, QtGui, QtCore
import pyktx2.parser


class Node(NamedTuple):
    unique_key: int
    data: Tuple[str, Any]
    children: Tuple['Node', ...]


NODE_ID = 1


def get_id():
    global NODE_ID
    id = NODE_ID
    NODE_ID += 1
    return id


class Ktx2Model(QtCore.QAbstractItemModel):
    def __init__(self, path: pathlib.Path, ktx2: pyktx2.parser.Ktx2, parent=None):
        super().__init__(parent)
        self.ktx2 = ktx2

        def level_index_node(i, level_index: pyktx2.parser.LevelIndex) -> Node:
            return Node(get_id(), ('level', i), (
                Node(get_id(), ('byteOffset', level_index.byteOffset), ()),
                Node(get_id(), ('byteLength', level_index.byteLength), ()),
                Node(get_id(), ('uncompressedByteLength',
                                level_index.uncompressedByteLength), ()),
            ))

        def dfd_node(dfd):
            return Node(get_id(), ('dfd', ''), ())

        def depth_image_node(level: int, layer: int, face: int, depth: int) -> Node:
            return Node(get_id(), ('depth', depth), tuple(

            ))

        def face_image_node(level: int, layer: int, face: int) -> Node:
            depth_count = ktx2.pixelDepth
            if depth_count == 0:
                depth_count = 1
            return Node(get_id(), ('face', face), tuple(
                depth_image_node(level, layer, face, depth) for depth in range(depth_count)
            ))

        def layer_image_node(level: int, layer: int) -> Node:
            face_count = ktx2.faceCount
            return Node(get_id(), ('layer', layer), tuple(
                face_image_node(level, layer, face) for face in range(face_count)
            ))

        def level_image_node(level: int):
            layer_count = ktx2.layerCount
            if layer_count == 0:
                layer_count = 1
            return Node(get_id(), ('level', level), tuple(
                layer_image_node(level, layer) for layer in range(layer_count)
            ))

        self. root = Node(get_id(), ('__root__', ''), (
            Node(get_id(), ('vkFormat', ktx2.vkFormat.name), ()),
            Node(get_id(), ('typeSize', ktx2.typeSize), ()),
            Node(get_id(), ('pixelWidth', ktx2.pixelWidth), ()),
            Node(get_id(), ('pixelHeight', ktx2.pixelHeight), ()),
            Node(get_id(), ('pixelDepth', ktx2.pixelDepth), ()),
            Node(get_id(), ('layerCount', ktx2.layerCount), ()),
            Node(get_id(), ('faceCount', ktx2.faceCount), ()),
            Node(get_id(), ('levelCount', ktx2.levelCount), ()),
            Node(get_id(), ('supercompressionScheme',
                 ktx2.supercompressionScheme.name), ()),

            Node(get_id(), ('dfdByteOffset', ktx2.dfdByteOffset), ()),
            Node(get_id(), ('dfdByteLength', ktx2.dfdByteLength), ()),
            Node(get_id(), ('kvdByteOffset', ktx2.kvdByteOffset), ()),
            Node(get_id(), ('kvdByteLength', ktx2.kvdByteLength), ()),
            Node(get_id(), ('sgdByteOffset', ktx2.sgdByteOffset), ()),
            Node(get_id(), ('sgdByteLength', ktx2.sgdByteLength), ()),

            Node(get_id(), ('levelIndices', len(ktx2.levelIndices)), tuple(
                level_index_node(i, level) for i, level in enumerate(ktx2.levelIndices)
            )),

            dfd_node(ktx2.dfd),

            Node(get_id(), ('kv', len(ktx2.kv)), tuple(
                Node(get_id(), (k, v), ()) for k, v in ktx2.kv.items()
            )),
            Node(get_id(), ('supercompressionGlobalData',
                            len(ktx2.supercompressionGlobalData)), ()),
            Node(get_id(), ('levelImages', len(ktx2.levelImages)), tuple(
                level_image_node(level) for level in range(max(1, ktx2.levelCount))
            )),
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

    def _find(self, path: List[Node], node: Node, target: Node):
        path.append(node)
        for child in node.children:
            if child == target:
                return True
            if self._find(path, child, target):
                return True
        path.remove(node)
        return False

    def get_path(self, target: Node) -> List[Node]:
        path = []
        self._find(path, self.root, target)
        return path


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

    @ QtCore.Slot()  # type: ignore
    def _on_select(self, selected: QtCore.QItemSelection, deselected):
        for index in selected.indexes():
            item = index.internalPointer()
            self.select(item)

    def select(self, node: Node):
        node_path = self.model.get_path(node)
        path = [item.data[0] for item in node_path]
        match path:
            case ['__root__', 'levelImages', 'level', 'layer', 'face']:
                layer_count = max(1, self.ktx2.layerCount)
                face_count = max(1, self.ktx2.faceCount)
                depth_count = max(1, self.ktx2.pixelDepth)

                level = node_path[-3].data[1]
                layer = node_path[-2].data[1]
                face = node_path[-1].data[1]
                depth = node.data[1]
                image_index = level * \
                    (layer_count * face_count * depth_count) + layer * \
                    (face_count * depth_count) + face * (depth_count) + depth
                # print(
                #     f'show image: {level}, {layer}, {face}, {depth}: {image_index}')
                self._set_image(
                    self.ktx2.levelImages[image_index], self.ktx2.vkFormat)
            case _:
                # print('not match')
                pass

    def load_file(self, path: pathlib.Path):
        import pyktx2.parser
        self.ktx2 = pyktx2.parser.parse_path(path)

        self.model = Ktx2Model(path, self.ktx2)
        self.tree.setModel(self.model)
        self.tree.selectionModel().selectionChanged.connect(
            self._on_select)  # type: ignore

        message = f'Opened "{path}", {self.ktx2.pixelWidth}x{self.ktx2.pixelHeight}, format: {self.ktx2.vkFormat})'
        self.statusBar().showMessage(message)
        # return True

    def _set_image(self, data: pyktx2.parser.Image, format: pyktx2.parser.VkFormat):
        image = QtGui.QImage(data.data, data.width,
                             data.height, QtGui.QImage.Format_RGBA16FPx4)
        # if self._image.colorSpace().isValid():
        #     self._image.convertToColorSpace(QtGui.QColorSpace.SRgb)
        self._image_label.setPixmap(QtGui.QPixmap.fromImage(image))

    @ QtCore.Slot()  # type: ignore
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
