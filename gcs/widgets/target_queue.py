# Target Queue Widget for SwarmDrones GCS
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QTableWidget, QTableWidgetItem,
                              QPushButton, QHeaderView, QAbstractItemView,
                              QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
                              QComboBox, QTextEdit, QSplitter, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


def parse_coordinate(coord_str: str, coord_type: str = "lat") -> float:
    """
    Parse coordinate string in multiple formats.
    Supports: DDD.DDDD, DD MM.MMMM, MGRS (partial)
    All coordinates use WGS84 datum.

    Args:
        coord_str: Coordinate string
        coord_type: "lat" or "lon" for hemisphere handling

    Returns:
        Decimal degrees float
    """
    coord_str = coord_str.strip().upper()

    # Check for hemisphere indicator
    negative = False
    if coord_str.endswith(('S', 'W')):
        negative = True
        coord_str = coord_str[:-1].strip()
    elif coord_str.endswith(('N', 'E')):
        coord_str = coord_str[:-1].strip()
    elif coord_str.startswith('-'):
        negative = True
        coord_str = coord_str[1:].strip()

    # Try DDD.DDDD format (decimal degrees)
    try:
        value = float(coord_str)
        return -value if negative else value
    except ValueError:
        pass

    # Try DD MM.MMMM format (degrees decimal minutes)
    ddm_match = re.match(r'^(\d+)[°\s]+(\d+\.?\d*)[\'′]?$', coord_str)
    if ddm_match:
        degrees = float(ddm_match.group(1))
        minutes = float(ddm_match.group(2))
        value = degrees + (minutes / 60.0)
        return -value if negative else value

    # Try DD MM SS.SS format (degrees minutes seconds)
    dms_match = re.match(r'^(\d+)[°\s]+(\d+)[\'′\s]+(\d+\.?\d*)[\"″]?$', coord_str)
    if dms_match:
        degrees = float(dms_match.group(1))
        minutes = float(dms_match.group(2))
        seconds = float(dms_match.group(3))
        value = degrees + (minutes / 60.0) + (seconds / 3600.0)
        return -value if negative else value

    raise ValueError(f"Cannot parse coordinate: {coord_str}")


def parse_mgrs(mgrs_str: str) -> tuple:
    """
    Parse MGRS coordinate string.
    Example: 31U DQ 48251 11932

    Returns:
        (lat, lon) in decimal degrees
    """
    # Basic MGRS parsing - for full support would need mgrs library
    # pip install mgrs
    try:
        import mgrs
        m = mgrs.MGRS()
        lat, lon = m.toLatLon(mgrs_str.replace(' ', ''))
        return lat, lon
    except ImportError:
        raise ValueError("MGRS library not installed. Run: pip install mgrs")
    except Exception as e:
        raise ValueError(f"Invalid MGRS: {e}")


def format_ddm(lat: float, lon: float) -> str:
    """Format coordinates as DD MM.MMMM"""
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    lat = abs(lat)
    lon = abs(lon)
    lat_deg = int(lat)
    lat_min = (lat - lat_deg) * 60
    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60
    return f"{lat_deg:02d} {lat_min:06.3f}{lat_dir}  {lon_deg:03d} {lon_min:06.3f}{lon_dir}"


