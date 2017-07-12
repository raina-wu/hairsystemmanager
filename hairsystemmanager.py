__author__ = 'rainawu'

import pymel.core as pm
from maya import OpenMayaUI as omui
import os

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2 import __version__
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from PySide.QtUiTools import *
    from PySide import __version__
    from shiboken import wrapInstance

import nucleusutils

map(reload,[nucleusutils])


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)

_win = None
def show():
    global _win
    if _win == None:
        _win = HairSystemManagerUI()
    _win.show()

class HairSystemManagerUI(QWidget):

    def __init__(self, *args, **kwargs):
        super(HairSystemManagerUI, self).__init__(*args, **kwargs)

        # Parent widget under Maya main window
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)

        # Set the object name
        self.setObjectName('HairSystemManagerUI_uniqueId')
        self.setWindowTitle('Hair System Manager')

        self._initUI()


    def _initUI(self):
        # load UI from .ui file
        loader = QUiLoader()
        currentDir = os.path.dirname(__file__)
        uiFile = QFile(currentDir+"/hairsystemmanager.ui")
        uiFile.open(QFile.ReadOnly)
        self.ui = loader.load(uiFile, parentWidget=self)
        uiFile.close()
        layout = QHBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        # initialize hair system table
        self._columnHairSys = 2
        self._columnEnableCache = 1
        self._columnSimMethod = 0
        self._updateHairSystemList()
        self.ui.hairSystemTableWidget.setFocusPolicy(Qt.NoFocus)
        self.ui.hairSystemTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        # hair system management section
        self.ui.refreshButton.clicked.connect(self._updateHairSystemList)
        self.ui.simMethodSetButton.clicked.connect(self._setSimMethod)
        self.ui.hairSystemTableWidget.itemDoubleClicked.connect(self._selectHairSystemFromUI)
        self.ui.hairSystemTableWidget.itemClicked.connect(self._setEnableCache)

        # cache section
        self.ui.newCacheButton.clicked.connect(self._newCache)
        self.ui.loadCacheButton.clicked.connect(self._loadCache)
        self.ui.deleteCacheButton.clicked.connect(self._deleteCache)

        # selection section
        self.ui.selSolverButton.clicked.connect(self._selectSolver)
        self.ui.selHairSysButton.clicked.connect(self._selectHairSystem)
        self.ui.selCurvesButton.clicked.connect(self._selectCurves)
        self.ui.selFollicleButton.clicked.connect(self._selectFollicle)


    def _addCacheCheckBox(self):
        cbWidget = QWidget()
        checkBox = QCheckBox()
        layout = QHBoxLayout(cbWidget)
        layout.addWidget(checkBox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0,0,0,0)
        cbWidget.setLayout(layout)
        return cbWidget
        # pMyTableWidget->setCellWidget(0,0,cbWidget)

    def _updateHairSystemList(self):
        hairSystems = pm.ls(type="hairSystem")
        self.ui.hairSystemTableWidget.clearContents()
        self.ui.hairSystemTableWidget.setRowCount(len(hairSystems))
        rowCnt = 0
        for hairSystem in hairSystems:
            # hair system name
            systemNameItem = QTableWidgetItem(hairSystem.name())
            systemNameItem.setFlags(~Qt.ItemIsEditable)
            systemNameItem.setTextAlignment(Qt.AlignCenter)
            # cache
            cacheItem = QTableWidgetItem("Enable")
            cacheItem.setFlags(~Qt.ItemIsEditable)
            cacheItem.setTextAlignment(Qt.AlignCenter)
            if nucleusutils.hasCache(hairSystem):
                checkState = Qt.Checked if nucleusutils.getEnableCache(hairSystem) else Qt.Unchecked
                cacheItem.setCheckState(checkState)
            else:
                cacheItem.setCheckState(Qt.Unchecked)
                cacheItem.setFlags(cacheItem.flags() & ~Qt.ItemIsEnabled)
            # sim method
            simMethod = ["Off", "Static", "Dynamic Follicles Only", "All Follicles"][hairSystem.simulationMethod.get()]
            simMethodItem = QTableWidgetItem(simMethod)
            simMethodItem.setFlags(~Qt.ItemIsEditable)
            simMethodItem.setTextAlignment(Qt.AlignCenter)
            # add to table
            self.ui.hairSystemTableWidget.setItem(rowCnt, self._columnHairSys, systemNameItem)
            self.ui.hairSystemTableWidget.setItem(rowCnt, self._columnEnableCache, cacheItem)
            self.ui.hairSystemTableWidget.setItem(rowCnt, self._columnSimMethod, simMethodItem)
            rowCnt = rowCnt + 1

        self.ui.hairSystemTableWidget.sortItems(0)

    def _getSelectedHairSystems(self):
        selectedItems = self.ui.hairSystemTableWidget.selectedItems()
        rowIds = set(item.row() for item in selectedItems)
        hairSystemList = [pm.PyNode(self.ui.hairSystemTableWidget.item(rowId,self._columnHairSys).text()) for rowId in rowIds]
        return  hairSystemList

    def _setSimMethod(self):
        # simMethods = ["Off", "Static", "Dynamic Follicles Only", "All Follicles"]
        simMethodId = self.ui.simMethodComboBox.currentIndex()
        selectedHairSys = self._getSelectedHairSystems()
        for hairSys in selectedHairSys:
            hairSys.simulationMethod.set(simMethodId)
        self._updateHairSystemList()

    def _selectHairSystemFromUI(self, item):
        pm.select(self.ui.hairSystemTableWidget.item(item.row(), self._columnHairSys).text())

    def _newCache(self):
        selected = self._getSelectedHairSystems()
        if len(selected) != 1:
            msgBox = QMessageBox()
            msgBox.setText("Please select one hairSystem to create cache.")
            msgBox.exec_()
            return
        pm.select(selected[0])
        # performCreateNclothCache.mel
        pm.mel.eval("performCreateNclothCache 1 \"add\";")

    def _loadCache(self):
        selected = self._getSelectedHairSystems()
        if len(selected) != 1:
            msgBox = QMessageBox()
            msgBox.setText("Please select one hairSystem to load cache.")
            msgBox.exec_()
            return
        if nucleusutils.importNHairCache(selected[0]):
            self._updateHairSystemList()

    def _deleteCache(self):
        selected = self._getSelectedHairSystems()
        for hairSys in selected:
            if not nucleusutils.hasCache(hairSys): continue
            pm.select(hairSys)
            pm.language.mel.eval("deleteCacheFile 2 { \"keep\", \"\" };")
        self._updateHairSystemList()

    def _setEnableCache(self, item):
        if item.column() != self._columnEnableCache: return
        checkFlag = 0 if item.checkState() == Qt.Unchecked else 1
        hairSystem = pm.PyNode(self.ui.hairSystemTableWidget.item(item.row(), 2).text())
        nucleusutils.setEnableCache(hairSystem, checkFlag)

    def _selectSolver(self):
        pm.select(nucleusutils.getSolver())

    def _selectCurves(self):
        pm.select(nucleusutils.getCurves())

    def _selectFollicle(self):
        pm.select(nucleusutils.getFollicles())

    def _selectHairSystem(self):
        pm.select(nucleusutils.getHairSystems())
