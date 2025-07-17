import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QListWidget, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsObject, QGraphicsSimpleTextItem, QStackedWidget, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import QTimer, Qt, QRectF, QPropertyAnimation, QPointF, pyqtProperty, QEasingCurve, QLineF
from PyQt5.QtGui import QColor, QBrush, QPen, QFont, QPainter, QPolygonF
import sip
from typing import Optional
import weakref

# Linked list node data structure for logic
class LLNode:
    def __init__(self, value):
        self.value = value
        self.next: Optional['LLNode'] = None

# Doubly linked list node data structure for logic
class DLLNode:
    def __init__(self, value):
        self.value = value
        self.next: Optional['DLLNode'] = None
        self.prev: Optional['DLLNode'] = None

# Modern color palette
PRIMARY_BG = "#18181b"
CARD_BG = "#23232a"
ACCENT = "#ff1744"  # Neon red
NODE_COLOR = QColor(255, 60, 80)  # Neon red for nodes
ARROW_COLOR = QColor(255, 60, 80)  # Neon red for arrows
HIGHLIGHT_COLOR = QColor(255, 255, 255)  # White highlight
TEXT_COLOR = "#fff"
SUBTEXT_COLOR = "#ff1744"

# --- Box/Node Size and Spacing Constants ---
BOX_WIDTH = 60
BOX_HEIGHT = 60
BOX_SPACING = 30
LL_NODE_STEP = BOX_WIDTH + BOX_SPACING  # For linked list, keep same as array for consistency
# For stack (bookshelf), use wider and shorter boxes
STACK_BOX_WIDTH = 140
STACK_BOX_HEIGHT = 36
STACK_BOX_SPACING = 18

class BaseBox(QGraphicsObject):
    """Base class for all box-like graphics objects"""
    def __init__(self, value, color=QColor(240,240,240)):
        super().__init__()
        self.value = value
        self._pos = QPointF(0, 0)
        self.rect = QRectF(0, 0, BOX_WIDTH, BOX_HEIGHT)
        self.color = color
        self.default_color = color
        self.text = str(value)
        self.setZValue(1)

    def boundingRect(self):
        return self.rect.adjusted(-2, -2, 2, 22)

    def paint(self, painter, option, widget=None):
        if painter is None:
            return
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRoundedRect(self.rect, 10, 10)
        painter.setFont(QFont('Arial', 18, QFont.Bold))
        painter.setPen(QPen(Qt.black))
        painter.drawText(self.rect, Qt.AlignCenter, self.text)

    def set_value(self, value):
        self.value = value
        self.text = str(value)
        self.update()

    def set_box_color(self, color):
        self.color = color
        self.update()

    def reset_color(self):
        self.color = self.default_color
        self.update()

    def get_pos(self):
        return self._pos

    def set_pos(self, pos):
        self._pos = pos
        self.setPos(pos)

    pos = pyqtProperty(QPointF, fget=get_pos, fset=set_pos)

class ArrayBox(BaseBox):
    def __init__(self, value, index, color=QColor(240,240,240)):
        super().__init__(value, color)
        self.index = index
        self.index_text = f'[{index}]'

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if painter is None:
            return
        painter.setFont(QFont('Arial', 10))
        painter.setPen(QPen(Qt.darkGray))
        painter.drawText(0, 60, 60, 20, Qt.AlignCenter, self.index_text)

    def set_index(self, index):
        self.index = index
        self.index_text = f'[{index}]'
        self.update()

class ArrayScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 800, 250)
        self.boxes = []
        self.spacing = BOX_SPACING
        self.box_w = BOX_WIDTH
        self.box_h = BOX_HEIGHT
        self.animations = []
        self.lines = []

    def clear_scene(self):
        for box in self.boxes:
            self.removeItem(box)
        self.boxes = []
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        self.clear()

    def layout_boxes(self, animate=True):
        n = len(self.boxes)
        total_width = n * self.box_w + (n-1) * self.spacing if n > 0 else 0
        # Expand scene rect to fit all boxes (min width 800)
        scene_width = max(800, total_width + 40)
        self.setSceneRect(0, 0, scene_width, 250)
        start_x = max(20, (scene_width - total_width) // 2)
        y = 80
        for i, box in enumerate(self.boxes):
            box.set_index(i)
            target = QPointF(start_x + i * (self.box_w + self.spacing), y)
            if animate:
                anim = QPropertyAnimation(box, b'pos')
                anim.setDuration(900)
                anim.setEasingCurve(QEasingCurve.InOutCubic)
                anim.setEndValue(target)
                anim.start()
                self.animations.append(anim)
            else:
                box.set_pos(target)
        # Draw lines after animations complete
        QTimer.singleShot(950, self.update_lines)

    def update_lines(self):
        # Remove old lines
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        # Draw new lines
        for i in range(1, len(self.boxes)):
            prev_box = self.boxes[i-1]
            curr_box = self.boxes[i]
            # Draw from center-right of prev_box to center-left of curr_box
            x1 = prev_box.pos.x() + self.box_w
            y1 = prev_box.pos.y() + self.box_h / 2
            x2 = curr_box.pos.x()
            y2 = curr_box.pos.y() + self.box_h / 2
            line = self.addLine(x1, y1, x2, y2, QPen(ARROW_COLOR, 3))
            if line:
                line.setZValue(0)
            self.lines.append(line)

    def set_values(self, values, animate=True):
        # Only add/remove boxes as needed, and animate movement
        # Update existing boxes
        n = len(values)
        # Remove extra boxes
        while len(self.boxes) > n:
            box = self.boxes.pop()
            self.removeItem(box)
        # Add new boxes if needed
        while len(self.boxes) < n:
            box = ArrayBox(values[len(self.boxes)], len(self.boxes))
            self.addItem(box)
            self.boxes.append(box)
        # Update values and animate movement
        for i, v in enumerate(values):
            self.boxes[i].set_value(v)
        self.layout_boxes(animate=animate)

    def add_box(self, value, index, color=QColor(240,240,240)):
        box = ArrayBox(value, index, color)
        self.addItem(box)
        self.boxes.insert(index, box)
        self.layout_boxes()
        return box

    def remove_box(self, index):
        box = self.boxes.pop(index)
        anim = QPropertyAnimation(box, b'opacity')
        anim.setDuration(500)
        anim.setEndValue(0)
        anim.start()
        self.animations.append(anim)
        QTimer.singleShot(500, lambda: self.removeItem(box))
        self.layout_boxes()

    def swap_boxes(self, idx1, idx2):
        self.boxes[idx1], self.boxes[idx2] = self.boxes[idx2], self.boxes[idx1]
        self.layout_boxes()

    def set_box_color(self, index, color):
        if 0 <= index < len(self.boxes):
            self.boxes[index].set_box_color(color)

    def reset_all_colors(self):
        for box in self.boxes:
            box.reset_color()

    def animate_swap(self, idx1, idx2, callback=None, after_anim1=None, after_anim2=None):
        if idx1 == idx2 or idx1 < 0 or idx2 < 0 or idx1 >= len(self.boxes) or idx2 >= len(self.boxes):
            if callback:
                callback()
            return
        box1 = self.boxes[idx1]
        box2 = self.boxes[idx2]
        # Calculate temp position above the array
        temp_y = box1.pos.y() - 80
        temp_pos = QPointF(box1.pos.x(), temp_y)
        duration = 1800
        # Step 1: Move box1 to temp
        anim1 = QPropertyAnimation(box1, b'pos')
        anim1.setDuration(duration)
        anim1.setEndValue(temp_pos)
        anim1.setEasingCurve(QEasingCurve.InOutCubic)
        # Step 2: Move box2 to box1's original position
        anim2 = QPropertyAnimation(box2, b'pos')
        anim2.setDuration(duration)
        anim2.setEndValue(box1.pos)
        anim2.setEasingCurve(QEasingCurve.InOutCubic)
        # Step 3: Move box1 (in temp) to box2's original position
        anim3 = QPropertyAnimation(box1, b'pos')
        anim3.setDuration(duration)
        anim3.setEndValue(box2.pos)
        anim3.setEasingCurve(QEasingCurve.InOutCubic)
        # Animation chaining
        def after_anim1_local():
            if after_anim1:
                after_anim1()
            anim2.start()
            anim2.finished.connect(after_anim2_local)
        def after_anim2_local():
            if after_anim2:
                after_anim2()
            anim3.start()
            anim3.finished.connect(after_anim3)
        def after_anim3():
            # Swap in the boxes list
            self.boxes[idx1], self.boxes[idx2] = self.boxes[idx2], self.boxes[idx1]
            self.boxes[idx1].set_index(idx1)
            self.boxes[idx2].set_index(idx2)
            self.update_lines()
            if callback:
                callback()
        anim1.finished.connect(after_anim1_local)
        anim1.start()
        # Highlight both boxes
        box1.set_box_color(QColor(255, 215, 0))
        box2.set_box_color(QColor(255, 215, 0))
        # After all, reset color
        def reset_colors():
            box1.reset_color()
            box2.reset_color()
        anim3.finished.connect(reset_colors)

    def show_temp_box(self, value, pos):
        temp_box = ArrayBox(value, -1, QColor(255, 255, 180))
        temp_box.setPos(pos)
        temp_box.setZValue(2)
        self.addItem(temp_box)
        # Add a label 'temp' below the box
        label = QGraphicsSimpleTextItem('temp')
        label.setFont(QFont('Arial', 14, QFont.Bold))
        label.setPos(pos.x() + 10, pos.y() + 65)
        label.setZValue(2)
        self.addItem(label)
        return temp_box, label

    def remove_temp_box(self, temp_box, label):
        self.removeItem(temp_box)
        self.removeItem(label)

class ArrayVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self._stopped = False
        self.animations_enabled = True
        self.array = []
        self.scene = ArrayScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet('background: #f8f8ff; border: none;')
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setHorizontalScrollBarPolicy(1)  # Qt.ScrollBarAlwaysOn
        self.view.setVerticalScrollBarPolicy(0)    # Qt.ScrollBarAlwaysOff
        self.feedback = QLabel('')
        self.feedback.setStyleSheet('font-size: 16px; color: #333; margin: 8px;')
        self.steps = []
        self.current_step = 0
        self.step_explanation = QLabel('')
        self.step_explanation.setStyleSheet('font-size: 20px; color: #222; background: #e0e7ef; border-radius: 8px; padding: 12px; margin: 12px; font-family: Arial, Helvetica, sans-serif;')
        self.animating = False
        self.btn_next_step = QPushButton('Next Step')
        self.btn_next_step.clicked.connect(self.next_step)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        title = QLabel('Array Visualizer')
        title.setStyleSheet('font-size: 22px; font-weight: bold; margin: 8px;')
        main_layout.addWidget(title)
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.feedback)
        main_layout.addWidget(self.step_explanation)
        main_layout.addWidget(self.btn_next_step)
        main_layout.addStretch(1)
        btn_layout = QHBoxLayout()
        self.btn_random = QPushButton('Random Array')
        self.btn_random.clicked.connect(self.generate_random_array)
        btn_layout.addWidget(self.btn_random)
        self.btn_create = QPushButton('Create Your Own')
        self.btn_create.clicked.connect(self.create_own_array)
        btn_layout.addWidget(self.btn_create)
        self.btn_add = QPushButton('Add Number')
        self.btn_add.clicked.connect(self.add_number)
        btn_layout.addWidget(self.btn_add)
        self.btn_insert = QPushButton('Insert at Index')
        self.btn_insert.clicked.connect(self.insert_at_index)
        btn_layout.addWidget(self.btn_insert)
        self.btn_remove = QPushButton('Remove Number')
        self.btn_remove.clicked.connect(self.remove_number)
        btn_layout.addWidget(self.btn_remove)
        self.btn_swap = QPushButton('Swap Elements')
        self.btn_swap.clicked.connect(self.swap_elements)
        btn_layout.addWidget(self.btn_swap)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setMinimumHeight(350)
        self.setMinimumWidth(800)
        self.step_explanation.setVisible(True)
        self.btn_next_step.setVisible(False)

    def show_feedback(self, text):
        self.feedback.setText(text)
        QTimer.singleShot(1200, lambda: self.feedback.setText(''))

    def play_steps(self, steps, finalize_callback=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self._play_next_step(finalize_callback)

    def _play_next_step(self, finalize_callback=None):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        if callable(step):
            step()
            self.current_step += 1
            QTimer.singleShot(3500, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])
        else:
            arr, highlight, explanation = step
            self.scene.set_values(arr)
            self.scene.reset_all_colors()
            for idx in highlight:
                self.scene.set_box_color(idx, QColor(255, 215, 0))
            if not sip.isdeleted(self.step_explanation):
                self.step_explanation.setText(explanation)
            self.feedback.setText('')
            self.current_step += 1
            QTimer.singleShot(3500, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])

    def generate_random_array(self):
        self.array = [random.randint(0, 99) for _ in range(random.randint(5, 10))]
        self.scene.set_values(self.array)
        self.show_feedback('Random array generated.')
        self.step_explanation.setText('')

    def create_own_array(self):
        text, ok = QInputDialog.getText(self, 'Create Array', 'Enter numbers separated by commas:')
        if ok:
            try:
                nums = [int(x.strip()) for x in text.split(',') if x.strip()]
                self.array = nums
                self.scene.set_values(self.array)
                self.show_feedback('Custom array created.')
                self.step_explanation.setText('')
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter only numbers separated by commas.')

    def set_animations_enabled(self, enabled):
        self.animations_enabled = enabled

    def add_number(self):
        num, ok = QInputDialog.getInt(self, 'Add Number', 'Enter a number to add:')
        if ok:
            if not self.animations_enabled:
                self.array.append(num)
                self.scene.set_values(self.array, animate=False)
                self.show_feedback(f'Added {num} to the end.')
                self.step_explanation.setText('')
                return
            steps = []
            arr = self.array.copy()
            steps.append((arr.copy(), [], f"Step 1: Current array."))
            arr.append(num)
            steps.append((arr.copy(), [len(arr)-1], f"Step 2: Add {num} to the end."))
            steps.append((arr.copy(), [], f"Step 3: Done. Array after adding {num}.") )
            def finalize():
                if sip.isdeleted(self):
                    return
                self.array.append(num)
                self.scene.set_values(self.array)
                self.show_feedback(f'Added {num} to the end.')
            self.play_steps(steps, finalize)

    def insert_at_index(self):
        if len(self.array) == 0:
            idx = 0
        else:
            idx, ok = QInputDialog.getInt(self, 'Insert at Index', f'Enter index (0 to {len(self.array)}):', min=0, max=len(self.array))
            if not ok:
                return
        num, ok = QInputDialog.getInt(self, 'Insert at Index', 'Enter a number to insert:')
        if ok:
            if not self.animations_enabled:
                self.array.insert(idx, num)
                self.scene.set_values(self.array, animate=False)
                self.show_feedback(f'Inserted {num} at index {idx}.')
                self.step_explanation.setText('')
                self.scene.reset_all_colors()
                return
            arr = self.array.copy()
            steps = []
            steps.append((arr.copy(), [idx], f"Step 1: Highlight index {idx} for insertion."))
            arr2 = arr.copy()
            arr2.append(0)
            steps.append((arr2.copy(), [len(arr2)-1], f"Step 2: Create space at the end for shifting."))
            for i in range(len(arr), idx, -1):
                arr2[i] = arr2[i-1]
                steps.append((arr2.copy(), [i], f"Step {len(steps)+1}: Shift value {arr2[i]} from index {i-1} to {i}."))
            arr2[idx] = num
            steps.append((arr2.copy(), [idx], f"Step {len(steps)+1}: Insert {num} at index {idx}."))
            steps.append((arr2.copy(), [], f"Step {len(steps)+1}: Done. Array after insertion."))
            def finalize():
                if sip.isdeleted(self):
                    return
                self.array.insert(idx, num)
                self.scene.set_values(self.array)
                self.show_feedback(f'Inserted {num} at index {idx}.')
                self.scene.reset_all_colors()
            self.play_steps(steps, finalize)

    def remove_number(self):
        if not self.array:
            QMessageBox.warning(self, 'Empty Array', 'Array is already empty!')
            return
        idx, ok = QInputDialog.getInt(self, 'Remove Number', f'Enter index to remove (0 to {len(self.array)-1}):', min=0, max=max(0, len(self.array)-1))
        if ok:
            if not self.animations_enabled:
                self.array.pop(idx)
                self.scene.set_values(self.array, animate=False)
                self.show_feedback(f'Element at index {idx} removed.')
                self.step_explanation.setText('')
                self.scene.reset_all_colors()
                return
            arr = self.array.copy()
            steps = []
            steps.append((arr.copy(), [idx], f"Step 1: Highlight index {idx} to remove ({arr[idx]})."))
            for i in range(idx, len(arr)-1):
                arr[i] = arr[i+1]
                steps.append((arr.copy(), [i], f"Step {len(steps)+1}: Move value {arr[i]} from index {i+1} to {i}."))
            arr2 = arr[:-1]
            steps.append((arr2.copy(), [], f"Step {len(steps)+1}: Remove last element (array shrinks)."))
            steps.append((arr2.copy(), [], f"Step {len(steps)+1}: Done. Array after removal."))
            def finalize():
                if sip.isdeleted(self):
                    return
                self.array = arr2
                self.scene.set_values(self.array)
                self.show_feedback(f'Element at index {idx} removed.')
                self.scene.reset_all_colors()
            self.play_steps(steps, finalize)

    def swap_elements(self):
        if len(self.array) < 2:
            QMessageBox.warning(self, 'Too Small', 'Need at least 2 elements to swap.')
            return
        idx1, ok1 = QInputDialog.getInt(self, 'Swap Elements', f'First index (0 to {len(self.array)-1}):', min=0, max=len(self.array)-1)
        if not ok1:
            return
        idx2, ok2 = QInputDialog.getInt(self, 'Swap Elements', f'Second index (0 to {len(self.array)-1}):', min=0, max=len(self.array)-1)
        if not ok2:
            return
        if idx1 == idx2:
            QMessageBox.warning(self, 'Invalid', 'Indices must be different.')
            return
        if not self.animations_enabled:
            self.array[idx1], self.array[idx2] = self.array[idx2], self.array[idx1]
            self.scene.set_values(self.array, animate=False)
            self.show_feedback(f'Swapped index {idx1} and {idx2}.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        arr = self.array.copy()
        steps = []
        steps.append((arr.copy(), [idx1, idx2], f"Step 1: Highlight indices {idx1} and {idx2} to swap."))
        steps.append((arr.copy(), [idx1], f"Step 2: Store value {arr[idx1]} from index {idx1} in temp variable."))
        arr[idx1] = arr[idx2]
        steps.append((arr.copy(), [idx1, idx2], f"Step 3: Assign value from index {idx2} ({arr[idx2]}) to index {idx1}."))
        arr[idx2] = arr[idx1]
        steps.append((arr.copy(), [idx2], f"Step 4: Assign temp value ({arr[idx2]}) to index {idx2}."))
        steps.append((arr.copy(), [], f"Step 5: Done. Array after swap."))
        def finalize():
            if sip.isdeleted(self):
                return
            self.array[idx1], self.array[idx2] = self.array[idx2], self.array[idx1]
            self.scene.set_values(self.array)
            self.show_feedback(f'Swapped index {idx1} and {idx2}.')
            self.scene.reset_all_colors()
        self.play_steps_auto_with_temp(steps, finalize, delay=2500, temp_value=arr[idx1], temp_steps=[1, 2, 3])

    def play_steps_auto_with_temp(self, steps, finalize_callback=None, delay=2500, temp_value=None, temp_steps=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self.temp_value = temp_value
        self.temp_steps = temp_steps or []
        self.temp_box = None
        self.temp_label = None
        self._play_next_step_auto_with_temp(finalize_callback, delay)

    def _play_next_step_auto_with_temp(self, finalize_callback=None, delay=2500):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if self.temp_box and self.temp_label:
                self.scene.remove_temp_box(self.temp_box, self.temp_label)
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        arr, highlight, explanation = step
        if self.current_step in self.temp_steps:
            if self.temp_box is None:
                # Create temp box to the right of the array
                n = len(arr)
                total_width = n * BOX_WIDTH + (n-1) * BOX_SPACING
                start_x = max(20, (800 - total_width) // 2)
                temp_x = start_x + total_width + BOX_SPACING * 2  # Position to the right with extra spacing
                temp_y = 80  # Same y-level as the array
                temp_pos = QPointF(temp_x, temp_y)
                self.temp_box, self.temp_label = self.scene.show_temp_box(self.temp_value, temp_pos)
                # Style the temp label with better formatting
                self.temp_label.setFont(QFont('Arial', 12, QFont.Bold))
                self.temp_label.setBrush(QBrush(QColor(255, 60, 80)))  # Use accent color
        else:
            # Remove temp box if it exists
            if self.temp_box and self.temp_label:
                self.scene.remove_temp_box(self.temp_box, self.temp_label)
                self.temp_box = None
                self.temp_label = None
        
        self.scene.set_values(arr)
        # Reset all colors first, then highlight only the relevant ones
        self.scene.reset_all_colors()
        for idx in highlight:
            self.scene.set_box_color(idx, QColor(255, 215, 0))
        if not sip.isdeleted(self.step_explanation):
            self.step_explanation.setText(explanation)
        self.feedback.setText('')
        self.current_step += 1
        QTimer.singleShot(delay, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step_auto_with_temp(finalize_callback, delay), None)[-1])

    def next_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if callable(step):
                step()
            else:
                arr, highlight, explanation = step
                self.scene.set_values(arr)
                for idx in highlight:
                    self.scene.set_box_color(idx, QColor(255, 215, 0))
                self.step_explanation.setText(explanation)
                self.feedback.setText('')
            self.current_step += 1
        if self.current_step >= len(self.steps):
            self.btn_next_step.setVisible(False)

    def stop_animations(self):
        self._stopped = True
        self.animating = False
        self.steps = []
        self.current_step = 0
        self.temp_box = None
        self.temp_label = None
        if hasattr(self.scene, 'animations'):
            for anim in self.scene.animations:
                anim.stop()
            self.scene.animations.clear()

class LinkedListNodeBox(BaseBox):
    def __init__(self, value, color=QColor(200,240,255)):
        super().__init__(value, color)
        self.index_label = None
        self.next_node: Optional['LinkedListNodeBox'] = None

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if painter is None:
            return
        painter.setFont(QFont('Arial', 10))
        painter.setPen(QPen(Qt.darkGray))
        if self.index_label is not None:
            painter.drawText(0, 60, 60, 20, Qt.AlignCenter, f'[{self.index_label}]')

    def set_index_label(self, index):
        self.index_label = index
        self.update()

class LinkedListScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 250)
        self.nodes = []
        self.animations = []
        self.lines = []
        self.arrows = []
        self.head_label = None

    def clear_scene(self):
        for node in self.nodes:
            self.removeItem(node)
        self.nodes = []
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        for arrow in self.arrows:
            self.removeItem(arrow)
        self.arrows = []
        if self.head_label:
            self.removeItem(self.head_label)
            self.head_label = None
        self.clear()

    def layout_nodes(self):
        n = len(self.nodes)
        node_spacing = BOX_WIDTH + BOX_SPACING
        total_width = n * BOX_WIDTH + (n-1) * node_spacing if n > 0 else 0
        # Expand scene rect to fit all nodes (min width 900)
        scene_width = max(900, total_width + 40)
        self.setSceneRect(0, 0, scene_width, 250)
        start_x = max(20, (scene_width - total_width) // 2)
        y = 80
        for i, node in enumerate(self.nodes):
            node.set_index_label(i)
            target = QPointF(start_x + i * (BOX_WIDTH + node_spacing), y)
            anim = QPropertyAnimation(node, b'pos')
            anim.setDuration(900)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.setEndValue(target)
            anim.finished.connect(self.update_arrows)
            anim.start()
            self.animations.append(anim)
        if n > 0 and self.head_label:
            head_x = start_x + BOX_WIDTH // 2 - 20
            self.head_label.setPos(head_x, y - 30)
        QTimer.singleShot(950, self.update_arrows)

    def update_lines(self):
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        for i in range(len(self.nodes)-1):
            n1 = self.nodes[i]
            n2 = self.nodes[i+1]
            # Draw from center-right of n1 to center-left of n2
            x1 = n1.pos.x() + BOX_WIDTH
            y1 = n1.pos.y() + BOX_HEIGHT / 2
            x2 = n2.pos.x()
            y2 = n2.pos.y() + BOX_HEIGHT / 2
            line = self.addLine(x1, y1, x2, y2, QPen(ARROW_COLOR, 3))
            if line:
                line.setZValue(0)
            self.lines.append(line)

    def set_from_head(self, head, animate=True):
        # Only add/remove nodes as needed, and animate movement
        # Update existing nodes
        n = 0
        node = head
        while node:
            n += 1
            node = node.next
        
        # Remove extra nodes
        while len(self.nodes) > n:
            node = self.nodes.pop()
            self.removeItem(node)
        
        # Add new nodes if needed
        node = head
        i = 0
        prev_box = None
        while node:
            if i >= len(self.nodes):
                box = LinkedListNodeBox(node.value)
                box.set_index_label(i)
                self.addItem(box)
                self.nodes.append(box)
            else:
                # Update existing node
                self.nodes[i].set_value(node.value)
                self.nodes[i].set_index_label(i)
            
            if prev_box is not None:
                prev_box.next_node = self.nodes[i]
            prev_box = self.nodes[i]
            node = node.next
            i += 1
        
        # Create or update head label
        if n > 0:
            if self.head_label is None:
                self.head_label = QGraphicsSimpleTextItem('head')
                self.head_label.setFont(QFont('Arial', 14, QFont.Bold))
                self.head_label.setBrush(QBrush(QColor(255, 60, 80)))  # Use accent color
                self.addItem(self.head_label)
        
        if animate:
            self.layout_nodes()
        else:
            # Set positions without animation
            node_spacing = BOX_WIDTH + BOX_SPACING  # Restore reasonable spacing
            total_width = n * BOX_WIDTH + (n-1) * node_spacing if n > 0 else 0
            start_x = max(20, (900 - total_width) // 2)
            y = 80
            for i, node in enumerate(self.nodes):
                node.set_index_label(i)
                target = QPointF(start_x + i * (BOX_WIDTH + node_spacing), y)
                node.set_pos(target)
            
            # Position head label
            if n > 0 and self.head_label:
                head_x = start_x + BOX_WIDTH // 2 - 20
                self.head_label.setPos(head_x, y - 30)
            
            # Update arrows immediately since no animation
            self.update_arrows()

    def set_box_color(self, index, color):
        if 0 <= index < len(self.nodes):
            self.nodes[index].set_box_color(color)

    def reset_all_colors(self):
        for node in self.nodes:
            node.reset_color()

    def update_arrows(self):
        for arrow in self.arrows:
            self.removeItem(arrow)
        self.arrows = []
        for i in range(len(self.nodes)-1):
            n1 = self.nodes[i]
            n2 = self.nodes[i+1]
            # Draw from center-right of n1 to center-left of n2
            x1 = n1.pos.x() + BOX_WIDTH
            y1 = n1.pos.y() + BOX_HEIGHT / 2
            x2 = n2.pos.x()
            y2 = n2.pos.y() + BOX_HEIGHT / 2
            line = self.addLine(x1, y1, x2, y2, QPen(ARROW_COLOR, 4, Qt.SolidLine, Qt.RoundCap))
            if line:
                line.setZValue(0)
            self.arrows.append(line)
            # Arrowhead
            arrow_size = 14
            arrow_p1 = QPointF(x2, y2) + QPointF(-arrow_size * 0.7, -arrow_size * 0.5)
            arrow_p2 = QPointF(x2, y2) + QPointF(-arrow_size * 0.7, arrow_size * 0.5)
            arrow_head = QPolygonF([QPointF(x2, y2), arrow_p1, arrow_p2])
            arrow_item = self.addPolygon(arrow_head, QPen(ARROW_COLOR), QBrush(ARROW_COLOR))
            if arrow_item:
                arrow_item.setZValue(1)
            self.arrows.append(arrow_item)
        # Draw prev arrows (left)
        for i, node in enumerate(self.nodes):
            if node.prev_node is not None:
                n1 = node
                n2 = node.prev_node
                x1 = n1.pos.x()
                y1 = n1.pos.y() + BOX_HEIGHT / 2
                x2 = n2.pos.x() + BOX_WIDTH
                y2 = n2.pos.y() + BOX_HEIGHT / 2
                line = self.addLine(x1, y1, x2, y2, QPen(QColor(80, 180, 255), 3, Qt.DashLine))
                if line:
                    line.setZValue(0)
                self.arrows.append(line)
                # Arrowhead
                arrow_size = 12
                arrow_p1 = QPointF(x2, y2) + QPointF(arrow_size * 0.7, -arrow_size * 0.5)
                arrow_p2 = QPointF(x2, y2) + QPointF(arrow_size * 0.7, arrow_size * 0.5)
                arrow_head = QPolygonF([QPointF(x2, y2), arrow_p1, arrow_p2])
                arrow_item = self.addPolygon(arrow_head, QPen(QColor(80, 180, 255)), QBrush(QColor(80, 180, 255)))
            if arrow_item:
                arrow_item.setZValue(1)
            self.arrows.append(arrow_item)

class LinkedListVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self._stopped = False
        self.animations_enabled = True
        self.head = None  # Head node of the linked list
        self.scene = LinkedListScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet('background: #f8f8ff; border: none;')
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setHorizontalScrollBarPolicy(1)  # Qt.ScrollBarAlwaysOn
        self.view.setVerticalScrollBarPolicy(0)    # Qt.ScrollBarAlwaysOff
        self.feedback = QLabel('')
        self.feedback.setStyleSheet('font-size: 16px; color: #333; margin: 8px;')
        self.steps = []
        self.current_step = 0
        self.step_explanation = QLabel('')
        self.step_explanation.setStyleSheet('font-size: 20px; color: #222; background: #e0e7ef; border-radius: 8px; padding: 12px; margin: 12px; font-family: Arial, Helvetica, sans-serif;')
        self.btn_next_step = QPushButton('Next Step')
        self.btn_next_step.clicked.connect(self.next_step)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        title = QLabel('Linked List Visualizer')
        title.setStyleSheet('font-size: 22px; font-weight: bold; margin: 8px;')
        main_layout.addWidget(title)
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.feedback)
        main_layout.addWidget(self.step_explanation)
        main_layout.addWidget(self.btn_next_step)
        main_layout.addStretch(1)
        btn_layout = QHBoxLayout()
        self.btn_random = QPushButton('Random List')
        self.btn_random.clicked.connect(self.generate_random_list)
        btn_layout.addWidget(self.btn_random)
        self.btn_create = QPushButton('Create Your Own')
        self.btn_create.clicked.connect(self.create_own_list)
        btn_layout.addWidget(self.btn_create)
        self.btn_add = QPushButton('Add Node')
        self.btn_add.clicked.connect(self.add_node)
        btn_layout.addWidget(self.btn_add)
        self.btn_insert = QPushButton('Insert at Index')
        self.btn_insert.clicked.connect(self.insert_at_index)
        btn_layout.addWidget(self.btn_insert)
        self.btn_remove = QPushButton('Remove Node')
        self.btn_remove.clicked.connect(self.remove_node)
        btn_layout.addWidget(self.btn_remove)
        self.btn_swap = QPushButton('Swap Nodes')
        self.btn_swap.clicked.connect(self.swap_nodes)
        btn_layout.addWidget(self.btn_swap)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setMinimumHeight(350)
        self.setMinimumWidth(900)
        self.step_explanation.setVisible(True)
        self.btn_next_step.setVisible(False)

    def show_feedback(self, text):
        self.feedback.setText(text)
        QTimer.singleShot(1200, lambda: self.feedback.setText(''))

    def play_steps(self, steps, finalize_callback=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self._play_next_step(finalize_callback)

    def _play_next_step(self, finalize_callback=None):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        if callable(step):
            step()
            self.current_step += 1
            QTimer.singleShot(3500, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])
        else:
            head, highlight, explanation = step
            self.scene.set_from_head(head, animate=True)
            self.scene.reset_all_colors()
            for idx in highlight:
                self.scene.set_box_color(idx, QColor(255, 215, 0))
            if not sip.isdeleted(self.step_explanation):
                self.step_explanation.setText(explanation)
            self.feedback.setText('')
            self.current_step += 1
            QTimer.singleShot(3500, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])

    def to_list(self, head):
        arr = []
        node = head
        while node:
            arr.append(node.value)
            node = node.next
        return arr

    def clone_list(self, head):
        # Returns a new head, and a mapping from old node to new node
        if not head:
            return None, {}
        old_to_new = {}
        new_head = LLNode(head.value)
        old_to_new[head] = new_head
        prev_new = new_head
        prev_old = head
        curr_old = head.next
        while curr_old:
            curr_new = LLNode(curr_old.value)
            old_to_new[curr_old] = curr_new
            prev_new.next = curr_new
            prev_new = curr_new
            prev_old = curr_old
            curr_old = curr_old.next
        return new_head, old_to_new

    def set_head(self, head):
        self.head = head
        self.scene.set_from_head(self.head)

    def generate_random_list(self):
        values = [random.randint(0, 99) for _ in range(random.randint(4, 8))]
        self.head = None
        prev = None
        for v in values:
            node = LLNode(v)
            if self.head is None:
                self.head = node
            if prev:
                prev.next = node
            prev = node
        self.scene.set_from_head(self.head)
        self.show_feedback('Random linked list generated.')
        self.step_explanation.setText('')

    def create_own_list(self):
        text, ok = QInputDialog.getText(self, 'Create Linked List', 'Enter numbers separated by commas:')
        if ok:
            try:
                nums = [int(x.strip()) for x in text.split(',') if x.strip()]
                self.head = None
                prev = None
                for v in nums:
                    node = LLNode(v)
                    if self.head is None:
                        self.head = node
                    if prev:
                        prev.next = node
                    prev = node
                self.scene.set_from_head(self.head)
                self.show_feedback('Custom linked list created.')
                self.step_explanation.setText('')
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter only numbers separated by commas.')

    def set_animations_enabled(self, enabled):
        self.animations_enabled = enabled

    def add_node(self):
        num, ok = QInputDialog.getInt(self, 'Add Node', 'Enter a number to add:')
        if ok:
            if not self.animations_enabled:
                if not self.head:
                    self.head = LLNode(num)
                else:
                    node = self.head
                    while node.next:
                        node = node.next
                    node.next = LLNode(num)
                self.scene.set_from_head(self.head, animate=False)
                self.show_feedback(f'Added {num} to the end.')
                self.step_explanation.setText('')
                return
            # Add to end
            if not self.head:
                self.head = LLNode(num)
            else:
                node = self.head
                while node.next:
                    node = node.next
                node.next = LLNode(num)
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Added {num} to the end.')
            self.step_explanation.setText('')

    def insert_at_index(self):
        idx, ok = QInputDialog.getInt(self, 'Insert at Index', f'Enter index (0 to {self.length()}):', min=0, max=self.length())
        if not ok:
            return
        num, ok = QInputDialog.getInt(self, 'Insert at Index', 'Enter a number to insert:')
        if not ok:
            return
        if not self.animations_enabled:
            if idx == 0:
                new_node = LLNode(num)
                new_node.next = self.head
                if self.head:
                    self.head.prev = new_node
                self.head = new_node
            else:
                curr = self.head
                for i in range(idx - 1):
                    if curr is None:
                        break
                    curr = curr.next
                if curr is not None:
                    new_node = LLNode(num)
                    new_node.next = curr.next
                    new_node.prev = curr
                    if curr.next:
                        curr.next.prev = new_node
                    curr.next = new_node
            self.scene.set_from_head(self.head, animate=False)
            self.show_feedback(f'Inserted {num} at index {idx}.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        # Create a copy of the list for animation
        head_copy, old_to_new = self.clone_list(self.head)
        steps = []
        
        # Step 1: Highlight where to insert
        if idx == 0:
            steps.append((head_copy, [idx], f"Step 1: Highlight position for new head node."))
        else:
            steps.append((head_copy, [idx], f"Step 1: Highlight index {idx} for insertion."))
        
        # Step 2: Traverse to the node before insertion point
        curr = head_copy
        prev = None
        for i in range(idx):
            if curr is None:
                break
            prev = curr
            curr = curr.next
        
        # Step 3: Create new node and update pointers
        new_node = LLNode(num)
        if prev is None:
            # Inserting at head
            new_node.next = head_copy
            new_head = new_node
            steps.append((new_head, [0], f"Step 2: Create new node with value {num} and make it the new head."))
        else:
            # Inserting in middle or end
            new_node.next = curr
            prev.next = new_node
            new_head = head_copy
            steps.append((new_head, [idx], f"Step 2: Create new node with value {num} and update pointers."))
        
        steps.append((new_head, [], f"Step 3: Done. List after insertion."))
        
        def finalize():
            if sip.isdeleted(self):
                return
            # Actually insert in real list
            if idx == 0:
                # Insert at head
                new_node = LLNode(num)
                new_node.next = self.head
                if self.head:
                    self.head.prev = new_node
                self.head = new_node
            else:
                # Insert in middle or end
                curr = self.head
                for i in range(idx - 1):
                    if curr is None:
                        break
                    curr = curr.next
                if curr is not None:
                    new_node = LLNode(num)
                    new_node.next = curr.next
                    new_node.prev = curr
                    if curr.next:
                        curr.next.prev = new_node
                    curr.next = new_node
            
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Inserted {num} at index {idx}.')
            # Reset all colors
            self.scene.reset_all_colors()
        
        self.play_steps(steps, finalize)

    def remove_node(self):
        if not self.head:
            QMessageBox.warning(self, 'Empty List', 'List is already empty!')
            return
        idx, ok = QInputDialog.getInt(self, 'Remove Node', f'Enter index to remove (0 to {self.length()-1}):', min=0, max=max(0, self.length()-1))
        if not ok:
            return
        if not self.animations_enabled:
            if idx == 0:
                if self.head:
                    self.head = self.head.next
            else:
                curr = self.head
                for i in range(idx - 1):
                    if curr is None:
                        break
                    curr = curr.next
                if curr and curr.next:
                    curr.next = curr.next.next
            self.scene.set_from_head(self.head, animate=False)
            self.show_feedback(f'Node at index {idx} removed.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        # Create a copy of the list for animation
        head_copy, old_to_new = self.clone_list(self.head)
        steps = []
        
        # Step 1: Highlight node to remove
        if idx == 0:
            steps.append((head_copy, [idx], f"Step 1: Highlight head node to remove."))
        else:
            steps.append((head_copy, [idx], f"Step 1: Highlight node {idx} to remove."))
        
        # Step 2: Traverse to the node before the one to remove
        curr = head_copy
        prev = None
        for i in range(idx):
            if curr is None:
                break
            prev = curr
            curr = curr.next
        
        # Step 3: Update pointers to skip the removed node
        if prev is None:
            # Removing head
            new_head = curr.next if curr else None
            if new_head:
                steps.append((new_head, [0], f"Step 2: Update head pointer to next node."))
            else:
                steps.append((new_head, [], f"Step 2: List becomes empty (no head)."))
        else:
            # Removing from middle or end
            if curr:
                prev.next = curr.next
            new_head = head_copy
            steps.append((new_head, [idx-1] if prev else [], f"Step 2: Update pointer to skip node {idx}."))
        
        steps.append((new_head, [], f"Step 3: Done. List after removal."))
        
        def finalize():
            if sip.isdeleted(self):
                return
            # Actually remove from real list
            if idx == 0:
                # Remove head
                if self.head:
                    self.head = self.head.next
            else:
                # Remove from middle or end
                curr = self.head
                for i in range(idx - 1):
                    if curr is None:
                        break
                    curr = curr.next
                if curr and curr.next:
                    curr.next = curr.next.next
            
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Node at index {idx} removed.')
            # Reset all colors
            self.scene.reset_all_colors()
        
        self.play_steps(steps, finalize)

    def length(self):
        count = 0
        node = self.head
        while node:
            count += 1
            node = node.next
        return count

    def swap_nodes(self):
        n = self.length()
        if n < 2:
            QMessageBox.warning(self, 'Too Small', 'Need at least 2 nodes to swap.')
            return
        idx1, ok1 = QInputDialog.getInt(self, 'Swap Nodes', f'First index (0 to {n-1}):', min=0, max=n-1)
        if not ok1:
            return
        idx2, ok2 = QInputDialog.getInt(self, 'Swap Nodes', f'Second index (0 to {n-1}):', min=0, max=n-1)
        if not ok2 or idx1 == idx2:
            return
        if not self.animations_enabled:
            if idx1 == idx2:
                return
            node1 = self.head
            prev1 = None
            for _ in range(idx1):
                if node1:
                    prev1 = node1
                    node1 = node1.next
            node2 = self.head
            prev2 = None
            for _ in range(idx2):
                if node2:
                    prev2 = node2
                    node2 = node2.next
            if node1 and node2:
                next1 = node1.next
                next2 = node2.next
                if prev1 is None:
                    self.head = node2
                else:
                    prev1.next = node2
                if prev2 is None:
                    self.head = node1
                else:
                    prev2.next = node1
                if node1 == next2:
                    node1.next = node2
                    node2.next = next1
                elif node2 == next1:
                    node2.next = node1
                    node1.next = next2
                else:
                    node1.next = next2
                    node2.next = next1
            self.scene.set_from_head(self.head, animate=False)
            self.show_feedback(f'Swapped nodes {idx1} and {idx2}.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        arr = self.array.copy()
        steps = []
        steps.append((arr.copy(), [idx1, idx2], f"Step 1: Highlight indices {idx1} and {idx2} to swap."))
        steps.append((arr.copy(), [idx1], f"Step 2: Store value {arr[idx1]} from index {idx1} in temp variable."))
        arr[idx1] = arr[idx2]
        steps.append((arr.copy(), [idx1, idx2], f"Step 3: Assign value from index {idx2} ({arr[idx2]}) to index {idx1}."))
        arr[idx2] = arr[idx1]
        steps.append((arr.copy(), [idx2], f"Step 4: Assign temp value ({arr[idx2]}) to index {idx2}."))
        steps.append((arr.copy(), [], f"Step 5: Done. Array after swap."))
        def finalize():
            if sip.isdeleted(self):
                return
            self.array[idx1], self.array[idx2] = self.array[idx2], self.array[idx1]
            self.scene.set_values(self.array)
            self.show_feedback(f'Swapped index {idx1} and {idx2}.')
            self.scene.reset_all_colors()
        self.play_steps_auto_with_temp(steps, finalize, delay=2500, temp_value=arr[idx1], temp_steps=[1, 2, 3])

    def play_steps_auto_with_temp(self, steps, finalize_callback=None, delay=2500, temp_value=None, temp_steps=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self.temp_value = temp_value
        self.temp_steps = temp_steps or []
        self.temp_box = None
        self.temp_label = None
        self._play_next_step_auto_with_temp(finalize_callback, delay)

    def _play_next_step_auto_with_temp(self, finalize_callback=None, delay=2500):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if self.temp_box and self.temp_label:
                self.scene.remove_temp_box(self.temp_box, self.temp_label)
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        arr, highlight, explanation = step
        if self.current_step in self.temp_steps:
            if self.temp_box is None:
                # Create temp box to the right of the array
                n = len(arr)
                total_width = n * BOX_WIDTH + (n-1) * BOX_SPACING
                start_x = max(20, (800 - total_width) // 2)
                temp_x = start_x + total_width + BOX_SPACING * 2  # Position to the right with extra spacing
                temp_y = 80  # Same y-level as the array
                temp_pos = QPointF(temp_x, temp_y)
                self.temp_box, self.temp_label = self.scene.show_temp_box(self.temp_value, temp_pos)
                # Style the temp label with better formatting
                self.temp_label.setFont(QFont('Arial', 12, QFont.Bold))
                self.temp_label.setBrush(QBrush(QColor(255, 60, 80)))  # Use accent color
        else:
            # Remove temp box if it exists
            if self.temp_box and self.temp_label:
                self.scene.remove_temp_box(self.temp_box, self.temp_label)
                self.temp_box = None
                self.temp_label = None
        
        self.scene.set_values(arr)
        # Reset all colors first, then highlight only the relevant ones
        self.scene.reset_all_colors()
        for idx in highlight:
            self.scene.set_box_color(idx, QColor(255, 215, 0))
        if not sip.isdeleted(self.step_explanation):
            self.step_explanation.setText(explanation)
        self.feedback.setText('')
        self.current_step += 1
        QTimer.singleShot(delay, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step_auto_with_temp(finalize_callback, delay), None)[-1])

    def next_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if callable(step):
                step()
            else:
                head, highlight, explanation = step
                self.scene.set_from_head(head)
                for idx in highlight:
                    self.scene.set_box_color(idx, QColor(255, 215, 0))
                self.step_explanation.setText(explanation)
                self.feedback.setText('')
            self.current_step += 1
        if self.current_step >= len(self.steps):
            self.btn_next_step.setVisible(False)

    def stop_animations(self):
        self._stopped = True
        self.animating = False
        self.steps = []
        self.current_step = 0
        self.temp_box = None
        self.temp_label = None
        if hasattr(self.scene, 'animations'):
            for anim in self.scene.animations:
                anim.stop()
            self.scene.animations.clear()

class DoublyLinkedListNodeBox(BaseBox):
    def __init__(self, value, color=QColor(200,255,200)):
        super().__init__(value, color)
        self.index_label = None
        self.next_node: Optional['DoublyLinkedListNodeBox'] = None
        self.prev_node: Optional['DoublyLinkedListNodeBox'] = None

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if painter is None:
            return
        painter.setFont(QFont('Arial', 10))
        painter.setPen(QPen(Qt.darkGray))
        if self.index_label is not None:
            painter.drawText(0, 60, 60, 20, Qt.AlignCenter, f'[{self.index_label}]')

    def set_index_label(self, index):
        self.index_label = index
        self.update()

# Scene for doubly linked list
class DoublyLinkedListScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 250)
        self.nodes = []
        self.animations = []
        self.lines = []
        self.arrows = []
        self.head_label = None
        self.tail_label = None

    def clear_scene(self):
        for node in self.nodes:
            self.removeItem(node)
        self.nodes = []
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        for arrow in self.arrows:
            self.removeItem(arrow)
        self.arrows = []
        if self.head_label:
            self.removeItem(self.head_label)
            self.head_label = None
        if self.tail_label:
            self.removeItem(self.tail_label)
            self.tail_label = None
        self.clear()

    def layout_nodes(self):
        n = len(self.nodes)
        node_spacing = BOX_WIDTH + BOX_SPACING
        total_width = n * BOX_WIDTH + (n-1) * node_spacing if n > 0 else 0
        scene_width = max(900, total_width + 40)
        self.setSceneRect(0, 0, scene_width, 250)
        start_x = max(20, (scene_width - total_width) // 2)
        y = 80
        for i, node in enumerate(self.nodes):
            node.set_index_label(i)
            target = QPointF(start_x + i * (BOX_WIDTH + node_spacing), y)
            anim = QPropertyAnimation(node, b'pos')
            anim.setDuration(900)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.setEndValue(target)
            anim.finished.connect(self.update_arrows)
            anim.start()
            self.animations.append(anim)
        # Head label
        if n > 0:
            if self.head_label is None:
                self.head_label = QGraphicsSimpleTextItem('head')
                self.head_label.setFont(QFont('Arial', 14, QFont.Bold))
                self.head_label.setBrush(QBrush(QColor(255, 60, 80)))
                self.addItem(self.head_label)
            head_x = start_x + BOX_WIDTH // 2 - 20
            self.head_label.setPos(head_x, y - 30)
            # Tail label
            if self.tail_label is None:
                self.tail_label = QGraphicsSimpleTextItem('tail')
                self.tail_label.setFont(QFont('Arial', 14, QFont.Bold))
                self.tail_label.setBrush(QBrush(QColor(255, 60, 80)))
                self.addItem(self.tail_label)
            tail_x = start_x + (n-1) * (BOX_WIDTH + node_spacing) + BOX_WIDTH // 2 - 20
            self.tail_label.setPos(tail_x, y + BOX_HEIGHT + 10)
        QTimer.singleShot(950, self.update_arrows)

    def set_from_head(self, head, animate=True):
        # Build node list from head
        nodes = []
        node = head
        while node:
            nodes.append(node)
            node = node.next
        n = len(nodes)
        # Remove extra boxes
        while len(self.nodes) > n:
            node = self.nodes.pop()
            self.removeItem(node)
        # Add new boxes if needed
        node = head
        i = 0
        prev_box = None
        while node:
            if i >= len(self.nodes):
                box = DoublyLinkedListNodeBox(node.value)
                box.set_index_label(i)
                self.addItem(box)
                self.nodes.append(box)
            else:
                self.nodes[i].set_value(node.value)
                self.nodes[i].set_index_label(i)
            # Set next/prev for arrows
            if prev_box is not None:
                prev_box.next_node = self.nodes[i]
                self.nodes[i].prev_node = prev_box
            prev_box = self.nodes[i]
            node = node.next
            i += 1
        if animate:
            self.layout_nodes()
        else:
            node_spacing = BOX_WIDTH + BOX_SPACING
            total_width = n * BOX_WIDTH + (n-1) * node_spacing if n > 0 else 0
            scene_width = max(900, total_width + 40)
            self.setSceneRect(0, 0, scene_width, 250)
            start_x = max(20, (scene_width - total_width) // 2)
            y = 80
            for i, node in enumerate(self.nodes):
                node.set_index_label(i)
                target = QPointF(start_x + i * (BOX_WIDTH + node_spacing), y)
                node.set_pos(target)
            # Head label
            if n > 0 and self.head_label:
                head_x = start_x + BOX_WIDTH // 2 - 20
                self.head_label.setPos(head_x, y - 30)
            if n > 0 and self.tail_label:
                tail_x = start_x + (n-1) * (BOX_WIDTH + node_spacing) + BOX_WIDTH // 2 - 20
                self.tail_label.setPos(tail_x, y + BOX_HEIGHT + 10)
            self.update_arrows()

    def set_box_color(self, index, color):
        if 0 <= index < len(self.nodes):
            self.nodes[index].set_box_color(color)

    def reset_all_colors(self):
        for node in self.nodes:
            node.reset_color()

    def update_arrows(self):
        for arrow in self.arrows:
            self.removeItem(arrow)
        self.arrows = []
        # Draw next arrows (right)
        for i, node in enumerate(self.nodes):
            if node.next_node is not None:
                n1 = node
                n2 = node.next_node
                x1 = n1.pos.x() + BOX_WIDTH
                y1 = n1.pos.y() + BOX_HEIGHT / 2
                x2 = n2.pos.x()
                y2 = n2.pos.y() + BOX_HEIGHT / 2
                line = self.addLine(x1, y1, x2, y2, QPen(ARROW_COLOR, 4))
                if line:
                    line.setZValue(0)
                self.arrows.append(line)
                # Arrowhead
                arrow_size = 14
                arrow_p1 = QPointF(x2, y2) + QPointF(-arrow_size * 0.7, -arrow_size * 0.5)
                arrow_p2 = QPointF(x2, y2) + QPointF(-arrow_size * 0.7, arrow_size * 0.5)
                arrow_head = QPolygonF([QPointF(x2, y2), arrow_p1, arrow_p2])
                arrow_item = self.addPolygon(arrow_head, QPen(ARROW_COLOR), QBrush(ARROW_COLOR))
                if arrow_item:
                    arrow_item.setZValue(1)
                self.arrows.append(arrow_item)
        # Draw prev arrows (left)
        for i, node in enumerate(self.nodes):
            if node.prev_node is not None:
                n1 = node
                n2 = node.prev_node
                x1 = n1.pos.x()
                y1 = n1.pos.y() + BOX_HEIGHT / 2
                x2 = n2.pos.x() + BOX_WIDTH
                y2 = n2.pos.y() + BOX_HEIGHT / 2
                line = self.addLine(x1, y1, x2, y2, QPen(QColor(80, 180, 255), 3, Qt.DashLine))
                if line:
                    line.setZValue(0)
                self.arrows.append(line)
                # Arrowhead
                arrow_size = 12
                arrow_p1 = QPointF(x2, y2) + QPointF(arrow_size * 0.7, -arrow_size * 0.5)
                arrow_p2 = QPointF(x2, y2) + QPointF(arrow_size * 0.7, arrow_size * 0.5)
                arrow_head = QPolygonF([QPointF(x2, y2), arrow_p1, arrow_p2])
                arrow_item = self.addPolygon(arrow_head, QPen(QColor(80, 180, 255)), QBrush(QColor(80, 180, 255)))
                if arrow_item:
                    arrow_item.setZValue(1)
                self.arrows.append(arrow_item)

class DoublyLinkedListVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self._stopped = False
        self.animations_enabled = True
        self.head = None  # Head node of the doubly linked list
        self.scene = DoublyLinkedListScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet('background: #f8f8ff; border: none;')
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setHorizontalScrollBarPolicy(1)  # Qt.ScrollBarAlwaysOn
        self.view.setVerticalScrollBarPolicy(0)    # Qt.ScrollBarAlwaysOff
        self.feedback = QLabel('')
        self.feedback.setStyleSheet('font-size: 16px; color: #333; margin: 8px;')
        self.steps = []
        self.current_step = 0
        self.step_explanation = QLabel('')
        self.step_explanation.setStyleSheet('font-size: 20px; color: #222; background: #e0e7ef; border-radius: 8px; padding: 12px; margin: 12px; font-family: Arial, Helvetica, sans-serif;')
        self.btn_next_step = QPushButton('Next Step')
        self.btn_next_step.clicked.connect(self.next_step)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        title = QLabel('Doubly Linked List Visualizer')
        title.setStyleSheet('font-size: 22px; font-weight: bold; margin: 8px;')
        main_layout.addWidget(title)
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.feedback)
        main_layout.addWidget(self.step_explanation)
        main_layout.addWidget(self.btn_next_step)
        main_layout.addStretch(1)
        btn_layout = QHBoxLayout()
        self.btn_random = QPushButton('Random List')
        self.btn_random.clicked.connect(self.generate_random_list)
        btn_layout.addWidget(self.btn_random)
        self.btn_create = QPushButton('Create Your Own')
        self.btn_create.clicked.connect(self.create_own_list)
        btn_layout.addWidget(self.btn_create)
        self.btn_add = QPushButton('Add Node')
        self.btn_add.clicked.connect(self.add_node)
        btn_layout.addWidget(self.btn_add)
        self.btn_insert = QPushButton('Insert at Index')
        self.btn_insert.clicked.connect(self.insert_at_index)
        btn_layout.addWidget(self.btn_insert)
        self.btn_remove = QPushButton('Remove Node')
        self.btn_remove.clicked.connect(self.remove_node)
        btn_layout.addWidget(self.btn_remove)
        self.btn_swap = QPushButton('Swap Nodes')
        self.btn_swap.clicked.connect(self.swap_nodes)
        btn_layout.addWidget(self.btn_swap)
        self.btn_replace = QPushButton('Replace Node Value')
        self.btn_replace.clicked.connect(self.replace_node_value)
        btn_layout.addWidget(self.btn_replace)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setMinimumHeight(350)
        self.setMinimumWidth(900)
        self.step_explanation.setVisible(True)
        self.btn_next_step.setVisible(False)

    def show_feedback(self, text):
        self.feedback.setText(text)
        QTimer.singleShot(1200, lambda: self.feedback.setText(''))

    def play_steps(self, steps, finalize_callback=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self._play_next_step(finalize_callback)

    def _play_next_step(self, finalize_callback=None):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        if callable(step):
            step()
            self.current_step += 1
            QTimer.singleShot(3500, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])
        else:
            head, highlight, explanation = step
            self.scene.set_from_head(head, animate=True)
            self.scene.reset_all_colors()
            for idx in highlight:
                self.scene.set_box_color(idx, QColor(255, 215, 0))
            if not sip.isdeleted(self.step_explanation):
                self.step_explanation.setText(explanation)
            self.feedback.setText('')
            self.current_step += 1
            QTimer.singleShot(3500, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])

    def to_list(self, head):
        arr = []
        node = head
        while node:
            arr.append(node.value)
            node = node.next
        return arr

    def clone_list(self, head):
        # Returns a new head, and a mapping from old node to new node
        if not head:
            return None, {}
        old_to_new = {}
        new_head = DLLNode(head.value)
        old_to_new[head] = new_head
        prev_new = new_head
        prev_old = head
        curr_old = head.next
        while curr_old:
            curr_new = DLLNode(curr_old.value)
            old_to_new[curr_old] = curr_new
            prev_new.next = curr_new
            curr_new.prev = prev_new
            prev_new = curr_new
            prev_old = curr_old
            curr_old = curr_old.next
        return new_head, old_to_new

    def set_head(self, head):
        self.head = head
        self.scene.set_from_head(self.head)

    def generate_random_list(self):
        values = [random.randint(0, 99) for _ in range(random.randint(4, 8))]
        self.head = None
        prev = None
        for v in values:
            node = DLLNode(v)
            if self.head is None:
                self.head = node
            if prev:
                prev.next = node
                node.prev = prev
            prev = node
        self.scene.set_from_head(self.head)
        self.show_feedback('Random doubly linked list generated.')
        self.step_explanation.setText('')

    def create_own_list(self):
        text, ok = QInputDialog.getText(self, 'Create Doubly Linked List', 'Enter numbers separated by commas:')
        if ok:
            try:
                nums = [int(x.strip()) for x in text.split(',') if x.strip()]
                self.head = None
                prev = None
                for v in nums:
                    node = DLLNode(v)
                    if self.head is None:
                        self.head = node
                    if prev:
                        prev.next = node
                        node.prev = prev
                    prev = node
                self.scene.set_from_head(self.head)
                self.show_feedback('Custom doubly linked list created.')
                self.step_explanation.setText('')
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter only numbers separated by commas.')

    def set_animations_enabled(self, enabled):
        self.animations_enabled = enabled

    def add_node(self):
        num, ok = QInputDialog.getInt(self, 'Add Node', 'Enter a number to add:')
        if ok:
            if not self.animations_enabled:
                if not self.head:
                    self.head = DLLNode(num)
                else:
                    node = self.head
                    while node.next:
                        node = node.next
                    new_node = DLLNode(num)
                    node.next = new_node
                    new_node.prev = node
                self.scene.set_from_head(self.head, animate=False)
                self.show_feedback(f'Added {num} to the end.')
                self.step_explanation.setText('')
                return
            # Add to end
            if not self.head:
                self.head = DLLNode(num)
            else:
                node = self.head
                while node.next:
                    node = node.next
                new_node = DLLNode(num)
                node.next = new_node
                new_node.prev = node
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Added {num} to the end.')
            self.step_explanation.setText('')

    def insert_at_index(self):
        idx, ok = QInputDialog.getInt(self, 'Insert at Index', f'Enter index (0 to {self.length()}):', min=0, max=self.length())
        if not ok:
            return
        num, ok = QInputDialog.getInt(self, 'Insert at Index', 'Enter a number to insert:')
        if not ok:
            return
        if not self.animations_enabled:
            if idx == 0:
                new_node = DLLNode(num)
                new_node.next = self.head
                if self.head:
                    self.head.prev = new_node
                self.head = new_node
            else:
                curr = self.head
                for i in range(idx - 1):
                    if curr is None:
                        break
                    curr = curr.next
                if curr is not None:
                    new_node = DLLNode(num)
                    new_node.next = curr.next
                    new_node.prev = curr
                    if curr.next:
                        curr.next.prev = new_node
                    curr.next = new_node
            self.scene.set_from_head(self.head, animate=False)
            self.show_feedback(f'Inserted {num} at index {idx}.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        # Create a copy of the list for animation
        head_copy, old_to_new = self.clone_list(self.head)
        steps = []
        
        # Step 1: Highlight where to insert
        if idx == 0:
            steps.append((head_copy, [idx], f"Step 1: Highlight position for new head node."))
        else:
            steps.append((head_copy, [idx], f"Step 1: Highlight index {idx} for insertion."))
        
        # Step 2: Traverse to the node before insertion point
        curr = head_copy
        prev = None
        for i in range(idx):
            if curr is None:
                break
            prev = curr
            curr = curr.next
        
        # Step 3: Create new node and update pointers
        new_node = DLLNode(num)
        if prev is None:
            # Inserting at head
            new_node.next = head_copy
            new_head = new_node
            steps.append((new_head, [0], f"Step 2: Create new node with value {num} and make it the new head."))
        else:
            # Inserting in middle or end
            new_node.next = curr
            prev.next = new_node
            new_head = head_copy
            steps.append((new_head, [idx], f"Step 2: Create new node with value {num} and update pointers."))
        
        steps.append((new_head, [], f"Step 3: Done. List after insertion."))
        
        def finalize():
            if sip.isdeleted(self):
                return
            # Actually insert in real list
            if idx == 0:
                # Insert at head
                new_node = DLLNode(num)
                new_node.next = self.head
                if self.head:
                    self.head.prev = new_node
                self.head = new_node
            else:
                # Insert in middle or end
                curr = self.head
                for i in range(idx - 1):
                    if curr is None:
                        break
                    curr = curr.next
                if curr is not None:
                    new_node = DLLNode(num)
                    new_node.next = curr.next
                    new_node.prev = curr
                    if curr.next:
                        curr.next.prev = new_node
                    curr.next = new_node
            
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Inserted {num} at index {idx}.')
            # Reset all colors
            self.scene.reset_all_colors()
        
        self.play_steps(steps, finalize)

    def remove_node(self):
        if not self.head:
            QMessageBox.warning(self, 'Empty List', 'List is already empty!')
            return
        idx, ok = QInputDialog.getInt(self, 'Remove Node', f'Enter index to remove (0 to {self.length()-1}):', min=0, max=max(0, self.length()-1))
        if not ok:
            return
        if not self.animations_enabled:
            curr = self.head
            prev = None
            for i in range(idx):
                prev = curr
                curr = curr.next if curr else None
            if curr is None:
                return
            if prev is None:
                self.head = curr.next
                if self.head:
                    self.head.prev = None
            else:
                prev.next = curr.next
                if curr.next:
                    curr.next.prev = prev
            self.scene.set_from_head(self.head, animate=False)
            self.show_feedback(f'Node at index {idx} removed.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        steps = []
        steps.append((self.head, [idx], f"Step 1: Highlight index {idx} to remove."))
        curr = self.head
        prev = None
        for i in range(idx):
            if curr is None:
                break
            prev = curr
            curr = curr.next if curr else None
        if curr is None:
            return
        if prev is None:
            # Remove head
            self.head = curr.next
            if self.head:
                self.head.prev = None
        else:
            prev.next = curr.next
            if curr.next:
                curr.next.prev = prev
        steps.append((self.head, [], f"Step 2: Node at index {idx} removed."))
        steps.append((self.head, [], f"Step 3: Done. List after removal."))
        def finalize():
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Node at index {idx} removed.')
            self.scene.reset_all_colors()
        self.play_steps(steps, finalize)

    def swap_nodes(self):
        n = self.length()
        if n < 2:
            QMessageBox.warning(self, 'Too Small', 'Need at least 2 nodes to swap.')
            return
        idx1, ok1 = QInputDialog.getInt(self, 'Swap Nodes', f'First index (0 to {n-1}):', min=0, max=n-1)
        if not ok1:
            return
        idx2, ok2 = QInputDialog.getInt(self, 'Swap Nodes', f'Second index (0 to {n-1}):', min=0, max=n-1)
        if not ok2 or idx1 == idx2:
            return
        if idx1 > idx2:
            idx1, idx2 = idx2, idx1
        if not self.animations_enabled:
            node1 = self.head
            for _ in range(idx1):
                node1 = node1.next
            node2 = self.head
            for _ in range(idx2):
                node2 = node2.next
            node1.value, node2.value = node2.value, node1.value
            self.scene.set_from_head(self.head, animate=False)
            self.show_feedback(f'Swapped nodes {idx1} and {idx2}.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        steps = []
        steps.append((self.head, [idx1, idx2], f"Step 1: Highlight nodes {idx1} and {idx2} to swap."))
        # Find nodes
        node1 = self.head
        for _ in range(idx1):
            node1 = node1.next
        node2 = self.head
        for _ in range(idx2):
            node2 = node2.next
        # Swap values (not nodes)
        node1.value, node2.value = node2.value, node1.value
        steps.append((self.head, [idx1, idx2], f"Step 2: Swap values at indices {idx1} and {idx2}."))
        steps.append((self.head, [], f"Step 3: Done. List after swap."))
        def finalize():
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Swapped nodes {idx1} and {idx2}.')
            self.scene.reset_all_colors()
        self.play_steps(steps, finalize)

    def replace_node_value(self):
        n = self.length()
        if n == 0:
            QMessageBox.warning(self, 'Empty List', 'List is empty!')
            return
        idx, ok = QInputDialog.getInt(self, 'Replace Node Value', f'Index to replace (0 to {n-1}):', min=0, max=n-1)
        if not ok:
            return
        value, ok = QInputDialog.getInt(self, 'Replace Node Value', 'New value:')
        if not ok:
            return
        steps = []
        steps.append((self.head, [idx], f"Step 1: Highlight node {idx} to replace value."))
        node = self.head
        for _ in range(idx):
            node = node.next
        old_value = node.value
        node.value = value
        steps.append((self.head, [idx], f"Step 2: Replace value {old_value} with {value} at index {idx}."))
        steps.append((self.head, [], f"Step 3: Done. List after replacement."))
        def finalize():
            self.scene.set_from_head(self.head)
            self.show_feedback(f'Replaced value at index {idx} with {value}.')
            self.scene.reset_all_colors()
        self.play_steps(steps, finalize)

    def length(self):
        count = 0
        node = self.head
        while node:
            count += 1
            node = node.next
        return count

    def next_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if callable(step):
                step()
            else:
                head, highlight, explanation = step
                self.scene.set_from_head(head)
                for idx in highlight:
                    self.scene.set_box_color(idx, QColor(255, 215, 0))
                self.step_explanation.setText(explanation)
                self.feedback.setText('')
            self.current_step += 1
        if self.current_step >= len(self.steps):
            self.btn_next_step.setVisible(False)

    def stop_animations(self):
        self._stopped = True
        self.animating = False
        self.steps = []
        self.current_step = 0
        if hasattr(self.scene, 'animations'):
            for anim in self.scene.animations:
                anim.stop()
            self.scene.animations.clear()

class StackBox(BaseBox):
    def __init__(self, value, index, color=QColor(240,240,240)):
        super().__init__(value, color)
        self.index = index
        self.index_text = f'[{index}]'
        self.rect = QRectF(0, 0, STACK_BOX_WIDTH, STACK_BOX_HEIGHT)
        self.default_color = color
        self.color = color
        self.text = str(value)
        self.setZValue(1)

    def boundingRect(self):
        return self.rect.adjusted(-2, -2, 2, 18)

    def paint(self, painter, option, widget=None):
        if painter is None:
            return
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRoundedRect(self.rect, 10, 10)
        painter.setFont(QFont('Arial', 16, QFont.Bold))
        painter.setPen(QPen(Qt.black))
        painter.drawText(self.rect, Qt.AlignCenter, self.text)
        painter.setFont(QFont('Arial', 10))
        painter.setPen(QPen(Qt.darkGray))
        painter.drawText(0, STACK_BOX_HEIGHT, STACK_BOX_WIDTH, 18, Qt.AlignCenter, self.index_text)

    def set_index(self, index):
        self.index = index
        self.index_text = f'[{index}]'
        self.update()

class StackScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, STACK_BOX_WIDTH + 60, 650)  # Match the new view height
        self.boxes = []
        self.spacing = STACK_BOX_SPACING
        self.box_w = STACK_BOX_WIDTH
        self.box_h = STACK_BOX_HEIGHT
        self.animations = []
        self.lines = []
        self.top_label = None

    def clear_scene(self):
        for box in self.boxes:
            self.removeItem(box)
        self.boxes = []
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        if self.top_label:
            self.removeItem(self.top_label)
            self.top_label = None
        self.clear()

    def layout_boxes(self, animate=True):
        n = len(self.boxes)
        total_height = n * self.box_h + (n-1) * self.spacing if n > 0 else 0
        scene_height = max(650, total_height + 80)  # Match the new view height
        self.setSceneRect(0, 0, STACK_BOX_WIDTH + 60, scene_height)
        x = 30
        # Center the stack vertically in the scene
        start_y = max(20, (scene_height - total_height) // 2)
        for i, box in enumerate(reversed(self.boxes)):
            # Assign correct index: top is n-1, next is n-2, ..., bottom is 0
            box.set_index(n-1-i)
            target = QPointF(x, start_y + i * (self.box_h + self.spacing))
            if animate:
                anim = QPropertyAnimation(box, b'pos')
                anim.setDuration(900)
                anim.setEasingCurve(QEasingCurve.InOutCubic)
                anim.setEndValue(target)
                anim.start()
                self.animations.append(anim)
            else:
                box.set_pos(target)
        # Draw top label
        if n > 0:
            if self.top_label is None:
                self.top_label = QGraphicsSimpleTextItem('top')
                self.top_label.setFont(QFont('Arial', 14, QFont.Bold))
                self.top_label.setBrush(QBrush(QColor(255, 60, 80)))
                self.addItem(self.top_label)
            self.top_label.setPos(x + STACK_BOX_WIDTH + 10, start_y)

    def set_values(self, values, animate=True):
        n = len(values)
        while len(self.boxes) > n:
            box = self.boxes.pop()
            self.removeItem(box)
        while len(self.boxes) < n:
            box = StackBox(values[len(self.boxes)], len(self.boxes))
            self.addItem(box)
            self.boxes.append(box)
        for i, v in enumerate(values):
            self.boxes[i].set_value(v)
        self.layout_boxes(animate=animate)

    def set_box_color(self, index, color):
        n = len(self.boxes)
        # index 0 is bottom, n-1 is top; visually, top is at y=0
        # So to highlight the top, use: self.boxes[-1]
        if 0 <= index < n:
            # Visually, box at y=0 is self.boxes[-1], at y=bottom is self.boxes[0]
            self.boxes[index].set_box_color(color)

    def reset_all_colors(self):
        for box in self.boxes:
            box.reset_color()

class StackVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self._stopped = False
        self.animations_enabled = True
        self.stack = []
        self.scene = StackScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet('background: #f8f8ff; border: none;')
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setVerticalScrollBarPolicy(1)  # Qt.ScrollBarAlwaysOn
        self.view.setHorizontalScrollBarPolicy(0)  # Qt.ScrollBarAlwaysOff
        self.feedback = QLabel('')
        self.feedback.setStyleSheet('font-size: 16px; color: #333; margin: 8px;')
        self.steps = []
        self.current_step = 0
        self.step_explanation = QLabel('')
        self.step_explanation.setStyleSheet('font-size: 20px; color: #222; background: #e0e7ef; border-radius: 8px; padding: 12px; margin: 12px; font-family: Arial, Helvetica, sans-serif;')
        self.btn_next_step = QPushButton('Next Step')
        self.btn_next_step.clicked.connect(self.next_step)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        title = QLabel('Stack Visualizer (Bookshelf)')
        title.setStyleSheet('font-size: 22px; font-weight: bold; margin: 8px;')
        main_layout.addWidget(title)
        # Make the stack view a bit taller
        self.view.setFixedHeight(650)  # Increased from 500 to 650
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.feedback)
        main_layout.addWidget(self.step_explanation)
        main_layout.addWidget(self.btn_next_step)
        btn_layout = QHBoxLayout()
        self.btn_random = QPushButton('Random Stack')
        self.btn_random.clicked.connect(self.generate_random_stack)
        btn_layout.addWidget(self.btn_random)
        self.btn_create = QPushButton('Create Your Own')
        self.btn_create.clicked.connect(self.create_own_stack)
        btn_layout.addWidget(self.btn_create)
        self.btn_push = QPushButton('Push')
        self.btn_push.clicked.connect(self.push_value)
        btn_layout.addWidget(self.btn_push)
        self.btn_pop = QPushButton('Pop')
        self.btn_pop.clicked.connect(self.pop_value)
        btn_layout.addWidget(self.btn_pop)
        self.btn_replace = QPushButton('Replace Value')
        self.btn_replace.clicked.connect(self.replace_value)
        btn_layout.addWidget(self.btn_replace)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setMinimumHeight(850)  # Adjusted for new view height
        self.setMinimumWidth(340)
        self.step_explanation.setVisible(True)
        self.btn_next_step.setVisible(False)

    def show_feedback(self, text):
        self.feedback.setText(text)
        QTimer.singleShot(1200, lambda: self.feedback.setText(''))

    def play_steps(self, steps, finalize_callback=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self._play_next_step(finalize_callback)

    def _play_next_step(self, finalize_callback=None):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        if callable(step):
            step()
            self.current_step += 1
            QTimer.singleShot(2000, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])
        else:
            arr, highlight, explanation = step
            self.scene.set_values(arr)
            self.scene.reset_all_colors()
            for idx in highlight:
                # Highlighting: index 0 is bottom, -1 is top
                self.scene.set_box_color(idx, QColor(255, 215, 0))
            self.step_explanation.setText(explanation)
            self.feedback.setText('')
            self.current_step += 1
            QTimer.singleShot(2000, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])

    def generate_random_stack(self):
        self.stack = [random.randint(0, 99) for _ in range(random.randint(4, 10))]
        self.scene.set_values(self.stack)
        self.show_feedback('Random stack generated.')
        self.step_explanation.setText('')

    def create_own_stack(self):
        text, ok = QInputDialog.getText(self, 'Create Stack', 'Enter numbers separated by commas:')
        if ok:
            try:
                nums = [int(x.strip()) for x in text.split(',') if x.strip()]
                self.stack = nums
                self.scene.set_values(self.stack)
                self.show_feedback('Custom stack created.')
                self.step_explanation.setText('')
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter only numbers separated by commas.')

    def set_animations_enabled(self, enabled):
        self.animations_enabled = enabled

    def push_value(self):
        num, ok = QInputDialog.getInt(self, 'Push', 'Enter a number to push:')
        if ok:
            if not self.animations_enabled:
                self.stack.append(num)
                self.scene.set_values(self.stack, animate=False)
                self.show_feedback(f'Pushed {num} to the stack.')
                self.step_explanation.setText('')
                return
            steps = []
            arr = self.stack.copy()
            steps.append((arr.copy(), [], f"Step 1: Current stack."))
            arr.append(num)
            steps.append((arr.copy(), [len(arr)-1], f"Step 2: Push {num} to the top of the stack."))
            steps.append((arr.copy(), [], f"Step 3: Done. Stack after push."))
            def finalize():
                self.stack.append(num)
                self.scene.set_values(self.stack)
                self.show_feedback(f'Pushed {num} to the stack.')
            self.play_steps(steps, finalize)

    def pop_value(self):
        if not self.stack:
            QMessageBox.warning(self, 'Empty Stack', 'Stack is already empty!')
            return
        if not self.animations_enabled:
            self.stack.pop()
            self.scene.set_values(self.stack, animate=False)
            self.show_feedback('Popped top value from the stack.')
            self.step_explanation.setText('')
            return
        steps = []
        arr = self.stack.copy()
        steps.append((arr.copy(), [len(arr)-1], f"Step 1: Highlight top value {arr[-1]} to pop."))
        arr2 = arr[:-1]
        steps.append((arr2.copy(), [], f"Step 2: Remove top value. Stack shrinks."))
        steps.append((arr2.copy(), [], f"Step 3: Done. Stack after pop."))
        def finalize():
            self.stack.pop()
            self.scene.set_values(self.stack)
            self.show_feedback('Popped top value from the stack.')
        self.play_steps(steps, finalize)

    def replace_value(self):
        if not self.stack:
            QMessageBox.warning(self, 'Empty Stack', 'Stack is empty!')
            return
        idx, ok = QInputDialog.getInt(self, 'Replace Value', f'Index to replace (0 is bottom, {len(self.stack)-1} is top):', min=0, max=len(self.stack)-1)
        if not ok:
            return
        value, ok = QInputDialog.getInt(self, 'Replace Value', 'New value:')
        if not ok:
            return
        if not self.animations_enabled:
            self.stack[idx] = value
            self.scene.set_values(self.stack, animate=False)
            self.show_feedback(f'Replaced value at index {idx} with {value}.')
            self.step_explanation.setText('')
            return
        steps = []
        arr = self.stack.copy()
        steps.append((arr.copy(), [idx], f"Step 1: Highlight index {idx} to replace value."))
        old_value = arr[idx]
        arr[idx] = value
        steps.append((arr.copy(), [idx], f"Step 2: Replace value {old_value} with {value} at index {idx}."))
        steps.append((arr.copy(), [], f"Step 3: Done. Stack after replacement."))
        def finalize():
            self.stack[idx] = value
            self.scene.set_values(self.stack)
            self.show_feedback(f'Replaced value at index {idx} with {value}.')
        self.play_steps(steps, finalize)

    def next_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if callable(step):
                step()
            else:
                arr, highlight, explanation = step
                self.scene.set_values(arr)
                for idx in highlight:
                    self.scene.set_box_color(idx, QColor(255, 215, 0))
                self.step_explanation.setText(explanation)
                self.feedback.setText('')
            self.current_step += 1
        if self.current_step >= len(self.steps):
            self.btn_next_step.setVisible(False)

    def stop_animations(self):
        self._stopped = True
        self.animating = False
        self.steps = []
        self.current_step = 0
        if hasattr(self.scene, 'animations'):
            for anim in self.scene.animations:
                anim.stop()
            self.scene.animations.clear()

class QueueScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 900, 250)
        self.boxes = []
        self.spacing = STACK_BOX_SPACING  # Use stack spacing for pancake style
        self.box_w = STACK_BOX_WIDTH      # Use stack box width
        self.box_h = STACK_BOX_HEIGHT     # Use stack box height
        self.animations = []
        self.lines = []
        self.front_label = None

    def clear_scene(self):
        for box in self.boxes:
            self.removeItem(box)
        self.boxes = []
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        if self.front_label:
            self.removeItem(self.front_label)
            self.front_label = None
        self.clear()

    def layout_boxes(self, animate=True):
        n = len(self.boxes)
        total_width = n * self.box_w + (n-1) * self.spacing if n > 0 else 0
        scene_width = max(900, total_width + 40)
        self.setSceneRect(0, 0, scene_width, 250)
        start_x = max(20, (scene_width - total_width) // 2)
        y = 80
        for i, box in enumerate(self.boxes):
            box.set_index(i)
            target = QPointF(start_x + i * (self.box_w + self.spacing), y)
            if animate:
                anim = QPropertyAnimation(box, b'pos')
                anim.setDuration(700)  # Smoother, slightly faster
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.setEndValue(target)
                anim.start()
                self.animations.append(anim)
            else:
                box.set_pos(target)
        QTimer.singleShot(750, self.update_lines)
        if n > 0:
            if self.front_label is None:
                self.front_label = QGraphicsSimpleTextItem('front')
                self.front_label.setFont(QFont('Arial', 14, QFont.Bold))
                self.front_label.setBrush(QBrush(QColor(255, 60, 80)))
                self.addItem(self.front_label)
            front_x = start_x + self.box_w // 2 - 20
            self.front_label.setPos(front_x, y - 30)

    def update_lines(self):
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        for i in range(1, len(self.boxes)):
            prev_box = self.boxes[i-1]
            curr_box = self.boxes[i]
            x1 = prev_box.pos.x() + self.box_w
            y1 = prev_box.pos.y() + self.box_h / 2
            x2 = curr_box.pos.x()
            y2 = curr_box.pos.y() + self.box_h / 2
            line = self.addLine(x1, y1, x2, y2, QPen(ARROW_COLOR, 3))
            if line:
                line.setZValue(0)
            self.lines.append(line)

    def set_values(self, values, animate=True):
        n = len(values)
        while len(self.boxes) > n:
            box = self.boxes.pop()
            self.removeItem(box)
        while len(self.boxes) < n:
            box = StackBox(values[len(self.boxes)], len(self.boxes))  # Use StackBox for pancake style
            self.addItem(box)
            self.boxes.append(box)
        for i, v in enumerate(values):
            self.boxes[i].set_value(v)
        self.layout_boxes(animate=animate)

    def set_box_color(self, index, color):
        if 0 <= index < len(self.boxes):
            self.boxes[index].set_box_color(color)

    def reset_all_colors(self):
        for box in self.boxes:
            box.reset_color()

    def show_temp_box(self, value, pos):
        temp_box = StackBox(value, -1, QColor(255, 255, 180))
        temp_box.setPos(pos)
        temp_box.setZValue(2)
        self.addItem(temp_box)
        label = QGraphicsSimpleTextItem('temp')
        label.setFont(QFont('Arial', 14, QFont.Bold))
        label.setBrush(QBrush(QColor(255, 60, 80)))
        label.setPos(pos.x() + 30, pos.y() + STACK_BOX_HEIGHT + 8)
        label.setZValue(2)
        self.addItem(label)
        return temp_box, label

    def remove_temp_box(self, temp_box, label):
        self.removeItem(temp_box)
        self.removeItem(label)

class QueueVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self._stopped = False
        self.animations_enabled = True
        self.queue = []
        self.scene = QueueScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet('background: #f8f8ff; border: none;')
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setHorizontalScrollBarPolicy(1)
        self.view.setVerticalScrollBarPolicy(0)
        self.feedback = QLabel('')
        self.feedback.setStyleSheet('font-size: 16px; color: #333; margin: 8px;')
        self.steps = []
        self.current_step = 0
        self.step_explanation = QLabel('')
        self.step_explanation.setStyleSheet('font-size: 20px; color: #222; background: #e0e7ef; border-radius: 8px; padding: 12px; margin: 12px; font-family: Arial, Helvetica, sans-serif;')
        self.btn_next_step = QPushButton('Next Step')
        self.btn_next_step.clicked.connect(self.next_step)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        title = QLabel('Queue Visualizer')
        title.setStyleSheet('font-size: 22px; font-weight: bold; margin: 8px;')
        main_layout.addWidget(title)
        self.view.setFixedHeight(650)  # Match StackVisualizer
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.feedback)
        main_layout.addWidget(self.step_explanation)
        main_layout.addWidget(self.btn_next_step)
        btn_layout = QHBoxLayout()
        self.btn_random = QPushButton('Random Queue')
        self.btn_random.clicked.connect(self.generate_random_queue)
        btn_layout.addWidget(self.btn_random)
        self.btn_create = QPushButton('Create Your Own')
        self.btn_create.clicked.connect(self.create_own_queue)
        btn_layout.addWidget(self.btn_create)
        self.btn_enqueue = QPushButton('Enqueue')
        self.btn_enqueue.clicked.connect(self.enqueue_value)
        btn_layout.addWidget(self.btn_enqueue)
        self.btn_dequeue = QPushButton('Dequeue')
        self.btn_dequeue.clicked.connect(self.dequeue_value)
        btn_layout.addWidget(self.btn_dequeue)
        self.btn_replace = QPushButton('Replace Value')
        self.btn_replace.clicked.connect(self.replace_value)
        btn_layout.addWidget(self.btn_replace)
        self.btn_swap = QPushButton('Swap Elements')
        self.btn_swap.clicked.connect(self.swap_elements)
        btn_layout.addWidget(self.btn_swap)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setMinimumHeight(850)  # Match StackVisualizer
        self.setMinimumWidth(340)
        self.step_explanation.setVisible(True)
        self.btn_next_step.setVisible(False)

    def show_feedback(self, text):
        self.feedback.setText(text)
        QTimer.singleShot(1200, lambda: self.feedback.setText(''))

    def play_steps(self, steps, finalize_callback=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self._play_next_step(finalize_callback)

    def _play_next_step(self, finalize_callback=None):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        if callable(step):
            step()
            self.current_step += 1
            QTimer.singleShot(2000, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])
        else:
            arr, highlight, explanation = step
            self.scene.set_values(arr)
            self.scene.reset_all_colors()
            for idx in highlight:
                self.scene.set_box_color(idx, QColor(255, 215, 0))
            self.step_explanation.setText(explanation)
            self.feedback.setText('')
            self.current_step += 1
            QTimer.singleShot(2000, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])

    def generate_random_queue(self):
        self.queue = [random.randint(0, 99) for _ in range(random.randint(4, 10))]
        self.scene.set_values(self.queue)
        self.show_feedback('Random queue generated.')
        self.step_explanation.setText('')

    def create_own_queue(self):
        text, ok = QInputDialog.getText(self, 'Create Queue', 'Enter numbers separated by commas:')
        if ok:
            try:
                nums = [int(x.strip()) for x in text.split(',') if x.strip()]
                self.queue = nums
                self.scene.set_values(self.queue)
                self.show_feedback('Custom queue created.')
                self.step_explanation.setText('')
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter only numbers separated by commas.')

    def set_animations_enabled(self, enabled):
        self.animations_enabled = enabled

    def enqueue_value(self):
        num, ok = QInputDialog.getInt(self, 'Enqueue', 'Enter a number to enqueue:')
        if ok:
            if not self.animations_enabled:
                self.queue.append(num)
                self.scene.set_values(self.queue, animate=False)
                self.show_feedback(f'Enqueued {num} to the queue.')
                self.step_explanation.setText('')
                return
            steps = []
            arr = self.queue.copy()
            steps.append((arr.copy(), [], f"Step 1: Current queue."))
            arr.append(num)
            steps.append((arr.copy(), [len(arr)-1], f"Step 2: Enqueue {num} to the rear of the queue."))
            steps.append((arr.copy(), [0], f"Step 3: Front of the queue is at index 0."))
            steps.append((arr.copy(), [], f"Step 4: Done. Queue after enqueue."))
            def finalize():
                self.queue.append(num)
                self.scene.set_values(self.queue)
                self.show_feedback(f'Enqueued {num} to the queue.')
            self.play_steps(steps, finalize)

    def dequeue_value(self):
        if not self.queue:
            QMessageBox.warning(self, 'Empty Queue', 'Queue is already empty!')
            return
        if not self.animations_enabled:
            self.queue.pop(0)
            self.scene.set_values(self.queue, animate=False)
            self.show_feedback('Dequeued front value from the queue.')
            self.step_explanation.setText('')
            return
        steps = []
        arr = self.queue.copy()
        steps.append((arr.copy(), [0], f"Step 1: Highlight front value {arr[0]} to dequeue."))
        arr2 = arr[1:]
        steps.append((arr2.copy(), [0] if arr2 else [], f"Step 2: Remove front value. New front is at index 0." if arr2 else "Step 2: Queue is now empty."))
        steps.append((arr2.copy(), [], f"Step 3: Done. Queue after dequeue."))
        def finalize():
            self.queue.pop(0)
            self.scene.set_values(self.queue)
            self.show_feedback('Dequeued front value from the queue.')
        self.play_steps(steps, finalize)

    def replace_value(self):
        if not self.queue:
            QMessageBox.warning(self, 'Empty Queue', 'Queue is empty!')
            return
        idx, ok = QInputDialog.getInt(self, 'Replace Value', f'Index to replace (0 is front, {len(self.queue)-1} is rear):', min=0, max=len(self.queue)-1)
        if not ok:
            return
        value, ok = QInputDialog.getInt(self, 'Replace Value', 'New value:')
        if not ok:
            return
        if not self.animations_enabled:
            self.queue[idx] = value
            self.scene.set_values(self.queue, animate=False)
            self.show_feedback(f'Replaced value at index {idx} with {value}.')
            self.step_explanation.setText('')
            return
        steps = []
        arr = self.queue.copy()
        steps.append((arr.copy(), [idx], f"Step 1: Highlight index {idx} to replace value."))
        old_value = arr[idx]
        arr[idx] = value
        steps.append((arr.copy(), [idx], f"Step 2: Replace value {old_value} with {value} at index {idx}."))
        steps.append((arr.copy(), [], f"Step 3: Done. Queue after replacement."))
        def finalize():
            self.queue[idx] = value
            self.scene.set_values(self.queue)
            self.show_feedback(f'Replaced value at index {idx} with {value}.')
        self.play_steps(steps, finalize)

    def swap_elements(self):
        if len(self.queue) < 2:
            QMessageBox.warning(self, 'Too Small', 'Need at least 2 elements to swap.')
            return
        idx1, ok1 = QInputDialog.getInt(self, 'Swap Elements', f'First index (0 to {len(self.queue)-1}):', min=0, max=len(self.queue)-1)
        if not ok1:
            return
        idx2, ok2 = QInputDialog.getInt(self, 'Swap Elements', f'Second index (0 to {len(self.queue)-1}):', min=0, max=len(self.queue)-1)
        if not ok2 or idx1 == idx2:
            return
        if not self.animations_enabled:
            self.queue[idx1], self.queue[idx2] = self.queue[idx2], self.queue[idx1]
            self.scene.set_values(self.queue, animate=False)
            self.show_feedback(f'Swapped index {idx1} and {idx2}.')
            self.step_explanation.setText('')
            self.scene.reset_all_colors()
            return
        arr = self.queue.copy()
        steps = []
        steps.append((arr.copy(), [idx1, idx2], f"Step 1: Highlight indices {idx1} and {idx2} to swap."))
        steps.append((arr.copy(), [idx1], f"Step 2: Store value {arr[idx1]} from index {idx1} in temp variable."))
        temp = arr[idx1]
        arr[idx1] = arr[idx2]
        steps.append((arr.copy(), [idx1, idx2], f"Step 3: Assign value from index {idx2} ({arr[idx2]}) to index {idx1}."))
        arr[idx2] = temp
        steps.append((arr.copy(), [idx2], f"Step 4: Assign temp value ({arr[idx2]}) to index {idx2}."))
        steps.append((arr.copy(), [], f"Step 5: Done. Queue after swap."))
        def finalize():
            self.queue[idx1], self.queue[idx2] = self.queue[idx2], self.queue[idx1]
            self.scene.set_values(self.queue)
            self.show_feedback(f'Swapped index {idx1} and {idx2}.')
            self.scene.reset_all_colors()
        # Use temp box visualization
        self.play_steps_auto_with_temp(steps, finalize, delay=2200, temp_value=temp, temp_steps=[1,2,3], idx1=idx1, idx2=idx2)

    def play_steps_auto_with_temp(self, steps, finalize_callback=None, delay=2200, temp_value=None, temp_steps=None, idx1=None, idx2=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self.temp_value = temp_value
        self.temp_steps = temp_steps or []
        self.temp_box = None
        self.temp_label = None
        self._play_next_step_auto_with_temp(finalize_callback, delay, idx1, idx2)

    def _play_next_step_auto_with_temp(self, finalize_callback=None, delay=2200, idx1=None, idx2=None):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if self.temp_box and self.temp_label:
                self.scene.remove_temp_box(self.temp_box, self.temp_label)
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        arr, highlight, explanation = step
        # Handle temp box visibility
        if self.current_step in self.temp_steps:
            if self.temp_box is None:
                # Center temp box above the queue
                n = len(arr)
                total_width = n * STACK_BOX_WIDTH + (n-1) * STACK_BOX_SPACING
                scene_width = max(900, total_width + 40)
                start_x = max(20, (scene_width - total_width) // 2)
                temp_x = start_x + ((idx1 + idx2) / 2) * (STACK_BOX_WIDTH + STACK_BOX_SPACING)
                temp_y = 20  # Above the queue
                temp_pos = QPointF(temp_x, temp_y)
                self.temp_box, self.temp_label = self.scene.show_temp_box(self.temp_value, temp_pos)
        else:
            if self.temp_box and self.temp_label:
                self.scene.remove_temp_box(self.temp_box, self.temp_label)
                self.temp_box = None
                self.temp_label = None
        self.scene.set_values(arr)
        self.scene.reset_all_colors()
        for idx in highlight:
            self.scene.set_box_color(idx, QColor(255, 215, 0))
        if hasattr(self, 'step_explanation') and self.step_explanation and not sip.isdeleted(self.step_explanation):
            self.step_explanation.setText(explanation)
        self.feedback.setText('')
        self.current_step += 1
        QTimer.singleShot(delay, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step_auto_with_temp(finalize_callback, delay, idx1, idx2), None)[-1])

    def next_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if callable(step):
                step()
            else:
                arr, highlight, explanation = step
                self.scene.set_values(arr)
                for idx in highlight:
                    self.scene.set_box_color(idx, QColor(255, 215, 0))
                self.step_explanation.setText(explanation)
                self.feedback.setText('')
            self.current_step += 1
        if self.current_step >= len(self.steps):
            self.btn_next_step.setVisible(False)

    def stop_animations(self):
        self._stopped = True
        self.animating = False
        self.steps = []
        self.current_step = 0
        self.temp_box = None
        self.temp_label = None
        if hasattr(self.scene, 'animations'):
            for anim in self.scene.animations:
                anim.stop()
            self.scene.animations.clear()

class VisualizerArea(QWidget):
    def __init__(self, structure_name):
        super().__init__()
        self.layout_widget = QVBoxLayout()
        self.structure_name = structure_name
        self.current_widget = None
        self.setLayout(self.layout_widget)
        self.set_structure(structure_name)

    def set_structure(self, structure_name):
        # Remove old widget
        if self.current_widget:
            self.layout_widget.removeWidget(self.current_widget)
            self.current_widget.deleteLater()
            self.current_widget = None
        self.structure_name = structure_name
        if structure_name == 'Array':
            self.current_widget = ArrayVisualizer()
        elif structure_name == 'Singly Linked List':
            self.current_widget = LinkedListVisualizer()
        elif structure_name == 'Doubly Linked List':
            self.current_widget = DoublyLinkedListVisualizer()
        elif structure_name == 'Stack':
            self.current_widget = StackVisualizer()
        elif structure_name == 'Queue':
            self.current_widget = QueueVisualizer()
        elif structure_name == 'Sorting':
            self.current_widget = SortingVisualizer()
        else:
            self.current_widget = QLabel(f'Visualization for: {structure_name}')
            self.current_widget.setStyleSheet('font-size: 20px;')
        self.layout_widget.addWidget(self.current_widget)

    def update_structure(self, structure_name):
        self.set_structure(structure_name)

class MainMenu(QWidget):
    def __init__(self, on_select, on_tutorial=None, on_tree=None):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel(f"<b style='font-size:32px; color:{ACCENT}; letter-spacing:2px;'>Data Structures Visualizer</b>")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel(f"<span style='font-size:18px; color:{SUBTEXT_COLOR};'>Learn how data structures work, step by step!</span>")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(30)
        # Create buttons with consistent styling
        buttons = [
            ("Array Visualizer", 'Array'),
            ("Singly Linked List Visualizer", 'Singly Linked List'),
            ("Doubly Linked List Visualizer", 'Doubly Linked List'),
            ("Stack Visualizer (Bookshelf)", 'Stack'),
            ("Queue Visualizer", 'Queue'),
            ("Sorting Visualizer", 'Sorting'),
        ]
        for text, structure in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"padding:18px; font-size:20px; border-radius:12px; background:{ACCENT}; color:{TEXT_COLOR}; letter-spacing:1px;")
            btn.clicked.connect(lambda checked, s=structure: on_select(s))
            layout.addWidget(btn)
        # Add Tree Visualizer button
        tree_btn = QPushButton('Tree Visualizer')
        tree_btn.setStyleSheet(f"padding:18px; font-size:20px; border-radius:12px; background:{ACCENT}; color:{TEXT_COLOR}; letter-spacing:1px;")
        if on_tree:
            tree_btn.clicked.connect(on_tree)
        layout.addWidget(tree_btn)
        # Rename tutorial button
        tutorial_btn = QPushButton('Tutorial')
        tutorial_btn.setStyleSheet(f"padding:14px; font-size:18px; border-radius:10px; background:#fff; color:{ACCENT}; font-weight:bold; margin-top:18px;")
        if on_tutorial:
            tutorial_btn.clicked.connect(on_tutorial)
        layout.addWidget(tutorial_btn)
        layout.addStretch(1)
        self.setLayout(layout)

class ModernMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Data Structures Visualizer')
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet(f"background: {PRIMARY_BG};")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stacked = QStackedWidget()
        self.menu = MainMenu(self.select_visualizer, self.show_tutorial, self.show_tree_menu)
        self.stacked.addWidget(self.menu)
        self.visualizer_area = None
        self.tutorial_widget = None
        self.tree_type_menu = None
        self.animations_enabled = True
        # Animation toggle
        self.anim_toggle = QCheckBox('Animations On')
        self.anim_toggle.setChecked(True)
        self.anim_toggle.setStyleSheet('font-size: 16px; color: #fff; margin: 12px;')
        self.anim_toggle.stateChanged.connect(self.toggle_animations)
        # Layout for toggle
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.stacked)
        # Add toggle at the bottom left
        toggle_layout = QHBoxLayout()
        toggle_layout.setContentsMargins(10, 0, 0, 10)
        toggle_layout.addWidget(self.anim_toggle, alignment=Qt.AlignLeft | Qt.AlignBottom)
        toggle_layout.addStretch(1)
        main_layout.addLayout(toggle_layout)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # No need to move toggle manually
    def toggle_animations(self, state):
        self.animations_enabled = bool(state)
        # Update current visualizer if present
        if self.visualizer_area and hasattr(self.visualizer_area, 'set_animations_enabled'):
            self.visualizer_area.set_animations_enabled(self.animations_enabled)
    def select_visualizer(self, name):
        if self.visualizer_area:
            self.stacked.removeWidget(self.visualizer_area)
            self.visualizer_area.deleteLater()
        visualizer_map = {
            'Array': ArrayVisualizer,
            'Singly Linked List': LinkedListVisualizer,
            'Doubly Linked List': DoublyLinkedListVisualizer,
            'Stack': StackVisualizer,
            'Queue': QueueVisualizer,
            'Sorting': SortingVisualizer
        }
        if name in visualizer_map:
            self.visualizer_area = visualizer_map[name]()
            if hasattr(self.visualizer_area, 'set_animations_enabled'):
                self.visualizer_area.set_animations_enabled(self.animations_enabled)
        else:
            self.visualizer_area = QLabel('Coming soon!')
        card = QWidget()
        card.setStyleSheet(f"background: {CARD_BG}; border-radius: 18px; padding: 32px; margin: 32px;")
        vbox = QVBoxLayout()
        vbox.addWidget(self.visualizer_area)
        back_btn = QPushButton('Back to Menu')
        back_btn.setStyleSheet(f"background: transparent; color: {ACCENT}; font-size: 16px; border: 2px solid {ACCENT}; border-radius: 8px; padding: 6px 18px; margin-bottom: 12px; margin-left: auto;")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.show_menu)
        vbox.insertWidget(0, back_btn, alignment=Qt.AlignRight)
        card.setLayout(vbox)
        self.stacked.addWidget(card)
        self.stacked.setCurrentWidget(card)
    def show_menu(self):
        if self.visualizer_area and hasattr(self.visualizer_area, 'stop_animations'):
            self.visualizer_area.stop_animations()
        self.stacked.setCurrentWidget(self.menu)
    def show_tutorial(self):
        if self.tutorial_widget:
            self.stacked.removeWidget(self.tutorial_widget)
            self.tutorial_widget.deleteLater()
        self.tutorial_widget = TutorialWidget(on_exit=self.show_menu)
        self.stacked.addWidget(self.tutorial_widget)
        self.stacked.setCurrentWidget(self.tutorial_widget)
    def show_tree_menu(self):
        if self.tree_type_menu:
            self.stacked.removeWidget(self.tree_type_menu)
            self.tree_type_menu.deleteLater()
        self.tree_type_menu = TreeTypeMenu(self.select_tree_type, self.show_menu)
        self.stacked.addWidget(self.tree_type_menu)
        self.stacked.setCurrentWidget(self.tree_type_menu)
    def select_tree_type(self, tree_type):
        if self.visualizer_area:
            self.stacked.removeWidget(self.visualizer_area)
            self.visualizer_area.deleteLater()
        self.visualizer_area = TreeVisualizer(tree_type)
        card = QWidget()
        card.setStyleSheet(f"background: {CARD_BG}; border-radius: 18px; padding: 32px; margin: 32px;")
        vbox = QVBoxLayout()
        vbox.addWidget(self.visualizer_area)
        back_btn = QPushButton('Back to Tree Menu')
        back_btn.setStyleSheet(f"background: transparent; color: {ACCENT}; font-size: 16px; border: 2px solid {ACCENT}; border-radius: 8px; padding: 6px 18px; margin-bottom: 12px; margin-left: auto;")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.show_tree_menu)
        vbox.insertWidget(0, back_btn, alignment=Qt.AlignRight)
        card.setLayout(vbox)
        self.stacked.addWidget(card)
        self.stacked.setCurrentWidget(card)

