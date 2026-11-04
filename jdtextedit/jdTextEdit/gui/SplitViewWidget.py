from PyQt6.QtWidgets import QWidget, QSplitter, QHBoxLayout
from jdTextEdit.gui.EditTabWidget import EditTabWidget
from jdTextEdit.Environment import Environment
from jdTextEdit.gui.CodeEdit import CodeEdit
from PyQt6.QtCore import QCoreApplication
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from jdTextEdit.gui.MainWindow import MainWindow


class SplitViewWidget(QWidget):
    def __init__(self, env: Environment, mainWindow: "MainWindow") -> None:
        super().__init__()
        self.env = env
        self.activeID = 0
        self._mainWindow = mainWindow

        self.splitterWidget = QSplitter(self)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.splitterWidget)

        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(mainLayout)

    def getCurrentTextEditWidget(self) -> CodeEdit:
        return self.splitterWidget.widget(self.activeID).currentWidget().getCodeEditWidget()

    def getCurrentTabWidget(self) -> EditTabWidget:
        return self.splitterWidget.widget(self.activeID)

    def getAllTabWidgets(self) -> list[EditTabWidget]:
        widgetList: list[EditTabWidget] = []
        for i in range(self.splitterWidget.count()):
            widgetList.append(self.splitterWidget.widget(i))
        return widgetList

    def setActiveWidget(self, splitID: int) -> None:
        self.activeID = splitID

    def initTabWidget(self) -> None:
        self.splitterWidget.addWidget(EditTabWidget(self.env, self, 0))

    def splitVertical(self) -> None:
        tabWidget = EditTabWidget(self.env, self, self.splitterWidget.count())
        tabWidget.createTab(QCoreApplication.translate("SplitViewWidget", "Untitled"))
        tabWidget.updateSettings(self.env.settings)
        self.splitterWidget.insertWidget(self.activeID + 1, tabWidget)
        self.env.mainWindow.deleteCurrentViewAction.setEnabled(True)

    def deleteCurrentView(self) -> None:
        currentTabWidget = self.getCurrentTabWidget()
        widgetList = []
        for i in range(currentTabWidget.count()):
            widgetList.append({
                "widget": currentTabWidget.widget(i),
                "title": currentTabWidget.tabText(i),
                "icon": currentTabWidget.tabIcon(i),
            })
        currentTabWidget.setParent(None)
        self.activeID -= 1
        if self.activeID == -1:
            self.activeID = 0
        self.updateTabWidgetID()
        newTabWidget = self.getCurrentTabWidget()
        for i in widgetList:
            newTabWidget.addExistingTab(i["widget"], i["title"], i["icon"])
        if self.splitterWidget.count() == 1:
            self.env.mainWindow.deleteCurrentViewAction.setEnabled(False)

    def getSessionData(self) -> dict:
        count = 0
        data = {}
        data["tabWidgets"] = []
        for i in self.getAllTabWidgets():
            tabData, count = i.getSessionData(count)
            data["tabWidgets"].append(tabData)
        return data

    def restoreSession(self, data: dict) -> None:
        if "tabWidgets" not in data:
            self.splitterWidget.addWidget(EditTabWidget(self.env, self, self.splitterWidget.count()))
            self.splitterWidget.widget(self.splitterWidget.count() - 1).restoreSession(data, old_version=True)
            return
        for i in data["tabWidgets"]:
            self.splitterWidget.addWidget(EditTabWidget(self.env, self, self.splitterWidget.count()))
            self.splitterWidget.widget(self.splitterWidget.count() - 1).restoreSession(i)
        if self.splitterWidget.count() > 1:
            self._mainWindow.deleteCurrentViewAction.setEnabled(True)

    def updateTabWidgetID(self) -> None:
        for count, i in enumerate(self.getAllTabWidgets()):
            i.splitID = count

    def getMainWindow(self) -> "MainWindow":
        return self._mainWindow
