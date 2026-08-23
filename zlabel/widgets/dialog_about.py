from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtWidgets import QDialog

from zlabel import __version__

from .ui import Ui_DialogAbout

_GITHUB_URL = "https://github.com/ZhengGroupLZU/ZLabel"


class DialogAbout(QDialog, Ui_DialogAbout):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self._set_about_html()

    def retranslateUi(self, dialog):
        # Language switches call retranslateUi, which would reset the browser to
        # the static .ui HTML; re-apply the dynamic version/license content.
        super().retranslateUi(dialog)
        self._set_about_html()

    def _set_about_html(self):
        self.textBrowser.setHtml(
            f"""
            <div align="center">
              <img src=":/icon/icons/logo.svg" height="100"/>
              <h1>ZLabel</h1>
              <p><b>Version {__version__}</b></p>
              <p>An image data labeling tool powered by advanced AI models.</p>
              <p>ZLabel Copyright (C) 2023-2026 Rainyl@ZhengGroup.</p>
              <p>
                <a href="{_GITHUB_URL}">{_GITHUB_URL}</a>
              </p>
            </div>
            <hr/>
            <p><b>License</b></p>
            <p>This software is released under the Apache License 2.0.</p>
            <p><b>Disclaimer</b></p>
            <p>
              This software is provided "as is", without warranty of any kind,
              express or implied, including but not limited to the warranties of
              merchantability, fitness for a particular purpose and
              noninfringement. In no event shall the authors or copyright holders
              be liable for any claim, damages or other liability arising from,
              out of or in connection with the software or the use or other
              dealings in the software.
            </p>
            """
        )