# --- Sorting Visualizer ---
class SortingVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self._stopped = False
        self.animations_enabled = True
        self.array = []
        self.scene = ArrayScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet('background: #f8f8ff; border: none;')
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QAbstractScrollArea
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.feedback = QLabel('')
        self.feedback.setStyleSheet('font-size: 16px; color: #333; margin: 8px;')
        self.steps = []
        self.current_step = 0
        self.step_explanation = QLabel('')
        self.step_explanation.setStyleSheet('font-size: 20px; color: #222; background: #e0e7ef; border-radius: 8px; padding: 12px; margin: 12px; font-family: Arial, Helvetica, sans-serif;')
        self.animating = False
        self.btn_next_step = QPushButton('Next Step')
        self.btn_next_step.clicked.connect(self.next_step)
        # Dijkstra
        self.dijkstra_scene = DijkstraGraphScene()
        self.dijkstra_view = QGraphicsView(self.dijkstra_scene)
        self.dijkstra_view.setRenderHint(QPainter.Antialiasing)
        self.dijkstra_view.setStyleSheet('background: #f8f8ff; border: none;')
        self.dijkstra_view.setFixedHeight(400)
        self.dijkstra_view.setVisible(False)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        title = QLabel('Sorting & Dijkstra Visualizer')
        title.setStyleSheet('font-size: 22px; font-weight: bold; margin: 8px;')
        main_layout.addWidget(title)
        main_layout.addWidget(self.view)
        main_layout.addWidget(self.dijkstra_view)
        main_layout.addWidget(self.feedback)
        main_layout.addWidget(self.step_explanation)
        main_layout.addWidget(self.btn_next_step)
        main_layout.addStretch(1)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(32)  # Add more space between buttons
        # Button style: white background, red border, bold text, 30% smaller
        button_style = (
            "background: #fff; color: #23232a; font-size: 11.6px; min-width: 126px; padding: 12.6px 8px; "
            "border: 2px solid #ff1744; border-radius: 12px; font-weight: bold; letter-spacing: 1px; margin: 6px;"
        )
        self.btn_random = QPushButton('Random Array')
        self.btn_random.setStyleSheet(button_style)
        self.btn_random.clicked.connect(self.generate_random_array)
        btn_layout.addWidget(self.btn_random)
        self.btn_create = QPushButton('Create Your Own')
        self.btn_create.setStyleSheet(button_style)
        self.btn_create.clicked.connect(self.create_own_array)
        btn_layout.addWidget(self.btn_create)
        self.btn_bubble = QPushButton('Bubble Sort')
        self.btn_bubble.setStyleSheet(button_style)
        self.btn_bubble.clicked.connect(self.bubble_sort)
        btn_layout.addWidget(self.btn_bubble)
        self.btn_selection = QPushButton('Selection Sort')
        self.btn_selection.setStyleSheet(button_style)
        self.btn_selection.clicked.connect(self.selection_sort)
        btn_layout.addWidget(self.btn_selection)
        self.btn_insertion = QPushButton('Insertion Sort')
        self.btn_insertion.setStyleSheet(button_style)
        self.btn_insertion.clicked.connect(self.insertion_sort)
        btn_layout.addWidget(self.btn_insertion)
        self.btn_merge = QPushButton('Merge Sort')
        self.btn_merge.setStyleSheet(button_style)
        self.btn_merge.clicked.connect(self.merge_sort)
        btn_layout.addWidget(self.btn_merge)
        self.btn_quick = QPushButton('Quick Sort')
        self.btn_quick.setStyleSheet(button_style)
        self.btn_quick.clicked.connect(self.quick_sort)
        btn_layout.addWidget(self.btn_quick)
        self.btn_dijkstra = QPushButton("Dijkstra's Algorithm")
        self.btn_dijkstra.setStyleSheet(button_style)
        self.btn_dijkstra.clicked.connect(self.dijkstra_algorithm)
        btn_layout.addWidget(self.btn_dijkstra)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.setMinimumHeight(400)
        self.setMinimumWidth(900)
        self.step_explanation.setVisible(True)
        self.btn_next_step.setVisible(False)

    def show_feedback(self, text):
        self.feedback.setText(text)
        QTimer.singleShot(1200, lambda: self.feedback.setText(''))

    def play_steps(self, steps, finalize_callback=None):
        self._stopped = False
        self.steps = steps
        self.current_step = 0
        self.animating = True
        self._play_next_step(finalize_callback)

    def _play_next_step(self, finalize_callback=None):
        if getattr(self, '_stopped', False) or sip.isdeleted(self):
            return
        if self.current_step >= len(self.steps):
            self.animating = False
            if finalize_callback:
                finalize_callback()
            return
        step = self.steps[self.current_step]
        arr, highlight, explanation = step
        self.scene.set_values(arr)
        self.scene.reset_all_colors()
        for idx in highlight:
            self.scene.set_box_color(idx, QColor(255, 215, 0))
        # Fix: Only set text if label exists and is not deleted
        if hasattr(self, 'step_explanation') and self.step_explanation and not sip.isdeleted(self.step_explanation):
            self.step_explanation.setText(explanation)
        self.feedback.setText('')
        self.current_step += 1
        QTimer.singleShot(1200, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self._play_next_step(finalize_callback), None)[-1])

    def generate_random_array(self):
        self.array = [random.randint(0, 99) for _ in range(random.randint(6, 12))]
        self.scene.set_values(self.array)
        self.show_feedback('Random array generated.')
        self.step_explanation.setText('')

    def create_own_array(self):
        text, ok = QInputDialog.getText(self, 'Create Array', 'Enter numbers separated by commas:')
        if ok:
            try:
                nums = [int(x.strip()) for x in text.split(',') if x.strip()]
                self.array = nums
                self.scene.set_values(self.array)
                self.show_feedback('Custom array created.')
                self.step_explanation.setText('')
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter only numbers separated by commas.')

    def bubble_sort(self):
        arr = self.array.copy()
        n = len(arr)
        if not self.animations_enabled:
            arr.sort()
            self.array = arr
            self.scene.set_values(self.array, animate=False)
            self.show_feedback('Bubble Sort complete.')
            self.step_explanation.setText('')
            return
        steps = [(arr.copy(), [], 'Bubble Sort: We will repeatedly compare and swap adjacent elements if they are in the wrong order. The largest value "bubbles" to the end each round.')]
        for i in range(n):
            for j in range(0, n-i-1):
                steps.append((arr.copy(), [j, j+1], f'Compare elements at index {j} and {j+1}. If the left one is bigger, we swap them.'))
                if arr[j] > arr[j+1]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
                    steps.append((arr.copy(), [j, j+1], f'Swap! Now {arr[j]} is before {arr[j+1]}.'))
            steps.append((arr.copy(), [n-i-1], f'After this round, the largest unsorted value is at index {n-i-1}.'))
        steps.append((arr.copy(), [], 'Bubble Sort is finished! The array is now sorted from smallest to largest.'))
        def finalize():
            self.array = arr
            self.scene.set_values(self.array)
            self.show_feedback('Bubble Sort complete.')
        self.play_steps(steps, finalize)

    def selection_sort(self):
        arr = self.array.copy()
        n = len(arr)
        if not self.animations_enabled:
            arr.sort()
            self.array = arr
            self.scene.set_values(self.array, animate=False)
            self.show_feedback('Selection Sort complete.')
            self.step_explanation.setText('')
            return
        steps = [(arr.copy(), [], 'Selection Sort: We repeatedly find the smallest value in the unsorted part and move it to its correct place.')]
        for i in range(n):
            min_idx = i
            steps.append((arr.copy(), [i], f'Assume index {i} is the smallest in the unsorted part.'))
            for j in range(i+1, n):
                steps.append((arr.copy(), [min_idx, j], f'Compare index {min_idx} (current smallest) with index {j}.'))
                if arr[j] < arr[min_idx]:
                    min_idx = j
                    steps.append((arr.copy(), [min_idx], f'Found a new smallest value at index {min_idx}.'))
            if min_idx != i:
                arr[i], arr[min_idx] = arr[min_idx], arr[i]
                steps.append((arr.copy(), [i, min_idx], f'Swap the smallest value to index {i}.'))
            steps.append((arr.copy(), [i], f'Index {i} is now sorted.'))
        steps.append((arr.copy(), [], 'Selection Sort is finished! The array is sorted.'))
        def finalize():
            self.array = arr
            self.scene.set_values(self.array)
            self.show_feedback('Selection Sort complete.')
        self.play_steps(steps, finalize)

    def insertion_sort(self):
        arr = self.array.copy()
        n = len(arr)
        if not self.animations_enabled:
            arr.sort()
            self.array = arr
            self.scene.set_values(self.array, animate=False)
            self.show_feedback('Insertion Sort complete.')
            self.step_explanation.setText('')
            return
        steps = [(arr.copy(), [], 'Insertion Sort: We build the sorted array one value at a time by inserting each value into its correct position.')]
        for i in range(1, n):
            key = arr[i]
            j = i-1
            steps.append((arr.copy(), [i], f'Pick value {key} at index {i} to insert into the sorted part.'))
            while j >= 0 and arr[j] > key:
                arr[j+1] = arr[j]
                steps.append((arr.copy(), [j, j+1], f'Shift value at index {j} to {j+1}.'))
                j -= 1
            arr[j+1] = key
            steps.append((arr.copy(), [j+1], f'Insert key at index {j+1}.'))
            steps.append((arr.copy(), list(range(i+1)), f'First {i+1} values are now sorted.'))
        steps.append((arr.copy(), [], 'Insertion Sort is finished! The array is sorted.'))
        def finalize():
            self.array = arr
            self.scene.set_values(self.array)
            self.show_feedback('Insertion Sort complete.')
        self.play_steps(steps, finalize)

    def merge_sort(self):
        arr = self.array.copy()
        if not self.animations_enabled:
            arr.sort()
            self.array = arr
            self.scene.set_values(self.array, animate=False)
            self.show_feedback('Merge Sort complete.')
            self.step_explanation.setText('')
            return
        steps = [(arr.copy(), [], 'Merge Sort: We divide the array into halves, sort each half, and then merge them back together in order.')]
        def merge_sort_rec(l, r):
            if l >= r:
                return
            m = (l + r) // 2
            merge_sort_rec(l, m)
            merge_sort_rec(m+1, r)
            left = arr[l:m+1]
            right = arr[m+1:r+1]
            i = l
            li = 0
            ri = 0
            while li < len(left) and ri < len(right):
                steps.append((arr.copy(), [i], f'Compare {left[li]} (left) and {right[ri]} (right). Place the smaller one at index {i}.'))
                if left[li] <= right[ri]:
                    arr[i] = left[li]
                    li += 1
                else:
                    arr[i] = right[ri]
                    ri += 1
                steps.append((arr.copy(), [i], f'Inserted value at index {i}.'))
                i += 1
            while li < len(left):
                arr[i] = left[li]
                steps.append((arr.copy(), [i], f'Insert remaining left value {left[li]} at index {i}.'))
                li += 1
                i += 1
            while ri < len(right):
                arr[i] = right[ri]
                steps.append((arr.copy(), [i], f'Insert remaining right value {right[ri]} at index {i}.'))
                ri += 1
                i += 1
        merge_sort_rec(0, len(arr)-1)
        steps.append((arr.copy(), [], 'Merge Sort is finished! The array is sorted.'))
        def finalize():
            self.array = arr
            self.scene.set_values(self.array)
            self.show_feedback('Merge Sort complete.')
        self.play_steps(steps, finalize)

    def quick_sort(self):
        arr = self.array.copy()
        if not self.animations_enabled:
            arr.sort()
            self.array = arr
            self.scene.set_values(self.array, animate=False)
            self.show_feedback('Quick Sort complete.')
            self.step_explanation.setText('')
            return
        steps = [(arr.copy(), [], 'Quick Sort: We pick a pivot value and move all smaller values to the left and larger to the right, then sort each part recursively.')]
        def quick_sort_rec(l, r):
            if l >= r:
                return
            pivot = arr[r]
            steps.append((arr.copy(), [r], f'Choose pivot {pivot} at index {r}.'))
            i = l
            for j in range(l, r):
                steps.append((arr.copy(), [j, r], f'Compare {arr[j]} at index {j} with pivot {pivot}.'))
                if arr[j] < pivot:
                    arr[i], arr[j] = arr[j], arr[i]
                    steps.append((arr.copy(), [i, j], f'Swap {arr[i]} and {arr[j]} so smaller values are on the left.'))
                    i += 1
            arr[i], arr[r] = arr[r], arr[i]
            steps.append((arr.copy(), [i, r], f'Place pivot {pivot} at its correct position at index {i}.'))
            quick_sort_rec(l, i-1)
            quick_sort_rec(i+1, r)
        quick_sort_rec(0, len(arr)-1)
        steps.append((arr.copy(), [], 'Quick Sort is finished! The array is sorted.'))
        def finalize():
            self.array = arr
            self.scene.set_values(self.array)
            self.show_feedback('Quick Sort complete.')
        self.play_steps(steps, finalize)

    # --- Dijkstra's Algorithm ---
    def dijkstra_algorithm(self):
        # Example graph: adjacency list [(neighbor, weight), ...]
        graph = [
            [(1, 2), (2, 4)],    # 0
            [(0, 2), (2, 1), (3, 7)], # 1
            [(0, 4), (1, 1), (3, 3)], # 2
            [(1, 7), (2, 3)]     # 3
        ]
        pos = [(100, 300), (300, 100), (500, 300), (700, 100)]
        n = len(graph)
        dist = [999] * n
        visited = [False] * n
        prev = [None] * n
        steps = []
        start = 0
        dist[start] = 0
        steps.append((dist.copy(), visited.copy(), None, None, f"Start at node {start}. Set its distance to 0. All others are ∞ (infinity)."))
        for _ in range(n):
            # Find the unvisited node with the smallest distance
            u = None
            min_dist = 999
            for i in range(n):
                if not visited[i] and dist[i] < min_dist:
                    min_dist = dist[i]
                    u = i
            if u is None:
                break
            visited[u] = True
            steps.append((dist.copy(), visited.copy(), u, None, f"Pick node {u} (smallest distance not visited). Mark as visited."))
            for v, w in graph[u]:
                if not visited[v]:
                    if dist[u] + w < dist[v]:
                        old = dist[v]
                        dist[v] = dist[u] + w
                        prev[v] = u
                        steps.append((dist.copy(), visited.copy(), v, (u, v), f"Check neighbor {v} of node {u}. Update its distance from {old} to {dist[v]} (via {u})."))
                    else:
                        steps.append((dist.copy(), visited.copy(), v, (u, v), f"Check neighbor {v} of node {u}. No update needed (current distance is shorter)."))
        steps.append((dist.copy(), visited.copy(), None, None, "All nodes visited. Shortest distances from start node are shown."))
        self.dijkstra_steps = steps
        self.dijkstra_current_step = 0
        self.view.setVisible(False)
        self.dijkstra_view.setVisible(True)
        self.play_dijkstra_steps()

    def play_dijkstra_steps(self):
        if self.dijkstra_current_step >= len(self.dijkstra_steps):
            self.dijkstra_view.setVisible(False)
            self.view.setVisible(True)
            if hasattr(self, 'step_explanation') and self.step_explanation and not sip.isdeleted(self.step_explanation):
                self.step_explanation.setText('Dijkstra\'s Algorithm complete!')
            return
        dist, visited, highlight_node, highlight_edge, explanation = self.dijkstra_steps[self.dijkstra_current_step]
        graph = [
            [(1, 2), (2, 4)],
            [(0, 2), (2, 1), (3, 7)],
            [(0, 4), (1, 1), (3, 3)],
            [(1, 7), (2, 3)]
        ]
        pos = [(100, 300), (300, 100), (500, 300), (700, 100)]
        self.dijkstra_scene.draw_graph(graph, pos, distances=dist, visited=visited, highlight_node=highlight_node, highlight_edge=highlight_edge)
        if hasattr(self, 'step_explanation') and self.step_explanation and not sip.isdeleted(self.step_explanation):
            self.step_explanation.setText(explanation)
        self.feedback.setText('')
        self.dijkstra_current_step += 1
        QTimer.singleShot(2000, lambda: (not getattr(self, '_stopped', True) and not sip.isdeleted(self) and self.play_dijkstra_steps(), None)[-1])

    def next_step(self):
        if self.current_step < len(self.steps):
            arr, highlight, explanation = self.steps[self.current_step]
            self.scene.set_values(arr)
            for idx in highlight:
                self.scene.set_box_color(idx, QColor(255, 215, 0))
            self.step_explanation.setText(explanation)
            self.feedback.setText('')
            self.current_step += 1
        if self.current_step >= len(self.steps):
            self.btn_next_step.setVisible(False)

    def stop_animations(self):
        self._stopped = True
        self.animating = False
        self.steps = []
        self.current_step = 0
        if hasattr(self.scene, 'animations'):
            for anim in self.scene.animations:
                anim.stop()
            self.scene.animations.clear()
        # Dijkstra
        if hasattr(self, 'dijkstra_scene') and hasattr(self.dijkstra_scene, 'animations'):
            for anim in self.dijkstra_scene.animations:
                anim.stop()
            self.dijkstra_scene.animations.clear()

    def set_animations_enabled(self, enabled):
        self.animations_enabled = enabled

