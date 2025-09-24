import sys
import json
import networkx as nx
from PyQt6.QtWidgets import QWidget, QInputDialog, QMenu
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QTransform
from PyQt6.QtCore import Qt, QPointF, QRectF

# Import the recursive add function from the parser module
from json_parser import _add_node_recursive

class GraphWidget(QWidget):
    def __init__(self, graph=None):
        super().__init__()
        self.graph = None
        self.pos = None
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self.last_pan_pos = QPointF(0, 0)
        self.selected_node = None
        self.setMinimumSize(600, 400)
        self.set_graph(graph)

    def set_graph(self, graph):
        self.graph = graph
        self.selected_node = None
        self.update_layout()

    def update_layout(self):
        if self.graph is not None and len(self.graph) > 0:
            try:
                # Use graphviz for a hierarchical layout if available
                self.pos = nx.nx_pydot.graphviz_layout(self.graph, prog='dot')
            except Exception:
                # Fallback to spring layout
                self.pos = nx.spring_layout(self.graph, pos=self.pos, seed=42, iterations=50)
        else:
            self.pos = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.graph or not self.pos:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setTransform(self.get_world_transform())

        # Draw edges
        for edge in self.graph.edges(data=True):
            p1, p2 = self.pos[edge[0]], self.pos[edge[1]]
            painter.setPen(QPen(QColor("#a0a0a0"), 1.5))
            painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))
            if 'label' in edge[2]:
                painter.drawText((QPointF(p1[0], p1[1]) + QPointF(p2[0], p2[1])) / 2, edge[2]['label'])

        # Draw nodes
        for node, data in self.graph.nodes(data=True):
            p = self.pos[node]
            rect = self.get_node_rect(p, data['label'])
            painter.setBrush(QBrush(self.get_node_color(data['type'])))
            pen = QPen(QColor("red"), 3) if node == self.selected_node else QPen(Qt.GlobalColor.black, 1)
            painter.setPen(pen)
            painter.drawEllipse(rect)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, data['label'])

    def get_node_rect(self, pos, label):
        width = len(str(label)) * 7 + 20
        height = 30
        return QRectF(pos[0] - width / 2, pos[1] - height / 2, width, height)

    def get_node_color(self, t):
        colors = {'object': QColor("#a1c4fd"), 'array': QColor("#b2f2bb"), 'string': QColor("#fde2a3"),
                  'number': QColor("#f4b678"), 'boolean': QColor("#ffab91"), 'null': QColor("#e6e6e6")}
        return colors.get(t, QColor("#cccccc"))

    def get_world_transform(self):
        transform = QTransform()
        transform.translate(self.pan_offset.x(), self.pan_offset.y())
        transform.scale(self.zoom_factor, self.zoom_factor)
        return transform

    def get_node_at(self, pos):
        if not self.pos: return None
        transform, _ = self.get_world_transform().inverted()
        graph_pos = transform.map(pos)
        for node, p in self.pos.items():
            rect = self.get_node_rect(p, self.graph.nodes[node]['label'])
            if rect.contains(QPointF(graph_pos)):
                return node
        return None

    def contextMenuEvent(self, event):
        node_id = self.get_node_at(event.pos())
        if node_id is None: return

        menu = QMenu(self)
        node_type = self.graph.nodes[node_id].get('type')

        if node_type in ['object', 'array']:
            add_action = menu.addAction("Add...")
            add_action.triggered.connect(lambda: self.add_node(node_id))

        if self.graph.in_degree(node_id) > 0:
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self.delete_node(node_id))

        if menu.actions():
            menu.exec(event.globalPos())

    def add_node(self, parent_id):
        parent_type = self.graph.nodes[parent_id].get('type')
        key = None
        if parent_type == 'object':
            key, ok = QInputDialog.getText(self, "Add Key-Value Pair", "Enter key for new value:")
            if not ok or not key: return
        elif parent_type == 'array':
            key = str(len(list(self.graph.successors(parent_id))))

        value_str, ok = QInputDialog.getText(self, "Add Value", "Enter value (in JSON format):")
        if not ok: return

        try: value = json.loads(value_str)
        except json.JSONDecodeError: value = value_str

        _add_node_recursive(self.graph, value, parent_id, key)
        self.update_layout()

    def delete_node(self, node_id):
        if self.graph.has_node(node_id):
            descendants = list(nx.descendants(self.graph, node_id))
            self.graph.remove_nodes_from(descendants + [node_id])
            if self.selected_node in descendants + [node_id]:
                self.selected_node = None
            self.update_layout()

    def wheelEvent(self, e):
        factor = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.zoom_factor *= factor
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.selected_node = self.get_node_at(e.position())
            self.update()
        self.last_pan_pos = e.position()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton and self.selected_node is None:
            self.pan_offset += e.position() - self.last_pan_pos
            self.last_pan_pos = e.position()
            self.update()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            node_id = self.get_node_at(e.position())
            if node_id is not None: self.edit_node_value(node_id)

    def edit_node_value(self, node_id):
        node_data = self.graph.nodes[node_id]
        node_type = node_data.get('type')
        current_value = node_data.get('value')

        ok = False
        new_value = None

        if node_type == 'string':
            new_value, ok = QInputDialog.getText(self, "Edit String", "Value:", text=str(current_value))
        elif node_type == 'number':
            new_value, ok = QInputDialog.getDouble(self, "Edit Number", "Value:", value=float(current_value or 0))
        elif node_type == 'boolean':
            items = ["True", "False"]
            item, ok = QInputDialog.getItem(self, "Edit Boolean", "Value:", items, 0 if current_value else 1, False)
            if ok: new_value = (item == "True")

        if ok and new_value is not None:
            self.graph.nodes[node_id]['value'] = new_value
            label = f'"{new_value}"' if isinstance(new_value, str) else str(new_value)
            if isinstance(new_value, bool): label = str(new_value)
            self.graph.nodes[node_id]['label'] = label
            self.update_layout()
