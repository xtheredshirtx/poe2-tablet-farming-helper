"""Settings: league selection, trade defaults, data folder info."""
import os
import webbrowser

from PySide6.QtWidgets import (
    QApplication, QComboBox, QGridLayout, QGroupBox, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

from ..datastore import DATA_DIR
from ..theme import DEFAULT_THEME, PALETTES, build_qss
from ..widgets import dim, header, patch_bar


class SettingsTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        root = QVBoxLayout(self)
        root.addWidget(header("Settings", "h1"))
        root.addWidget(patch_bar(store.patch_banner()))

        box = QGroupBox("Preferences (saved to settings.json)")
        grid = QGridLayout(box)
        grid.addWidget(QLabel("Default league:"), 0, 0)
        self.league = QComboBox()
        self.league.addItems(store.meta["leagues"])
        self.league.setCurrentText(store.settings.get("league", "Runes of Aldur"))
        self.league.currentTextChanged.connect(self._save)
        grid.addWidget(self.league, 0, 1)

        grid.addWidget(QLabel("Default trade type:"), 1, 0)
        self.status = QComboBox()
        for opt in store.meta["trade"]["status_options_labeled"]:
            self.status.addItem(opt["text"], opt["id"])
        idx = self.status.findData(store.settings.get(
            "trade_status", store.meta["trade"].get("default_status", "securable")))
        self.status.setCurrentIndex(idx if idx >= 0 else 0)
        self.status.currentIndexChanged.connect(self._save)
        grid.addWidget(self.status, 1, 1)

        grid.addWidget(QLabel("Default investment mode:"), 2, 0)
        self.mode = QComboBox()
        self.mode.addItems(["budget", "high"])
        self.mode.setCurrentText(store.settings.get("budget_mode", "budget"))
        self.mode.currentTextChanged.connect(self._save)
        grid.addWidget(self.mode, 2, 1)

        grid.addWidget(QLabel("App colors:"), 3, 0)
        self.theme = QComboBox()
        self.theme.addItems(list(PALETTES.keys()))
        self.theme.setCurrentText(store.settings.get("theme", DEFAULT_THEME))
        self.theme.currentTextChanged.connect(self._apply_theme)
        grid.addWidget(self.theme, 3, 1)
        grid.addWidget(QLabel("Text colors adjust with each palette. The item-tooltip "
                              "cards keep the in-game look on purpose."), 4, 0, 1, 2)
        root.addWidget(box)

        data_box = QGroupBox("Data")
        d_lay = QVBoxLayout(data_box)
        d_lay.addWidget(dim("Seed data folder: %s" % DATA_DIR))
        d_lay.addWidget(dim("Data generated: %s from the Phase 2 canonical research folder. "
                            "Edit the JSON files and restart to update."
                            % store.meta["data_generated"]))
        open_btn = QPushButton("Open data folder")
        open_btn.clicked.connect(lambda: os.startfile(DATA_DIR))
        d_lay.addWidget(open_btn)
        patch_btn = QPushButton("Open official patch notes forum")
        patch_btn.clicked.connect(
            lambda: webbrowser.open(self.store.meta["patch"]["patch_forum_url"]))
        d_lay.addWidget(patch_btn)
        root.addWidget(data_box)

        about = QGroupBox("About / guardrails")
        a_lay = QVBoxLayout(about)
        for line in (
            "%s v%s — public work-in-progress prototype." % (store.meta["app_name"], store.meta["app_version"]),
            "This app never scrapes trade listings, never polls, and never runs background searches.",
            "Uncertain data stays labeled: CONFLICT and NEEDS VERIFICATION badges are intentional.",
            "Ratings are community opinion. Recheck official patch notes after every game update.",
        ):
            lbl = QLabel("• " + line)
            lbl.setWordWrap(True)
            a_lay.addWidget(lbl)
        root.addWidget(about)
        root.addStretch(1)

    def _apply_theme(self, name):
        QApplication.instance().setStyleSheet(build_qss(name))
        self._save()

    def _save(self):
        self.store.settings["league"] = self.league.currentText()
        self.store.settings["trade_status"] = self.status.currentData()
        self.store.settings["budget_mode"] = self.mode.currentText()
        self.store.settings["theme"] = self.theme.currentText()
        self.store.save_settings()