# --- Add Dijkstra's Algorithm to SortingVisualizer ---
class DijkstraGraphScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 800, 400)
        self.nodes = []
        self.edges = []
        self.node_items = []
        self.edge_items = []
        self.animations = []
        self.dist_labels = []
        self.visited_labels = []

    def clear_scene(self):
        for item in self.node_items + self.edge_items + self.dist_labels + self.visited_labels:
            self.removeItem(item)
        self.node_items = []
        self.edge_items = []
        self.dist_labels = []
        self.visited_labels = []
        self.clear()

    def draw_graph(self, graph, pos, distances=None, visited=None, highlight_node=None, highlight_edge=None):
        self.clear_scene()
        n = len(graph)
        # Draw edges
        for u in range(n):
            for v, w in graph[u]:
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                pen = QPen(QColor(120,120,120), 3)
                if highlight_edge and (u, v) == highlight_edge:
                    pen = QPen(QColor(255, 60, 80), 5)
                line = self.addLine(x1, y1, x2, y2, pen)
                self.edge_items.append(line)
                # Draw weight
                wx, wy = (x1 + x2) / 2, (y1 + y2) / 2
                label = QGraphicsSimpleTextItem(str(w))
                label.setFont(QFont('Arial', 12, QFont.Bold))
                label.setBrush(QBrush(QColor(80, 80, 80)))
                label.setPos(wx, wy)
                self.edge_items.append(label)
        # Draw nodes
        for i, (x, y) in enumerate(pos):
            color = QColor(200, 240, 255) if not visited or not visited[i] else QColor(180, 255, 180)
            if highlight_node == i:
                color = QColor(255, 215, 0)
            ellipse = self.addEllipse(x-20, y-20, 40, 40, QPen(Qt.black, 2), QBrush(color))
            self.node_items.append(ellipse)
            label = QGraphicsSimpleTextItem(str(i))
            label.setFont(QFont('Arial', 16, QFont.Bold))
            label.setPos(x-8, y-16)
            self.node_items.append(label)
            # Distance label
            if distances:
                d = distances[i]
                dist_label = QGraphicsSimpleTextItem(f'dist: {d if d < 999 else "∞"}')
                dist_label.setFont(QFont('Arial', 10))
                dist_label.setBrush(QBrush(QColor(80, 80, 255)))
                dist_label.setPos(x-20, y+22)
                self.dist_labels.append(dist_label)
                self.addItem(dist_label)
            # Visited label
            if visited and visited[i]:
                vlabel = QGraphicsSimpleTextItem('visited')
                vlabel.setFont(QFont('Arial', 10))
                vlabel.setBrush(QBrush(QColor(0, 180, 0)))
                vlabel.setPos(x+10, y-30)
                self.visited_labels.append(vlabel)
                self.addItem(vlabel)

