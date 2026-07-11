"""Dashboard: draft strategy cards with confidence/opinion badges."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget, QComboBox,
)

from ..widgets import badge, dim, header, patch_bar, rank_chip, warn_panel


class DashboardTab(QWidget):
    open_trade_builder = Signal(str)   # tablet type
    open_tablet_db = Signal(str)       # tablet type
    open_waystone_optimizer = Signal()

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        root = QVBoxLayout(self)
        root.addWidget(header("Farming Strategy Dashboard", "h1"))
        root.addWidget(patch_bar(store.patch_banner()))
        root.addWidget(warn_panel([
            "All strategy ratings are DRAFT community/editorial opinion, not final market truth.",
            "Profit claims, market prices, and meta rankings are perishable — recheck sources.",
            "Open a tablet page for focused modifier lists and trade-search entry points.",
        ]))

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Investment mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Budget", "High investment"])
        if store.settings.get("budget_mode") == "high":
            self.mode_combo.setCurrentIndex(1)
        self.mode_combo.currentIndexChanged.connect(self._rebuild_cards)
        controls.addWidget(self.mode_combo)
        controls.addStretch(1)
        root.addLayout(controls)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.cards_host = QWidget()
        self.cards_layout = QGridLayout(self.cards_host)
        self.cards_layout.setSpacing(10)
        scroll.setWidget(self.cards_host)
        root.addWidget(scroll, 1)
        self._rebuild_cards()

    def _rebuild_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        high = self.mode_combo.currentIndex() == 1
        for i, strat in enumerate(self.store.strategies):
            self.cards_layout.addWidget(self._card(strat, high), i // 2, i % 2)
        self.cards_layout.setRowStretch(len(self.store.strategies) // 2 + 1, 1)

    def _card(self, strat, high):
        card = QFrame()
        card.setProperty("role", "card")
        lay = QVBoxLayout(card)

        top = QHBoxLayout()
        title = header(strat["name"])
        top.addWidget(title)
        top.addStretch(1)
        rating = strat["high_investment_rating"] if high else strat["budget_rating"]
        top.addWidget(rank_chip(rating))
        top.addWidget(badge("opinion"))
        if not strat.get("trade_ready", True):
            top.addWidget(badge("unknown"))
        lay.addLayout(top)

        lay.addWidget(dim("Tablet: %s   |   Confidence: %s"
                          % (strat["tablet_type"], strat["confidence"])))
        setup = strat["high_investment_setup"] if high else strat["budget_setup"]
        setup_lbl = QLabel(("High investment: " if high else "Budget: ") + setup)
        setup_lbl.setWordWrap(True)
        lay.addWidget(setup_lbl)
        mods_lbl = QLabel("Key mods: " + ", ".join(strat["best_mods"]))
        mods_lbl.setWordWrap(True)
        lay.addWidget(mods_lbl)
        lay.addWidget(dim("Rewards: %s" % strat["rewards"]))
        lay.addWidget(dim("Main danger: %s" % strat["main_danger"]))
        for warning in strat.get("warnings", []):
            wl = QLabel("⚠ " + warning)
            wl.setProperty("role", "warn")
            wl.setWordWrap(True)
            lay.addWidget(wl)

        buttons = QHBoxLayout()
        if strat.get("id") == "waystone_sustain":
            db_btn = QPushButton("Open optimizer")
            db_btn.clicked.connect(self.open_waystone_optimizer.emit)
        else:
            db_btn = QPushButton("Open tablet page")
            db_btn.clicked.connect(
                lambda _=False, t=strat["tablet_type"]: self.open_tablet_db.emit(t))
        buttons.addWidget(db_btn)
        trade_btn = QPushButton("Trade builder")
        if strat.get("id") == "waystone_sustain":
            trade_btn.setEnabled(False)
            trade_btn.setToolTip("Use the Waystone Optimizer for map-mod planning.")
        elif strat.get("trade_ready", True):
            trade_btn.clicked.connect(
                lambda _=False, t=strat["tablet_type"]: self.open_trade_builder.emit(t))
        else:
            trade_btn.setEnabled(False)
            trade_btn.setToolTip("Disabled: required stat IDs are UNKNOWN - NEEDS VERIFICATION.")
        buttons.addWidget(trade_btn)
        buttons.addStretch(1)
        lay.addLayout(buttons)
        return card
