import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QMenuBar, QFileDialog, QMessageBox
from PyQt6.QtGui import QAction

from json_parser import json_to_graph, graph_to_json
from graph_widget import GraphWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON Visualizer")
        self.setGeometry(100, 100, 1200, 800)

        self.graph_widget = GraphWidget()
        self.setCentralWidget(self.graph_widget)

        self._create_menu_bar()

        # Load a sample graph on startup for demonstration
        self.load_sample()

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        open_action = QAction("&Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save As...", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def load_sample(self):
        sample_json = """
        {
            "example": "This is a sample JSON.",
            "data": {
                "items": [1, true, "three"],
                "nested_obj": {"key": "value"}
            }
        }
        """
        try:
            data = json.loads(sample_json)
            graph = json_to_graph(data)
            self.graph_widget.set_graph(graph)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sample JSON: {e}")

    def open_file(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)")
        if fileName:
            try:
                with open(fileName, 'r') as f:
                    data = json.load(f)
                graph = json_to_graph(data)
                self.graph_widget.set_graph(graph)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load or parse file: {e}")

    def save_file(self):
        if self.graph_widget.graph is None:
            QMessageBox.warning(self, "Warning", "There is no data to save.")
            return

        fileName, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)")
        if fileName:
            try:
                json_obj = graph_to_json(self.graph_widget.graph)
                with open(fileName, 'w') as f:
                    json.dump(json_obj, f, indent=2)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