class TutorialWidget(QWidget):
    def __init__(self, on_exit=None):
        super().__init__()
        self.on_exit = on_exit
        self.steps = [
            {
                'title': 'Welcome to Data Structures Visualizer!',
                'content': 'This app helps you learn data structures with interactive visualizations and animations.\n\nClick Next to learn how to use the app.'
            },
            {
                'title': 'Selecting a Visualizer',
                'content': 'From the main menu, choose a data structure (Array, Linked List, Stack, Queue, Sorting) to explore. Each visualizer lets you perform operations and see them step by step.'
            },
            {
                'title': 'Animation Toggle',
                'content': 'Use the "Animations On" checkbox at the bottom left to turn animations and explanations on or off.\n\n- On: See step-by-step animations and explanations.\n- Off: See the result instantly.'
            },
            {
                'title': 'Interacting with Visualizers',
                'content': 'Each visualizer has buttons to add, insert, remove, swap, and more.\n\nTry different operations to see how the data structure changes!'
            },
            {
                'title': 'Scrolling the View',
                'content': 'If the data structure grows large, you can scroll horizontally or vertically in the visualizer area.\n\nUse your mouse or trackpad to scroll and see all elements.'
            },
            {
                'title': 'Going Back and Switching Visualizers',
                'content': 'Use the "Back to Menu" button at the top right of any visualizer to return to the main menu and pick another data structure.'
            },
            {
                'title': 'Enjoy Learning!',
                'content': 'Experiment with different data structures and operations.\n\nIf you need help, revisit this tutorial from the main menu.'
            }
        ]
        self.current_step = 0
        self.init_ui()
        self.update_step()

    def init_ui(self):
        layout = QVBoxLayout()
        self.title_label = QLabel()
        self.title_label.setStyleSheet('font-size: 26px; font-weight: bold; color: #ff1744; margin: 12px;')
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet('font-size: 18px; color: #fff; background: #23232a; border-radius: 10px; padding: 18px; margin: 12px;')
        layout.addWidget(self.title_label)
        layout.addWidget(self.content_label)
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton('Previous')
        self.btn_prev.setStyleSheet('font-size: 16px; padding: 8px 18px; border-radius: 8px;')
        self.btn_prev.clicked.connect(self.prev_step)
        self.btn_next = QPushButton('Next')
        self.btn_next.setStyleSheet('font-size: 16px; padding: 8px 18px; border-radius: 8px;')
        self.btn_next.clicked.connect(self.next_step)
        self.btn_exit = QPushButton('Exit Tutorial')
        self.btn_exit.setStyleSheet('font-size: 16px; padding: 8px 18px; border-radius: 8px; background: #ff1744; color: #fff;')
        self.btn_exit.clicked.connect(self.exit_tutorial)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.btn_exit)
        layout.addLayout(nav_layout)
        self.setLayout(layout)
        self.setMinimumHeight(350)
        self.setMinimumWidth(700)

    def update_step(self):
        step = self.steps[self.current_step]
        self.title_label.setText(step['title'])
        self.content_label.setText(step['content'])
        self.btn_prev.setEnabled(self.current_step > 0)
        self.btn_next.setEnabled(self.current_step < len(self.steps) - 1)

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_step()

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step()

    def exit_tutorial(self):
        if self.on_exit:
            self.on_exit()

