"""Source Confidence tab: registry, conflicts, needs-verification queue."""
import webbrowser

from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from ..widgets import dim, header, make_table, patch_bar, warn_panel


class SourcesTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        root = QVBoxLayout(self)
        root.addWidget(header("Source Confidence & Conflicts", "h1"))
        root.addWidget(patch_bar(store.patch_banner()))

        sub = QTabWidget()

        # Sources
        sources_page = QWidget()
        s_lay = QVBoxLayout(sources_page)
        s_lay.addWidget(dim("Double-click a row to open the source URL in your browser."))
        sources = store.sources["sources"]
        self.sources_table = make_table(
            ["Source", "Type", "Reliability", "Data extracted", "Limitations"],
            [[s["name"], s["type"], s["reliability"], s["data"], s["limitations"]]
             for s in sources],
            stretch_column=3)
        self._source_urls = [s["url"] for s in sources]
        self.sources_table.itemDoubleClicked.connect(self._open_source)
        s_lay.addWidget(self.sources_table)
        sub.addTab(sources_page, "Source Registry")

        # Active conflicts
        conflicts_page = QWidget()
        c_lay = QVBoxLayout(conflicts_page)
        conflicts = [c for c in store.sources["conflicts"]
                     if c.get("status") != "RESOLVED"]
        if conflicts:
            c_lay.addWidget(warn_panel([
                "Active conflicts block final data until verified in-game or via "
                "official/database sources. Resolved rows are kept separately as "
                "history."]))
            c_lay.addWidget(make_table(
                ["ID", "Topic", "Claim A", "Claim B", "Status", "Notes"],
                [[c["id"], c["topic"], c["claim_a"], c["claim_b"], c["status"], c["note"]]
                 for c in conflicts],
                ["conflict"] * len(conflicts),
                stretch_column=5))
        else:
            c_lay.addWidget(dim(
                "No active source conflicts remain. Resolved source decisions are "
                "preserved in the Resolved History tab."))
            c_lay.addStretch(1)
        sub.addTab(conflicts_page, "Active Conflicts (%d)" % len(conflicts))

        # Resolved conflict history
        resolved_page = QWidget()
        r_lay = QVBoxLayout(resolved_page)
        resolved = [c for c in store.sources["conflicts"]
                    if c.get("status") == "RESOLVED"]
        r_lay.addWidget(make_table(
            ["ID", "Topic", "Resolution"],
            [[c["id"], c["topic"], c.get("resolution", c.get("note", ""))]
             for c in resolved],
            stretch_column=2,
            expand=True))
        sub.addTab(resolved_page, "Resolved History (%d)" % len(resolved))

        # Needs verification
        queue_page = QWidget()
        q_lay = QVBoxLayout(queue_page)
        q_lay.addWidget(header("Needs-verification queue"))
        for item in store.sources["needs_verification"]:
            lbl = QLabel("• " + item)
            lbl.setWordWrap(True)
            q_lay.addWidget(lbl)
        q_lay.addStretch(1)
        sub.addTab(queue_page, "Needs Verification")

        root.addWidget(sub, 1)

    def _open_source(self, item):
        url = self._source_urls[item.row()]
        if url:
            webbrowser.open(url)
