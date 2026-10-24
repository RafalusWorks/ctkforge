# CTkForge

Custom extension widgets for [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter): high-performance data table, popups / messageboxes, and spinbox.

[![PyPI version](https://img.shields.io/pypi/v/ctkforge.svg)](https://pypi.org/project/ctkforge/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![CTkForge Preview](docs/assets/ctkforge_preview.jpg)

## Installation

```bash
pip install ctkforge
```

## Components

| Component | Description | Documentation |
| :--- | :--- | :--- |
| [**CTkTable**](docs/table.md) | High-performance data table with smart sorting, row/cell selection, cell editing, and clipboard support. | [API Reference](docs/table.md) • [User Guide](docs/table_user_guide.md) |
| [**CTkPopup**](docs/popup.md) | Modern modal dialogs for alerts, confirmations, and errors with auto-scrolling and keyboard shortcuts. | [API Reference](docs/popup.md) • [User Guide](docs/popup_user_guide.md) |
| [**CTkSpinbox**](docs/spinbox.md) | Numeric input widget with classic arrow steppers, mouse wheel control, limits, and custom steps. | [API Reference](docs/spinbox.md) |
| [**Utilities**](docs/utilities.md) | High-DPI screen coordinate unscaling (`unscale`) and PyInstaller asset path resolution (`resource_path`). | [Utilities Reference](docs/utilities.md) |

## Interactive Examples

Runnable example scripts are available in the [`examples/`](examples/) folder:

* [`example_ctktable.py`](examples/example_ctktable.py) — Table sorting, editing, and selection
* [`demo_ctkpopup_basic.py`](examples/demo_ctkpopup_basic.py) — Modal dialog presets and result handling
* [`demo_ctkspinbox.py`](examples/demo_ctkspinbox.py) — Number steppers and styling variations
* [`demo_ctktable_clipboard_and_crud.py`](examples/demo_ctktable_clipboard_and_crud.py) — Advanced table CRUD and clipboard integration

---

<p align="center">Crafted and maintained by <b>Rafalus</b>. Happy forging!</p>