class TreeTypeMenu(QWidget):
    def __init__(self, on_select, on_back=None):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel(f"<b style='font-size:28px; color:{ACCENT}; letter-spacing:2px;'>Tree Visualizer</b>")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel(f"<span style='font-size:16px; color:{SUBTEXT_COLOR};'>Pick a tree type to explore:</span>")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        tree_types = [
            ("Binary Search Tree", 'BST'),
            ("Red-Black Tree", 'RBT'),
            ("Min Heap", 'MinHeap'),
            ("Max Heap", 'MaxHeap')
        ]
        for text, ttype in tree_types:
            btn = QPushButton(text)
            btn.setStyleSheet(f"padding:16px; font-size:18px; border-radius:10px; background:{ACCENT}; color:{TEXT_COLOR}; margin:6px;")
            btn.clicked.connect(lambda checked, t=ttype: on_select(t))
            layout.addWidget(btn)
        # Centered, styled Back button
        back_controls = QHBoxLayout()
        back_btn = QPushButton('Back to Menu')
        back_btn.setStyleSheet(f"padding:14px; font-size:18px; border-radius:10px; background:#fff; color:{ACCENT}; font-weight:bold; margin:18px auto 0 auto; min-width:200px;")
        back_btn.setFixedWidth(220)
        back_btn.setCursor(Qt.PointingHandCursor)
        if on_back:
            back_btn.clicked.connect(on_back)
        back_controls.addStretch(1)
        back_controls.addWidget(back_btn)
        back_controls.addStretch(1)
        layout.addLayout(back_controls)
        layout.addStretch(1)
        self.setLayout(layout)

