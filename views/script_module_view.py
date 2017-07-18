from PySide2 import QtWidgets, QtCore, QtGui
from functools import partial

from auri.auri_lib import grpbox, get_auri_icon


class ScriptModuleView(QtWidgets.QGroupBox):
    def __init__(self, category, script, module_name, main_model, ctrl_index=-1):
        """

        Args:
            main_model (auri.models.main_model.MainModel):
            module_name (str):
            script (str):
            category (str):
        """
        self.main_model = main_model
        self.category = category
        self.script = script
        self.module_name = module_name

        super(ScriptModuleView, self).__init__()
        # Create the script module view & controller
        exec "import auri.scripts.{0}.{1} as the_script; the_view = the_script.View(); the_ctrl = the_view.ctrl".format(category, script)
        # noinspection PyUnresolvedReferences
        the_ctrl.model.module_name = module_name
        self.the_view = the_view
        self.model = the_ctrl.model

        grp_title = "{0} - {1} - {2}".format(category, script, module_name)
        self.setTitle(grp_title)
        # Create the shell to hold the view
        script_layout = QtWidgets.QGridLayout()
        self.setLayout(script_layout)

        # Create the basic buttons
        btns_layout = QtWidgets.QHBoxLayout()
        btns_size = QtCore.QSize(24, 24)

        up_btn = QtWidgets.QToolButton()
        up_icon = QtGui.QIcon()
        up_icon.addPixmap(QtGui.QPixmap(get_auri_icon("Arrow_Up.png")))
        up_btn.setIcon(up_icon)
        up_btn.setIconSize(btns_size)
        up_btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)

        down_btn = QtWidgets.QToolButton()
        down_icon = QtGui.QIcon()
        down_icon.addPixmap(QtGui.QPixmap(get_auri_icon("Arrow_Down.png")))
        down_btn.setIcon(down_icon)
        down_btn.setIconSize(btns_size)
        down_btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)

        self.duplicate_btn = QtWidgets.QToolButton()
        duplicate_icon = QtGui.QIcon()
        duplicate_icon.addPixmap(QtGui.QPixmap(get_auri_icon("Duplicate.png")))
        self.duplicate_btn.setIcon(duplicate_icon)
        self.duplicate_btn.setIconSize(btns_size)
        self.duplicate_btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)

        self.delete_btn = QtWidgets.QToolButton()
        delete_icon = QtGui.QIcon()
        delete_icon.addPixmap(QtGui.QPixmap(get_auri_icon("Delete.png")))
        self.delete_btn.setIcon(delete_icon)
        self.delete_btn.setIconSize(btns_size)
        self.delete_btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)

        # TODO: Event should be removed, not necessary
        # TODO: Should check if refreshing every time we press Execute All is fast enough
        self.delete_btn.pressed.connect(partial(self.remove_ctrl, the_ctrl))

        # Add the buttons
        btns_layout.addWidget(up_btn)
        btns_layout.addWidget(down_btn)
        btns_layout.addWidget(self.duplicate_btn)
        btns_layout.addWidget(self.delete_btn)
        script_layout.addLayout(btns_layout, 0, 0)
        # Add the view
        script_layout.addWidget(the_view, 1, 0)

        # TODO: Should be removed, not necessary
        if ctrl_index < 0:
            self.main_model.scripts_to_execute.append(the_ctrl)
        else:
            self.main_model.scripts_to_execute.insert(ctrl_index, the_ctrl)

    def get_index(self):
        return self.parent().layout().indexOf(self)

    # TODO: Should be remove, not necessary
    def remove_ctrl(self, the_ctrl):
        self.main_model.scripts_to_execute.remove(the_ctrl)
