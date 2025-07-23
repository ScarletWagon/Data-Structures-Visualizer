# Data Structures Visualizer

**Data Structures Visualizer** is an interactive desktop application for visualizing and learning about fundamental data structures and algorithms. It provides step-by-step animations, explanations, and a modern UI for exploring arrays, linked lists, stacks, queues, sorting algorithms, and trees (including BSTs, Red-Black Trees, Heaps).

## Features

- **Array Visualizer**
  - Add, insert, remove, and swap elements
  - Animated box layout and temporary variable visualization
  - Step-by-step explanations for operations

- **Singly Linked List Visualizer**
  - Add, insert, remove, and swap nodes
  - Animated node layout and arrow updates
  - Step-by-step traversal and pointer updates

- **Doubly Linked List Visualizer**
  - Add, insert, remove, and swap nodes
  - Visualizes both next and previous pointers
  - Head and tail labels for clarity

- **Stack Visualizer (Bookshelf)**
  - Push, pop, and replace values
  - Animated stack layout with top label
  - Step explanations for stack operations

- **Queue Visualizer**
  - Enqueue, dequeue, replace, and swap elements
  - Animated queue layout with front label
  - Step-by-step feedback for queue operations

- **Sorting Visualizer**
  - Bubble, Selection, Insertion, Merge, and Quick Sort
  - Dijkstra's Algorithm visualization
  - Step-by-step sorting animations and explanations

- **Tree Visualizer**
  - Supports Binary Search Tree, Red-Black Tree, Min Heap, Max Heap
  - Add, remove, and replace values
  - Animated tree layout, node coloring (for RBT), and heap property restoration
  - Step-by-step explanations for tree operations

- **Tutorial**
  - Built-in tutorial widget to guide new users
  - Explains how to use each visualizer and interact with the UI

- **Modern UI**
  - Consistent, visually appealing interface
  - Scrollable views for large data structures
  - Animation toggle for instant or step-by-step mode
  - Back buttons for easy navigation

## Getting Started

### Requirements

- Python 3.7+
- PyQt5 (or PySide2)

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/data-structures-visualizer.git
    cd data-structures-visualizer
    ```

2. Install dependencies:
    ```sh
    pip install PyQt5
    ```

### Running the Application

```sh
python "data visualizer/main.py"
```

## File Structure

- `data visualizer/main.py` — Main application source code
- `.gitattributes` — Git configuration
- `README.md` — Project documentation

## How to Use

1. Launch the app and select a data structure from the main menu.
2. Use the provided buttons to perform operations (add, insert, remove, swap, etc.).
3. Toggle animations on/off using the checkbox at the bottom left.
4. Use the "Next Step" button to advance through explanations.
5. Access the tutorial from the main menu for guidance.

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements or new features.

## License

This project is licensed under the MIT License.

---

Enjoy learning data structures visually!