class TreeVisualizer(QWidget):
    def __init__(self, tree_type):
        super().__init__()
        self.tree_type = tree_type
        self.root = None  # Root node of the tree
        self.steps = []  # For step-by-step explanations
        self.current_step = 0
        self.animating = False
        self.animations_enabled = True  # Add this flag
        self.init_ui()

    def set_animations_enabled(self, enabled):
        self.animations_enabled = enabled

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel(f"Tree Visualizer: {self.tree_type}")
        title.setStyleSheet('font-size: 22px; font-weight: bold; margin: 8px;')
        layout.addWidget(title)
        # --- Custom Card for Drawing Area (tall rounded rectangle) ---
        card = QWidget()
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(12, 8, 12, 8)  # Minimal horizontal/vertical padding
        card.setLayout(card_layout)
        card.setStyleSheet('''
            background: #f8f8ff;
            border-radius: 36px;
            border: 2px solid #e0e0e0;
            margin: 0px;
        ''')
        # Graphics view for tree (taller, scrollable)
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 900, 600)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setStyleSheet('background: transparent; border: none;')
        self.view.setMinimumHeight(500)
        self.view.setMaximumHeight(600)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        card_layout.addWidget(self.view)
        layout.addWidget(card)
        # Controls for tree operations (evenly spaced)
        controls = QHBoxLayout()
        controls.setSpacing(24)
        controls.setContentsMargins(24, 8, 24, 8)
        btn_random = QPushButton('Random Tree')
        btn_random.setStyleSheet(f"padding:12px 24px; font-size:16px; border-radius:8px; background:{ACCENT}; color:{TEXT_COLOR};")
        btn_random.clicked.connect(self.generate_random_tree)
        controls.addWidget(btn_random)
        btn_custom = QPushButton('Create Your Own')
        btn_custom.setStyleSheet(f"padding:12px 24px; font-size:16px; border-radius:8px; background:{ACCENT}; color:{TEXT_COLOR};")
        btn_custom.clicked.connect(self.create_own_tree)
        controls.addWidget(btn_custom)
        btn_add = QPushButton('Add Value')
        btn_add.setStyleSheet(f"padding:12px 24px; font-size:16px; border-radius:8px; background:{ACCENT}; color:{TEXT_COLOR};")
        btn_add.clicked.connect(self.add_value)
        controls.addWidget(btn_add)
        btn_remove = QPushButton('Remove Value')
        btn_remove.setStyleSheet(f"padding:12px 24px; font-size:16px; border-radius:8px; background:{ACCENT}; color:{TEXT_COLOR};")
        btn_remove.clicked.connect(self.remove_value)
        controls.addWidget(btn_remove)
        btn_replace = QPushButton('Replace Value')
        btn_replace.setStyleSheet(f"padding:12px 24px; font-size:16px; border-radius:8px; background:{ACCENT}; color:{TEXT_COLOR};")
        btn_replace.clicked.connect(self.replace_value)
        controls.addWidget(btn_replace)
        layout.addLayout(controls)
        # Step explanation and navigation
        self.step_explanation = QLabel('')
        self.step_explanation.setStyleSheet('font-size: 18px; color: #222; background: #e0e7ef; border-radius: 8px; padding: 10px; margin: 10px; font-family: Arial, Helvetica, sans-serif;')
        layout.addWidget(self.step_explanation)
        self.btn_next_step = QPushButton('Next Step')
        self.btn_next_step.setStyleSheet(f"padding:10px 24px; font-size:16px; border-radius:8px; background:{ACCENT}; color:{TEXT_COLOR}; margin:8px auto 0 auto;")
        self.btn_next_step.clicked.connect(self.next_step)
        self.btn_next_step.setVisible(False)
        layout.addWidget(self.btn_next_step, alignment=Qt.AlignCenter)
        # Back button (centered, consistent)
        back_controls = QHBoxLayout()
        back_btn = QPushButton('Back to Tree Menu')
        back_btn.setStyleSheet(f"padding:14px; font-size:18px; border-radius:10px; background:#fff; color:{ACCENT}; font-weight:bold; margin:18px auto 0 auto; min-width:200px;")
        back_btn.setFixedWidth(220)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.parent_back)
        back_controls.addStretch(1)
        back_controls.addWidget(back_btn)
        back_controls.addStretch(1)
        layout.addLayout(back_controls)
        layout.addStretch(1)
        self.setLayout(layout)
        self.setMinimumHeight(500)
        self.setMinimumWidth(900)

    def parent_back(self):
        parent = self.parent()
        while parent and not hasattr(parent, 'show_tree_menu'):
            parent = parent.parent()
        if parent and hasattr(parent, 'show_tree_menu'):
            parent.show_tree_menu()

    def generate_random_tree(self):
        import random
        values = random.sample(range(1, 100), random.randint(5, 9))
        if self.tree_type == 'BST':
            self.root = None
            for v in values:
                self.root = self._bst_insert(self.root, v)
            self._play_steps([(self._tree_snapshot(self.root), [], f"Random BST created: {values}")])
        elif self.tree_type == 'RBT':
            self.root = None
            for v in values:
                self.root = self._rbt_insert(self.root, v)
            self._fix_rbt_colors(self.root)
            self._play_steps([(self._tree_snapshot(self.root), [], f"Random Red-Black Tree created: {values}")])
        elif self.tree_type == 'MinHeap':
            arr = values[:]
            self._heapify(arr, min_heap=True)
            self.root = self._array_to_tree(arr)
            self._play_steps([(self._tree_snapshot(self.root), [], f"Random Min Heap created: {arr}")])
        elif self.tree_type == 'MaxHeap':
            arr = values[:]
            self._heapify(arr, min_heap=False)
            self.root = self._array_to_tree(arr)
            self._play_steps([(self._tree_snapshot(self.root), [], f"Random Max Heap created: {arr}")])
        else:
            self.root = None
            self._play_steps([(self._tree_snapshot(self.root), [], f"Random tree created: {values}")])

    def create_own_tree(self):
        text, ok = QInputDialog.getText(self, 'Create Tree', 'Enter numbers separated by commas:')
        if ok:
            try:
                nums = [int(x.strip()) for x in text.split(',') if x.strip()]
                if self.tree_type == 'BST':
                    self.root = None
                    for v in nums:
                        self.root = self._bst_insert(self.root, v)
                    self._play_steps([(self._tree_snapshot(self.root), [], f"Custom BST created: {nums}")])
                elif self.tree_type == 'RBT':
                    self.root = None
                    for v in nums:
                        self.root = self._rbt_insert(self.root, v)
                    self._fix_rbt_colors(self.root)
                    self._play_steps([(self._tree_snapshot(self.root), [], f"Custom Red-Black Tree created: {nums}")])
                elif self.tree_type == 'MinHeap':
                    arr = nums[:]
                    self._heapify(arr, min_heap=True)
                    self.root = self._array_to_tree(arr)
                    self._play_steps([(self._tree_snapshot(self.root), [], f"Custom Min Heap created: {arr}")])
                elif self.tree_type == 'MaxHeap':
                    arr = nums[:]
                    self._heapify(arr, min_heap=False)
                    self.root = self._array_to_tree(arr)
                    self._play_steps([(self._tree_snapshot(self.root), [], f"Custom Max Heap created: {arr}")])
                else:
                    self.root = None
                    self._play_steps([(self._tree_snapshot(self.root), [], f"Custom tree created: {nums}")])
            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter only numbers separated by commas.')

    # --- Red-Black Tree logic (simplified for visualization) ---
    def _rbt_insert(self, root, value):
        def insert(node, value):
            if not node:
                return TreeNode(value, color='R')
            if value < node.value:
                node.left = insert(node.left, value)
            elif value > node.value:
                node.right = insert(node.right, value)
            return node
        return insert(root, value)

    def _fix_rbt_colors(self, node, parent_color='B'):
        # Post-process: root is black, children of red are black
        if not node:
            return
        if parent_color == 'R':
            node.color = 'B'
        elif node.color is None:
            node.color = 'R'
        if parent_color is None:
            node.color = 'B'  # Root
        if node == self.root:
            node.color = 'B'  # Root always black
        self._fix_rbt_colors(node.left, node.color)
        self._fix_rbt_colors(node.right, node.color)

    # --- Heap logic ---
    def _heapify(self, arr, min_heap=True):
        n = len(arr)
        def heapify_down(i):
            left = 2*i+1
            right = 2*i+2
            smallest = largest = i
            if min_heap:
                if left < n and arr[left] < arr[smallest]:
                    smallest = left
                if right < n and arr[right] < arr[smallest]:
                    smallest = right
                if smallest != i:
                    arr[i], arr[smallest] = arr[smallest], arr[i]
                    heapify_down(smallest)
            else:
                if left < n and arr[left] > arr[largest]:
                    largest = left
                if right < n and arr[right] > arr[largest]:
                    largest = right
                if largest != i:
                    arr[i], arr[largest] = arr[largest], arr[i]
                    heapify_down(largest)
        for i in range(n//2-1, -1, -1):
            heapify_down(i)

    def _array_to_tree(self, arr):
        def build(i):
            if i >= len(arr):
                return None
            node = TreeNode(arr[i])
            node.left = build(2*i+1)
            node.right = build(2*i+2)
            return node
        return build(0)

    def add_value(self):
        num, ok = QInputDialog.getInt(self, 'Add Value', 'Enter a number to add:')
        if not ok:
            return
        if self.tree_type in ('MinHeap', 'MaxHeap'):
            arr = self._tree_to_list(self.root)
            if not self.animations_enabled:
                arr.append(num)
                self._heapify(arr, min_heap=(self.tree_type == 'MinHeap'))
                self.root = self._array_to_tree(arr)
                self._play_steps([(self._tree_snapshot(self.root), [num], f"Added {num} and re-heapified.")])
                return
            # Step-by-step heap insert
            steps = []
            arr.append(num)
            idx = len(arr) - 1
            steps.append((self._array_to_tree(arr), [num], f"Step 1: Insert {num} at the end (index {idx})."))
            def parent(i):
                return (i-1)//2 if i > 0 else None
            min_heap = (self.tree_type == 'MinHeap')
            i = idx
            while i > 0:
                p = parent(i)
                if (min_heap and arr[i] < arr[p]) or (not min_heap and arr[i] > arr[p]):
                    arr[i], arr[p] = arr[p], arr[i]
                    steps.append((self._array_to_tree(arr), [arr[p], arr[i]], f"Step: Swap {arr[i]} (index {i}) with parent {arr[p]} (index {p}) to maintain heap property."))
                    i = p
                else:
                    break
            steps.append((self._array_to_tree(arr), [num], f"Done: {num} added and heap property restored."))
            def finalize():
                self.root = self._array_to_tree(arr)
            self._play_steps(steps, finalize)
        elif self.tree_type == 'RBT':
            if not self.animations_enabled:
                self.root = self._rbt_insert(self.root, num)
                self._fix_rbt_colors(self.root)
                self._play_steps([(self._tree_snapshot(self.root), [num], f"Added {num} to Red-Black Tree.")])
                return
            # Step-by-step RBT insert (simplified)
            steps = []
            arr = self._tree_to_list(self.root)
            # Insert as BST
            bst_steps = []
            node = self.root
            parent = None
            direction = None
            while node:
                parent = node
                if num < node.value:
                    bst_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {num} < {node.value})"))
                    node = node.left
                    direction = 'left'
                elif num > node.value:
                    bst_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {num} > {node.value})"))
                    node = node.right
                    direction = 'right'
                else:
                    bst_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Value {num} already exists in the tree."))
                    self._play_steps(bst_steps)
                    return
            bst_steps.append((self._tree_snapshot(self.root, highlight=[parent.value] if parent else []), [parent.value] if parent else [], f"Insert {num} as {'left' if direction=='left' else 'right'} child of {parent.value if parent else 'root'} (red)."))
            self.root = self._rbt_insert(self.root, num)
            # Now fix colors step by step
            color_steps = []
            def collect_color_fixes(node, parent_color='B'):
                if not node:
                    return
                if parent_color == 'R' and node.color != 'B':
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Fix: Parent is red, so {node.value} must be black."))
                    node.color = 'B'
                elif node.color is None:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Set {node.value} to red (default for new node)."))
                    node.color = 'R'
                if parent_color is None:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Root {node.value} must be black."))
                    node.color = 'B'
                if node == self.root:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Root {node.value} must be black."))
                    node.color = 'B'
                collect_color_fixes(node.left, node.color)
                collect_color_fixes(node.right, node.color)
            collect_color_fixes(self.root, None)
            steps = bst_steps + color_steps
            steps.append((self._tree_snapshot(self.root, highlight=[num]), [num], f"Done: {num} added and Red-Black properties restored."))
            def finalize():
                self._fix_rbt_colors(self.root)
            self._play_steps(steps, finalize)
        else:  # BST
            steps = []
            arr = self._tree_to_list(self.root)
            steps.append((self._tree_snapshot(self.root), [], f"Step 1: Start at root to add {num}.") )
            node = self.root
            parent = None
            direction = None
            while node:
                parent = node
                if num < node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {num} < {node.value})"))
                    node = node.left
                    direction = 'left'
                elif num > node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {num} > {node.value})"))
                    node = node.right
                    direction = 'right'
                else:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Value {num} already exists in the tree."))
                    self._play_steps(steps)
                    return
            steps.append((self._tree_snapshot(self.root, highlight=[parent.value] if parent else []), [parent.value] if parent else [], f"Insert {num} as {'left' if direction=='left' else 'right'} child of {parent.value if parent else 'root'}"))
            self.root = self._bst_insert(self.root, num)
            steps.append((self._tree_snapshot(self.root, highlight=[num]), [num], f"Done. {num} added to the tree."))
            self._play_steps(steps)

    def remove_value(self):
        num, ok = QInputDialog.getInt(self, 'Remove Value', 'Enter a number to remove:')
        if not ok:
            return
        if self.tree_type in ('MinHeap', 'MaxHeap'):
            arr = self._tree_to_list(self.root)
            if num not in arr:
                self._play_steps([(self._tree_snapshot(self.root), [], f"Value {num} not found in the heap.")])
                return
            if not self.animations_enabled:
                arr.remove(num)
                self._heapify(arr, min_heap=(self.tree_type == 'MinHeap'))
                self.root = self._array_to_tree(arr)
                self._play_steps([(self._tree_snapshot(self.root), [], f"Removed {num} and re-heapified.")])
                return
            # Step-by-step heap remove
            steps = []
            idx = arr.index(num)
            arr[idx], arr[-1] = arr[-1], arr[idx]
            removed = arr.pop()
            steps.append((self._array_to_tree(arr), [], f"Step 1: Swap {num} (index {idx}) with last element and remove it."))
            n = len(arr)
            min_heap = (self.tree_type == 'MinHeap')
            i = idx
            def left(i): return 2*i+1
            def right(i): return 2*i+2
            while True:
                l, r = left(i), right(i)
                swap_idx = i
                if min_heap:
                    if l < n and arr[l] < arr[swap_idx]:
                        swap_idx = l
                    if r < n and arr[r] < arr[swap_idx]:
                        swap_idx = r
                else:
                    if l < n and arr[l] > arr[swap_idx]:
                        swap_idx = l
                    if r < n and arr[r] > arr[swap_idx]:
                        swap_idx = r
                if swap_idx == i:
                    break
                arr[i], arr[swap_idx] = arr[swap_idx], arr[i]
                steps.append((self._array_to_tree(arr), [arr[i], arr[swap_idx]], f"Step: Swap {arr[swap_idx]} (index {swap_idx}) with {arr[i]} (index {i}) to maintain heap property."))
                i = swap_idx
            steps.append((self._array_to_tree(arr), [], f"Done: {num} removed and heap property restored."))
            def finalize():
                self.root = self._array_to_tree(arr)
            self._play_steps(steps, finalize)
        elif self.tree_type == 'RBT':
            if not self.animations_enabled:
                self.root = self._bst_remove(self.root, num)
                self._fix_rbt_colors(self.root)
                self._play_steps([(self._tree_snapshot(self.root), [], f"Removed {num} from Red-Black Tree.")])
                return
            # Step-by-step RBT remove (simplified)
            steps = []
            node = self.root
            parent = None
            found = False
            while node:
                if num < node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {num} < {node.value})"))
                    parent = node
                    node = node.left
                elif num > node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {num} > {node.value})"))
                    parent = node
                    node = node.right
                else:
                    found = True
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Found {num} in the tree. Removing it."))
                    break
            if not found:
                steps.append((self._tree_snapshot(self.root), [], f"Value {num} not found in the tree."))
                self._play_steps(steps)
                return
            self.root = self._bst_remove(self.root, num)
            # Now fix colors step by step
            color_steps = []
            def collect_color_fixes(node, parent_color='B'):
                if not node:
                    return
                if parent_color == 'R' and node.color != 'B':
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Fix: Parent is red, so {node.value} must be black."))
                    node.color = 'B'
                elif node.color is None:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Set {node.value} to red (default for new node)."))
                    node.color = 'R'
                if parent_color is None:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Root {node.value} must be black."))
                    node.color = 'B'
                if node == self.root:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Root {node.value} must be black."))
                    node.color = 'B'
                collect_color_fixes(node.left, node.color)
                collect_color_fixes(node.right, node.color)
            collect_color_fixes(self.root, None)
            steps += color_steps
            steps.append((self._tree_snapshot(self.root), [], f"Done: {num} removed and Red-Black properties restored."))
            def finalize():
                self._fix_rbt_colors(self.root)
            self._play_steps(steps, finalize)
        else:
            steps = []
            node = self.root
            parent = None
            found = False
            while node:
                if num < node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {num} < {node.value})"))
                    parent = node
                    node = node.left
                elif num > node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {num} > {node.value})"))
                    parent = node
                    node = node.right
                else:
                    found = True
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Found {num} in the tree. Removing it."))
                    break
            if not found:
                steps.append((self._tree_snapshot(self.root), [], f"Value {num} not found in the tree."))
                self._play_steps(steps)
                return
            self.root = self._bst_remove(self.root, num)
            steps.append((self._tree_snapshot(self.root), [], f"Done. {num} removed from the tree."))
            self._play_steps(steps)

    def replace_value(self):
        old, ok1 = QInputDialog.getInt(self, 'Replace Value', 'Value to replace:')
        if not ok1:
            return
        new, ok2 = QInputDialog.getInt(self, 'Replace Value', 'New value:')
        if not ok2:
            return
        if old == new:
            QMessageBox.warning(self, 'Invalid', 'Old and new values are the same.')
            return
        if self.tree_type in ('MinHeap', 'MaxHeap'):
            arr = self._tree_to_list(self.root)
            if old not in arr:
                self._play_steps([(self._tree_snapshot(self.root), [], f"Value {old} not found in the heap.")])
                return
            if not self.animations_enabled:
                arr[arr.index(old)] = new
                self._heapify(arr, min_heap=(self.tree_type == 'MinHeap'))
                self.root = self._array_to_tree(arr)
                self._play_steps([(self._tree_snapshot(self.root), [new], f"Replaced {old} with {new} and re-heapified.")])
                return
            # Step-by-step heap replace
            steps = []
            idx = arr.index(old)
            arr[idx] = new
            steps.append((self._array_to_tree(arr), [new], f"Step 1: Replace {old} with {new} at index {idx}."))
            # Heapify up
            min_heap = (self.tree_type == 'MinHeap')
            def parent(i): return (i-1)//2 if i > 0 else None
            i = idx
            up = False
            while i > 0:
                p = parent(i)
                if (min_heap and arr[i] < arr[p]) or (not min_heap and arr[i] > arr[p]):
                    arr[i], arr[p] = arr[p], arr[i]
                    steps.append((self._array_to_tree(arr), [arr[p], arr[i]], f"Step: Swap {arr[i]} (index {i}) with parent {arr[p]} (index {p}) to maintain heap property (heapify up)."))
                    i = p
                    up = True
                else:
                    break
            if not up:
                # Heapify down
                n = len(arr)
                i = idx
                def left(i): return 2*i+1
                def right(i): return 2*i+2
                while True:
                    l, r = left(i), right(i)
                    swap_idx = i
                    if min_heap:
                        if l < n and arr[l] < arr[swap_idx]:
                            swap_idx = l
                        if r < n and arr[r] < arr[swap_idx]:
                            swap_idx = r
                    else:
                        if l < n and arr[l] > arr[swap_idx]:
                            swap_idx = l
                        if r < n and arr[r] > arr[swap_idx]:
                            swap_idx = r
                    if swap_idx == i:
                        break
                    arr[i], arr[swap_idx] = arr[swap_idx], arr[i]
                    steps.append((self._array_to_tree(arr), [arr[i], arr[swap_idx]], f"Step: Swap {arr[swap_idx]} (index {swap_idx}) with {arr[i]} (index {i}) to maintain heap property (heapify down)."))
                    i = swap_idx
            steps.append((self._array_to_tree(arr), [new], f"Done: {old} replaced with {new} and heap property restored."))
            def finalize():
                self.root = self._array_to_tree(arr)
            self._play_steps(steps, finalize)
        elif self.tree_type == 'RBT':
            if not self.animations_enabled:
                self.root = self._bst_remove(self.root, old)
                self.root = self._rbt_insert(self.root, new)
                self._fix_rbt_colors(self.root)
                self._play_steps([(self._tree_snapshot(self.root), [new], f"Replaced {old} with {new} in Red-Black Tree.")])
                return
            # Step-by-step RBT replace (remove + insert)
            steps = []
            # Remove old
            node = self.root
            found = False
            while node:
                if old < node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {old} < {node.value})"))
                    node = node.left
                elif old > node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {old} > {node.value})"))
                    node = node.right
                else:
                    found = True
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Found {old}. Removing it."))
                    break
            if not found:
                steps.append((self._tree_snapshot(self.root), [], f"Value {old} not found in the tree."))
                self._play_steps(steps)
                return
            self.root = self._bst_remove(self.root, old)
            # Insert new
            node = self.root
            parent = None
            direction = None
            while node:
                parent = node
                if new < node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {new} < {node.value})"))
                    node = node.left
                    direction = 'left'
                elif new > node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {new} > {node.value})"))
                    node = node.right
                    direction = 'right'
                else:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Value {new} already exists in the tree."))
                    self._play_steps(steps)
                    return
            steps.append((self._tree_snapshot(self.root, highlight=[parent.value] if parent else []), [parent.value] if parent else [], f"Insert {new} as {'left' if direction=='left' else 'right'} child of {parent.value if parent else 'root'} (red)."))
            self.root = self._rbt_insert(self.root, new)
            # Now fix colors step by step
            color_steps = []
            def collect_color_fixes(node, parent_color='B'):
                if not node:
                    return
                if parent_color == 'R' and node.color != 'B':
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Fix: Parent is red, so {node.value} must be black."))
                    node.color = 'B'
                elif node.color is None:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Set {node.value} to red (default for new node)."))
                    node.color = 'R'
                if parent_color is None:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Root {node.value} must be black."))
                    node.color = 'B'
                if node == self.root:
                    color_steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Root {node.value} must be black."))
                    node.color = 'B'
                collect_color_fixes(node.left, node.color)
                collect_color_fixes(node.right, node.color)
            collect_color_fixes(self.root, None)
            steps += color_steps
            steps.append((self._tree_snapshot(self.root, highlight=[new]), [new], f"Done: {old} replaced with {new} and Red-Black properties restored."))
            def finalize():
                self._fix_rbt_colors(self.root)
            self._play_steps(steps, finalize)
        else:
            steps = []
            node = self.root
            found = False
            while node:
                if old < node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {old} < {node.value})"))
                    node = node.left
                elif old > node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {old} > {node.value})"))
                    node = node.right
                else:
                    found = True
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Found {old}. Removing it."))
                    break
            if not found:
                steps.append((self._tree_snapshot(self.root), [], f"Value {old} not found in the tree."))
                self._play_steps(steps)
                return
            self.root = self._bst_remove(self.root, old)
            steps.append((self._tree_snapshot(self.root), [], f"Removed {old}. Now add {new} to the tree."))
            node = self.root
            parent = None
            direction = None
            while node:
                parent = node
                if new < node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go left from {node.value} (since {new} < {node.value})"))
                    node = node.left
                    direction = 'left'
                elif new > node.value:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Go right from {node.value} (since {new} > {node.value})"))
                    node = node.right
                    direction = 'right'
                else:
                    steps.append((self._tree_snapshot(self.root, highlight=[node.value]), [node.value], f"Value {new} already exists in the tree."))
                    self._play_steps(steps)
                    return
            steps.append((self._tree_snapshot(self.root, highlight=[parent.value] if parent else []), [parent.value] if parent else [], f"Insert {new} as {'left' if direction=='left' else 'right'} child of {parent.value if parent else 'root'}"))
            self.root = self._bst_insert(self.root, new)
            steps.append((self._tree_snapshot(self.root, highlight=[new]), [new], f"Done. {old} replaced with {new} in the tree."))
            self._play_steps(steps)

    def _play_steps(self, steps):
        # Ensure all steps are (tree_snapshot, highlight, explanation)
        self.steps = []
        for step in steps:
            if len(step) == 3:
                self.steps.append(step)
            elif len(step) == 2:
                self.steps.append((step[0], step[1], ""))
            elif len(step) == 1:
                self.steps.append((step[0], [], ""))
        self.current_step = 0
        self.animating = True
        self.btn_next_step.setVisible(True)
        self._show_step()

    def _show_step(self):
        if self.current_step >= len(self.steps):
            self.animating = False
            self.btn_next_step.setVisible(False)
            return
        tree_snapshot, highlight, explanation = self.steps[self.current_step]
        if highlight is None:
            highlight = []
        self._draw_tree_snapshot(tree_snapshot, highlight)
        self.step_explanation.setText(explanation)

    def next_step(self):
        if self.current_step < len(self.steps):
            self.current_step += 1
            self._show_step()

    # --- Tree logic and helpers ---
    def _bst_insert(self, node, value):
        if not node:
            return TreeNode(value)
        if value < node.value:
            node.left = self._bst_insert(node.left, value)
        elif value > node.value:
            node.right = self._bst_insert(node.right, value)
        return node

    def _bst_remove(self, node, value):
        if not node:
            return None
        if value < node.value:
            node.left = self._bst_remove(node.left, value)
        elif value > node.value:
            node.right = self._bst_remove(node.right, value)
        else:
            if not node.left:
                return node.right
            if not node.right:
                return node.left
            # Node with two children: get inorder successor
            min_larger = node.right
            while min_larger.left:
                min_larger = min_larger.left
            node.value = min_larger.value
            node.right = self._bst_remove(node.right, min_larger.value)
        return node

    def _tree_to_list(self, node):
        if not node:
            return []
        return self._tree_to_list(node.left) + [node.value] + self._tree_to_list(node.right)

    def _tree_snapshot(self, node, highlight=None):
        # Returns a copy of the tree for visualization, with highlight info
        # For now, just return the node; highlight is a list of values to highlight
        return (self._copy_tree(node), highlight or [])

    def _copy_tree(self, node):
        if not node:
            return None
        # Copy color property as well for RBT
        return TreeNode(node.value, self._copy_tree(node.left), self._copy_tree(node.right), color=getattr(node, 'color', None))

    def _draw_tree_snapshot(self, tree_snapshot, highlight):
        # Accepts either (node, highlight_vals) or just node
        if isinstance(tree_snapshot, tuple) and len(tree_snapshot) == 2:
            node, highlight_vals = tree_snapshot
        else:
            node = tree_snapshot
            highlight_vals = highlight or []
        self.scene.clear()
        if not node:
            return
        # Use a simple recursive layout: assign x/y positions by in-order traversal
        positions = {}
        levels = {}
        def layout(node, depth, x):
            if not node:
                return x
            x = layout(node.left, depth+1, x)
            positions[node] = (x, depth)
            levels.setdefault(depth, []).append(node)
            x += 1
            x = layout(node.right, depth+1, x)
            return x
        layout(node, 0, 0)
        # Draw edges first
        for n, (x, y) in positions.items():
            if n.left:
                x1, y1 = x, y
                x2, y2 = positions[n.left]
                self.scene.addLine(100 + x1*80, 60 + y1*80, 100 + x2*80, 60 + y2*80, QPen(QColor(120,120,120), 3))
            if n.right:
                x1, y1 = x, y
                x2, y2 = positions[n.right]
                self.scene.addLine(100 + x1*80, 60 + y1*80, 100 + x2*80, 60 + y2*80, QPen(QColor(120,120,120), 3))
        # Draw nodes
        for n, (x, y) in positions.items():
            node_x = 100 + x*80
            node_y = 60 + y*80
            radius = 28
            # --- RBT Node Coloring ---
            if getattr(n, 'color', None) == 'R':
                fill = QColor(255, 60, 80)  # Red fill
                text_color = QColor(255,255,255)  # White text
            elif getattr(n, 'color', None) == 'B':
                fill = QColor(40, 40, 40)  # Black fill
                text_color = QColor(255,255,255)  # White text
            else:
                fill = QColor(255,255,255)  # Default white fill
                text_color = QColor(40,40,40)  # Dark text
            # Highlight overrides fill
            if n.value in highlight_vals:
                fill = QColor(255, 215, 0)  # Gold highlight
                text_color = QColor(40,40,40)
            ellipse = self.scene.addEllipse(node_x-radius, node_y-radius, 2*radius, 2*radius, QPen(QColor(80,80,80), 3), QBrush(fill))
            label = QGraphicsSimpleTextItem(str(n.value))
            label.setFont(QFont('Arial', 16, QFont.Bold))
            label.setBrush(QBrush(text_color))
            label.setPos(node_x-10, node_y-16)
            self.scene.addItem(label)

class TreeNode:
    """Simple binary tree node for visualization demo purposes."""
    def __init__(self, value, left=None, right=None, color=None):
        self.value = value
        self.left = left
        self.right = right
        self.color = color  # For Red-Black Tree: 'R' or 'B', None for others

def main():
    app = QApplication([])
    app.setStyleSheet(f'''
        QPushButton {{
            background: {ACCENT};
            color: {TEXT_COLOR};
            border-radius: 10px;
            font-size: 16px;
            padding: 10px 20px;
        }}
        QPushButton:hover {{
            background: #ff4569;
        }}
        QLabel {{
            font-family: Arial, Helvetica, sans-serif;
            color: {TEXT_COLOR};
        }}
        QWidget {{
            background: {PRIMARY_BG};
        }}
    ''')
    window = ModernMainWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main() 