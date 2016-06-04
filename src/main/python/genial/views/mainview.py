"""
    Génial
    ================================================
    A "Génies en herbe" questions manager.

    :copyright: (c) 2015, Adam Scott.
    :license: GPL3, see LICENSE for more details.
"""
from PyQt5.QtCore import QCoreApplication, QDir, pyqtSlot
from PyQt5.QtGui import QIcon, QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from genial.views.gen.ui_mainview import Ui_MainView
from genial.controllers.maincontroller import *
from genial.views.propertiesview import PropertiesView


class MainView(QMainWindow, Ui_MainView):
    def __init__(self, parent: 'MainController'=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainView()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        self.set_icons()
        self.set_slots()
        self.properties_view = None  # type: PropertiesView
        self.setup_properties()
        # There is no document opened, so...
        self.set_document_related_widgets_disabled(True)

    def closeEvent(self, event: QCloseEvent):
        if self.ui.document_view.close_file():
            event.accept()
        else:
            event.ignore()

    # noinspection PyCallByClass,PyTypeChecker
    def set_icons(self):
        self.ui.action_new.setIcon(
            QIcon.fromTheme(
                'document-new',
                QIcon(':/icon/document-new.svg')
            )
        )
        self.ui.action_open.setIcon(
            QIcon.fromTheme(
                'document-open',
                QIcon(':/icon/document-open.svg')
            )
        )
        self.ui.action_save.setIcon(
            QIcon.fromTheme(
                'document-save',
                QIcon(':/icon/document-save.svg')
            )
        )
        self.ui.action_saveas.setIcon(
            QIcon.fromTheme(
                'document-save-as',
                QIcon(':/icon/document-save-as.svg')
            )
        )
        self.ui.action_quit.setIcon(
            QIcon.fromTheme(
                'application-quit',
                QIcon(':/icon/application-quit.svg')
            )
        )
        self.ui.action_undo.setIcon(
            QIcon.fromTheme(
                'edit-undo',
                QIcon(':/icon/document-undo.svg')
            )
        )
        self.ui.action_redo.setIcon(
            QIcon.fromTheme(
                'edit-redo',
                QIcon(':/icon/document-redo.svg')
            )
        )
        self.ui.action_print.setIcon(
            QIcon.fromTheme(
                'document-print',
                QIcon(':/icon/document-print.svg')
            )
        )
        self.ui.action_properties.setIcon(
            QIcon.fromTheme(
                'document-properties',
                QIcon(':/icon/document-properties.svg')
            )
        )

    def set_slots(self):
        self.ui.document_view.document_available.connect(
            self.on_document_view_document_available
        )
        self.ui.document_view.document_unavailable.connect(
            self.on_document_view_document_unavailable
        )
        self.ui.document_view.document_open.connect(
            self.on_document_view_document_open
        )
        self.ui.document_view.document_close.connect(
            self.on_document_view_document_close
        )
        self.ui.document_view.document_requesting_settings_categories.connect(
            self.on_document_view_document_requesting_settings_categories
        )

    def set_document_related_widgets_disabled(self, disabled:bool):
        self.ui.action_save.setDisabled(disabled)
        self.ui.action_saveas.setDisabled(disabled)
        self.ui.action_newuser.setDisabled(disabled)
        self.ui.action_removeuser.setDisabled(disabled)
        self.ui.action_properties.setDisabled(disabled)
        self.ui.action_print.setDisabled(disabled)
        self.ui.action_close.setDisabled(disabled)
        if disabled:
            # Here, we KNOW that there is no undo/redo
            # when there is no document.
            self.ui.action_undo.setDisabled(True)
            self.ui.action_redo.setDisabled(True)

    def setup_properties(self):
        self.properties_view = PropertiesView()  # type: PropertiesView
        self.properties_view.setObjectName("settings_widget")

    @pyqtSlot()
    def on_action_save_triggered(self):
        self.ui.document_view.save_file()

    @pyqtSlot()
    def on_action_saveas_triggered(self):
        self.ui.document_view.save_file_as()

    @pyqtSlot()
    def on_action_close_triggered(self):
        self.ui.document_view.close_file()

    @pyqtSlot()
    def on_action_quit_triggered(self):
        self.close()

    @pyqtSlot()
    def on_action_newuser_triggered(self):
        print('New user!')

    @pyqtSlot()
    def on_action_removeuser_triggered(self):
        print('Remove user.')

    @pyqtSlot()
    def on_action_properties_triggered(self):
        self.properties_view.show()

    @pyqtSlot()
    def on_document_view_document_available(self):
        self.set_document_related_widgets_disabled(False)

    @pyqtSlot()
    def on_document_view_document_unavailable(self):
        self.set_document_related_widgets_disabled(True)

    @pyqtSlot()
    def on_document_view_document_was_modified(self):
        self.setWindowModified(self.ui.document_view.is_modified())

    @pyqtSlot()
    def on_document_view_document_open(self):
        self.setWindowFilePath(self.ui.document_view.get_current_file_name())

    @pyqtSlot()
    def on_document_view_document_close(self):
        self.setWindowFilePath("")

    @pyqtSlot()
    def on_document_view_document_requesting_settings_categories(self):
        self.properties_view.show()
        self.properties_view.ui.tab_widget.setCurrentWidget(
            self.properties_view.ui.categories_tab
        )