class ManualCoordDialog(QDialog):
    """Dialog for manual coordinate entry with multiple format support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual Coordinate Entry")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Decimal Degrees (DDD.DDDD)",
            "Degrees Decimal Minutes (DD MM.MMMM)",
            "MGRS"
        ])
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)

        # Datum note
        datum_label = QLabel("Datum: WGS84")
        datum_label.setStyleSheet("color: #808080; font-size: 10px;")
        layout.addWidget(datum_label)

        # Coordinate inputs - stacked layouts for different formats
        self.coord_stack = QWidget()
        stack_layout = QVBoxLayout(self.coord_stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)

        # DDD.DDDD format
        self.dd_widget = QWidget()
        dd_layout = QFormLayout(self.dd_widget)
        dd_layout.setContentsMargins(0, 0, 0, 0)
        self.lat_dd = QLineEdit()
        self.lat_dd.setPlaceholderText("52.1234 or 52.1234N")
        dd_layout.addRow("Latitude:", self.lat_dd)
        self.lon_dd = QLineEdit()
        self.lon_dd.setPlaceholderText("-1.5678 or 1.5678W")
        dd_layout.addRow("Longitude:", self.lon_dd)
        stack_layout.addWidget(self.dd_widget)

        # DD MM.MMMM format
        self.ddm_widget = QWidget()
        ddm_layout = QFormLayout(self.ddm_widget)
        ddm_layout.setContentsMargins(0, 0, 0, 0)
        self.lat_ddm = QLineEdit()
        self.lat_ddm.setPlaceholderText("52 07.404N")
        ddm_layout.addRow("Latitude:", self.lat_ddm)
        self.lon_ddm = QLineEdit()
        self.lon_ddm.setPlaceholderText("001 34.068W")
        ddm_layout.addRow("Longitude:", self.lon_ddm)
        stack_layout.addWidget(self.ddm_widget)
        self.ddm_widget.hide()

        # MGRS format
        self.mgrs_widget = QWidget()
        mgrs_layout = QFormLayout(self.mgrs_widget)
        mgrs_layout.setContentsMargins(0, 0, 0, 0)
        self.mgrs_input = QLineEdit()
        self.mgrs_input.setPlaceholderText("31U DQ 48251 11932")
        mgrs_layout.addRow("MGRS:", self.mgrs_input)
        stack_layout.addWidget(self.mgrs_widget)
        self.mgrs_widget.hide()

        layout.addWidget(self.coord_stack)

        # Name and description
        layout.addSpacing(10)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Optional custom name")
        form.addRow("Name:", self.name_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optional description or notes")
        self.desc_input.setMaximumHeight(60)
        form.addRow("Description:", self.desc_input)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_format_changed(self, index):
        """Switch between coordinate format inputs."""
        self.dd_widget.setVisible(index == 0)
        self.ddm_widget.setVisible(index == 1)
        self.mgrs_widget.setVisible(index == 2)

    def get_coordinates(self) -> tuple:
        """
        Get entered coordinates and metadata.
        Returns: (lat, lon, name, description) or (None, None, "", "") on error
        """
        try:
            fmt = self.format_combo.currentIndex()

            if fmt == 0:  # Decimal degrees
                lat = parse_coordinate(self.lat_dd.text(), "lat")
                lon = parse_coordinate(self.lon_dd.text(), "lon")
            elif fmt == 1:  # DD MM.MMMM
                lat = parse_coordinate(self.lat_ddm.text(), "lat")
                lon = parse_coordinate(self.lon_ddm.text(), "lon")
            else:  # MGRS
                lat, lon = parse_mgrs(self.mgrs_input.text())

            name = self.name_input.text().strip()
            desc = self.desc_input.toPlainText().strip()

            return lat, lon, name, desc

        except (ValueError, Exception) as e:
            print(f"[Coord Parse Error] {e}")
            return None, None, "", ""


class TargetDetailPanel(QFrame):
    """Panel showing details of selected target."""

    name_changed = pyqtSignal(str, str)  # target_id, new_name
    description_changed = pyqtSignal(str, str)  # target_id, new_description

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._current_target_id = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QLabel("TARGET DETAILS")
        header.setObjectName("header")
        layout.addWidget(header)

        # Info grid
        info_layout = QFormLayout()
        info_layout.setSpacing(2)

        self.coord_label = QLabel("--")
        self.coord_label.setStyleSheet("color: #60a5fa;")
        info_layout.addRow("Coords:", self.coord_label)

        self.ddm_label = QLabel("--")
        self.ddm_label.setStyleSheet("color: #808080; font-size: 10px;")
        info_layout.addRow("DDM:", self.ddm_label)

        self.source_label = QLabel("--")
        info_layout.addRow("Source:", self.source_label)

        self.orb_label = QLabel("--")
        info_layout.addRow("Orb:", self.orb_label)

        layout.addLayout(info_layout)

        # Editable name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter custom name")
        self.name_edit.editingFinished.connect(self._on_name_changed)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Enter description or notes")
        self.desc_edit.setMaximumHeight(50)
        layout.addWidget(self.desc_edit)

        # Save description button
        save_btn = QPushButton("Save Description")
        save_btn.clicked.connect(self._on_desc_changed)
        layout.addWidget(save_btn)

        layout.addStretch()

        # Datum note
        datum_label = QLabel("WGS84 datum")
        datum_label.setStyleSheet("color: #606060; font-size: 9px;")
        datum_label.setAlignment(Qt.AlignRight)
        layout.addWidget(datum_label)

    def update_target(self, target_id: str, lat: float, lon: float,
                      source: str, orb_id: str, name: str, description: str):
        """Update panel with target details."""
        self._current_target_id = target_id

        self.coord_label.setText(f"{lat:.5f}, {lon:.5f}")
        self.ddm_label.setText(format_ddm(lat, lon))
        self.source_label.setText(source)
        self.orb_label.setText(f"ORB{orb_id}" if orb_id else "--")

        self.name_edit.setText(name)
        self.desc_edit.setText(description)

    def clear(self):
        """Clear the panel."""
        self._current_target_id = None
        self.coord_label.setText("--")
        self.ddm_label.setText("--")
        self.source_label.setText("--")
        self.orb_label.setText("--")
        self.name_edit.clear()
        self.desc_edit.clear()

    def _on_name_changed(self):
        """Handle name edit finished."""
        if self._current_target_id:
            self.name_changed.emit(self._current_target_id, self.name_edit.text())

    def _on_desc_changed(self):
        """Handle description save."""
        if self._current_target_id:
            self.description_changed.emit(self._current_target_id, self.desc_edit.toPlainText())


class TargetQueueWidget(QFrame):
    """Widget showing target queue."""

    target_selected = pyqtSignal(str)  # target_id
    manual_entry_requested = pyqtSignal()
    target_removed = pyqtSignal(str)  # target_id
    target_renamed = pyqtSignal(str, str)  # target_id, new_name
    target_description_changed = pyqtSignal(str, str)  # target_id, new_description

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self._selected_id = None
        self._targets_data = []  # Store full target data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QHBoxLayout()
        title = QLabel("TARGET QUEUE")
        title.setObjectName("header")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Splitter for table and details
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)

        # Table container
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["NAME", "COORDINATES", "SOURCE", "ORB"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_double_click)
        self.table.setMinimumHeight(80)
        table_layout.addWidget(self.table)

        splitter.addWidget(table_container)

        # Target detail panel
        self.detail_panel = TargetDetailPanel()
        self.detail_panel.name_changed.connect(self.target_renamed.emit)
        self.detail_panel.description_changed.connect(self.target_description_changed.emit)
        self.detail_panel.setMinimumWidth(180)
        self.detail_panel.setMaximumWidth(250)
        splitter.addWidget(self.detail_panel)

        splitter.setSizes([300, 200])
        layout.addWidget(splitter)

        # Buttons
        btn_layout = QHBoxLayout()

        manual_btn = QPushButton("MANUAL COORD ENTRY")
        manual_btn.clicked.connect(self.manual_entry_requested.emit)
        btn_layout.addWidget(manual_btn)

        btn_layout.addStretch()

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._on_remove_clicked)
        btn_layout.addWidget(remove_btn)

        layout.addLayout(btn_layout)

    def _on_selection_changed(self):
        """Handle table selection change."""
        rows = self.table.selectedItems()
        if rows:
            row = rows[0].row()
            if row < len(self._targets_data):
                data = self._targets_data[row]
                self._selected_id = data['id']
                self.target_selected.emit(self._selected_id)

                # Update detail panel
                self.detail_panel.update_target(
                    data['id'], data['lat'], data['lon'],
                    data['source'], data['orb_id'],
                    data['name'], data['description']
                )

    def _on_double_click(self, item):
        """Handle double click on table item - edit name."""
        if item.column() == 0 and self._selected_id:
            from PyQt5.QtWidgets import QInputDialog
            current_name = item.text().replace("◎", "")
            new_name, ok = QInputDialog.getText(
                self, "Rename Target",
                "Enter new name:",
                text=current_name
            )
            if ok and new_name:
                self.target_renamed.emit(self._selected_id, new_name)

    def _on_remove_clicked(self):
        """Handle remove button click."""
        if self._selected_id:
            self.target_removed.emit(self._selected_id)

    def update_targets(self, targets: list):
        """
        Update the target list.
        targets: [(id, lat, lon, source, orb_id, name, description)]
        """
        self._targets_data = []
        self.table.setRowCount(len(targets))

        for i, target_data in enumerate(targets):
            # Handle both old (5-tuple) and new (7-tuple) formats
            if len(target_data) == 5:
                tid, lat, lon, source, orb_id = target_data
                name, description = "", ""
            else:
                tid, lat, lon, source, orb_id, name, description = target_data

            self._targets_data.append({
                'id': tid,
                'lat': lat,
                'lon': lon,
                'source': source,
                'orb_id': orb_id,
                'name': name,
                'description': description
            })

            # Name/ID column
            display_name = name if name else f"TGT{tid}"
            id_item = QTableWidgetItem(f"◎{display_name}")
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, id_item)

            # Coordinates
            coord_item = QTableWidgetItem(f"{lat:.4f}, {lon:.4f}")
            self.table.setItem(i, 1, coord_item)

            # Source
            source_item = QTableWidgetItem(source)
            source_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, source_item)

            # Orb assignment
            orb_text = f"ORB{orb_id}" if orb_id else "--"
            orb_item = QTableWidgetItem(orb_text)
            orb_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 3, orb_item)

        # Restore selection and update details
        if self._selected_id:
            for i, data in enumerate(self._targets_data):
                if data['id'] == self._selected_id:
                    self.table.selectRow(i)
                    self.detail_panel.update_target(
                        data['id'], data['lat'], data['lon'],
                        data['source'], data['orb_id'],
                        data['name'], data['description']
                    )
                    break
            else:
                self.detail_panel.clear()
        else:
            self.detail_panel.clear()

    def select_next(self):
        """Select next target in queue."""
        row_count = self.table.rowCount()
        if row_count == 0:
            return

        current = self.table.currentRow()
        next_row = (current + 1) % row_count
        self.table.selectRow(next_row)

    def select_target(self, target_id: str):
        """Select a specific target by ID."""
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item:
                # ID stored in column 0, format is "◎{id}"
                item_id = id_item.text().replace("◎", "")
                if item_id == target_id:
                    self.table.selectRow(row)
                    return True
        return False

    @property
    def selected_id(self) -> str:
        return self._selected_id
