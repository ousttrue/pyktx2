from .image_viewer import ImageViewer


def run():
    """PySide6 port of the widgets/imageviewer example from Qt v6.0"""
    from argparse import ArgumentParser, RawTextHelpFormatter
    import sys

    from PySide6.QtWidgets import (QApplication)

    arg_parser = ArgumentParser(description="Image Viewer",
                                formatter_class=RawTextHelpFormatter)
    arg_parser.add_argument('file', type=str, nargs='?', help='Image file')
    args = arg_parser.parse_args()

    app = QApplication(sys.argv)
    image_viewer = ImageViewer()

    if args.file and not image_viewer.load_file(args.file):
        sys.exit(-1)

    image_viewer.show()
    sys.exit(app.exec())
