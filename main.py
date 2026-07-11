"""PoE2 Tablet Farming Helper — Phase 3 MVP prototype.

Data source: POE2_054_Farming_Research_Phase2 (converted to data/*.json).
Run:  python main.py
"""
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from app.datastore import DataStore
from app.theme import DEFAULT_THEME, build_qss
from app.tabs.dashboard import DashboardTab
from app.tabs.tablet_pages import TabletHubTab
from app.tabs.waystone_tab import WaystoneOptimizerTab
from app.tabs.crafting_tab import CraftingTab
from app.tabs.expedition_tabs import LogbookPlannerTab
from app.tabs.atlas_tab import AtlasMastersTab
from app.tabs.gear_trade import TradeHubTab
from app.tabs.sources_tab import SourcesTab
from app.tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.setWindowTitle("%s  —  %s  (v%s, prototype)" % (
            store.meta["app_name"], store.meta["patch"]["version"],
            store.meta["app_version"]))
        # Owner target: ~1920-class resolution. Start maximized; layouts fill
        # whatever space is available and show more when the window grows.
        self.resize(1920, 1080)
        self.setMinimumSize(1360, 840)

        self.tabs = QTabWidget()
        self.dashboard = DashboardTab(store)
        self.tablets = TabletHubTab(store)
        self.waystones = WaystoneOptimizerTab(store)
        self.crafting = CraftingTab(store)
        self.logbook = LogbookPlannerTab(store)
        self.atlas = AtlasMastersTab(store)
        self.trade = TradeHubTab(store)
        self.sources = SourcesTab(store)
        self.settings = SettingsTab(store)

        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.tablets, "Tablets")
        self.tabs.addTab(self.waystones, "Waystone Optimizer")
        self.tabs.addTab(self.crafting, "Crafting")
        self.tabs.addTab(self.logbook, "Expedition Whispers")
        self.tabs.addTab(self.atlas, "Atlas Masters")
        self.tabs.addTab(self.trade, "Trade Search Builder")
        self.tabs.addTab(self.sources, "Source Confidence")
        self.tabs.addTab(self.settings, "Settings")
        self.setCentralWidget(self.tabs)

        self.dashboard.open_trade_builder.connect(self._goto_trade)
        self.dashboard.open_tablet_db.connect(self._goto_tablet_db)
        self.dashboard.open_waystone_optimizer.connect(self._goto_waystones)
        self.tablets.open_trade_builder.connect(self._goto_trade)

    def _goto_trade(self, tablet_type):
        self.trade.set_tablet_type(tablet_type)
        self.tabs.setCurrentWidget(self.trade)

    def _goto_tablet_db(self, tablet_type):
        # Expedition is no longer a tablet — its page is the whispers KB.
        if tablet_type not in self.store.tablet_base_names():
            self.tabs.setCurrentWidget(self.logbook)
            return
        self.tablets.show_tablet_type(tablet_type)
        self.tabs.setCurrentWidget(self.tablets)

    def _goto_waystones(self):
        self.tabs.setCurrentWidget(self.waystones)


def main():
    from PySide6.QtCore import Qt
    # Required so the lazy in-app video player (WebEngine) can start later.
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    store = DataStore()
    app.setStyleSheet(build_qss(store.settings.get("theme", DEFAULT_THEME)))
    window = MainWindow(store)
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
