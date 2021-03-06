import json
import os

import re

from auri.vendor.Qt import QtWidgets, QtCore
from collections import OrderedDict
from functools import partial

from auri.auri_lib import get_categories, get_scripts, get_subcategories
from auri.views.edit_script_view import EditScriptView
from auri.views.main_view import MainView
from auri.views.message_box_view import MessageBoxView
from auri.views.script_module_view import ScriptModuleView


class CommonController(object):
    def __init__(self, main_model, project_model, bootstrap_view):
        """

        Args:
            main_model (auri.models.main_model.MainModel):
            project_model (auri.models.project_model.ProjectModel):
            bootstrap_view (auri.views.bootstrap_view.BootstrapView):
        """
        self.dialog = QtWidgets.QFileDialog()
        self.dialog.setFilter(self.dialog.filter() | QtCore.QDir.Hidden)
        self.dialog.setDefaultSuffix("json")
        self.dialog.setNameFilters(["JSON (*.json)"])

        self.project_model = project_model
        self.main_model = main_model
        self.bootstrap_view = bootstrap_view
        self.main_view = None
        self.category_combobox = None
        self.subcategory_combobox = None
        self.script_selector = None
        self.edit_script_dialog = None
        self.message_box = None
        self.refresh()

    def add_script(self, category, subcategory, script, module_name, main_view, script_module_instance=None, model=None):
        if script_module_instance is not None:
            module_name = "{0}__DUPLICATE".format(module_name)
        if module_name in self.main_model.unique_names:
            self.message_box = MessageBoxView("Naming Error", "<p style='font-size:12pt'>A module named <b>{0}</b> already exists.\nYou should rename that module.</p>".format(module_name))
            self.message_box.show()
        if script_module_instance is not None:
            script_view = ScriptModuleView(category, subcategory, script, module_name, self.main_model)
            main_view.scrollable_layout.insertWidget(script_module_instance.get_index() + 1, script_view)
            script_view.model.__dict__ = script_module_instance.model.__dict__.copy()
            script_view.model.module_name = module_name
            script_view.refresh_module_name()
        else:
            script_view = ScriptModuleView(category, subcategory, script, module_name, self.main_model)
            main_view.scrollable_layout.insertWidget(main_view.scrollable_layout.count() - 1, script_view)
        script_view.fold_btn.pressed.connect(partial(self.fold_script, script_view))
        script_view.up_btn.pressed.connect(partial(self.move_script, script_view, 1))
        script_view.down_btn.pressed.connect(partial(self.move_script, script_view, -1))
        script_view.edit_btn.pressed.connect(partial(self.edit_script, script_view))
        script_view.duplicate_btn.pressed.connect(partial(self.add_script, category, subcategory, script, module_name, main_view, script_view))
        script_view.delete_btn.pressed.connect(partial(self.remove_script, script_view))
        script_view.refresh_module_name()
        if model is not None:
            script_view.model.__dict__ = model
        script_view.the_view.refresh_fold()
        script_view.the_view.refresh_view()
        self.main_model.unique_names.append(module_name)

    def fold_script(self, script_view):
        """

        Args:
            script_view (auri.views.script_module_view.ScriptModuleView):
        """
        script_view.the_view.setVisible(script_view.model.folded)
        script_view.model.folded = not script_view.the_view.isVisible()

    def move_script(self, script_view, offset_position):
        """

        Args:
            script_view (auri.views.script_module_view.ScriptModuleView):
            offset_position (int): 1 move one position up, -1 move one position down
        """
        old_position = script_view.get_index()
        self.main_view.scrollable_layout.removeWidget(script_view)
        self.main_view.scrollable_layout.insertWidget(old_position - offset_position, script_view)

    def edit_script(self, script_view):
        """

        Args:
            script_view (auri.views.script_module_view.ScriptModuleView):
        """
        self.edit_script_dialog = EditScriptView(script_view, self.project_model, self.main_model)
        result = self.edit_script_dialog.exec_()
        if result == 1:
            self.refresh_project_model()

    def remove_script(self, script_view):
        """

        Args:
            script_view (auri.views.script_module_view.ScriptModuleView):
        """
        self.main_view.scrollable_layout.removeWidget(script_view)
        script_view.deleteLater()
        self.main_model.unique_names.remove(script_view.module_name)

    def set_window_title(self, title):
        self.bootstrap_view.setWindowTitle(title)

    def new_project(self):
        assert (isinstance(self.main_view, MainView))
        while self.main_view.scrollable_layout.count():
            child = self.main_view.scrollable_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.main_view.scrollable_layout.addStretch(1)
        self.main_model.current_project = None
        self.project_model.scripts_to_execute = []
        self.main_model.unique_names = []
        self.set_window_title("Auri - New Project")

    def open_project(self, is_import=False):
        self.dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        if self.dialog.exec_() == QtWidgets.QDialog.Accepted:
            if not is_import:
                self.new_project()
                # Load the file
                self.main_model.current_project = self.dialog.selectedFiles()[0]
                file(self.main_model.current_project, "r").close()
                project_file_path = os.path.abspath(self.main_model.current_project)
                self.set_window_title("Auri - {0}".format(os.path.basename(self.main_model.current_project)))
            else:
                project_file_path = os.path.abspath(self.dialog.selectedFiles()[0])
            with open(project_file_path, "r") as project_file:
                self.project_model.__dict__ = json.load(project_file, object_pairs_hook=OrderedDict)
            # Create the project
            for index in self.project_model.scripts_in_order:
                category = self.project_model.scripts_in_order[index]["Module Category"]
                subcategory = self.project_model.scripts_in_order[index]["Module SubCategory"]
                script = self.project_model.scripts_in_order[index]["Module Script"]
                model = self.project_model.scripts_in_order[index]["Model"]
                module_name = model["module_name"]
                self.add_script(category, subcategory, script, module_name, self.main_view, model=model)

    def refresh_project_model(self):
        self.project_model.scripts_in_order = {}
        self.main_model.scripts_to_execute = []
        for widget_index in range(0, self.main_view.scrollable_layout.count()):
            script_view = self.main_view.scrollable_layout.itemAt(widget_index).widget()
            if not isinstance(script_view, ScriptModuleView):
                continue
            self.project_model.scripts_in_order[script_view.get_index()] = {}
            self.project_model.scripts_in_order[script_view.get_index()]["Module Category"] = script_view.category
            self.project_model.scripts_in_order[script_view.get_index()]["Module SubCategory"] = script_view.subcategory
            self.project_model.scripts_in_order[script_view.get_index()]["Module Script"] = script_view.script
            self.project_model.scripts_in_order[script_view.get_index()]["Model"] = script_view.model.__dict__
            self.main_model.scripts_to_execute.append(script_view.the_ctrl)

    def save_project(self):
        # self.project_model.unique_names = []
        if self.main_model.current_project is None:
            self.save_project_as()
        else:
            self.refresh_project_model()
            project_file_path = os.path.abspath(self.main_model.current_project)
            with open(project_file_path, "w") as project_file:
                json.dump(self.project_model.__dict__, project_file, sort_keys=True, indent=4, separators=(",", ": "))
            self.set_window_title("Auri - {0}".format(os.path.basename(self.main_model.current_project)))

    def save_project_as(self):
        self.dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if self.dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.main_model.current_project = self.dialog.selectedFiles()[0]
            file(self.main_model.current_project, "w").close()
            self.save_project()
        else:
            # If the file does not exist, remove it from the title
            if self.main_model.current_project is not None:
                if not os.path.isfile(self.main_model.current_project):
                    self.main_model.current_project = None
                    self.set_window_title("Auri - New Project")

    def refresh(self):
        # Reload UI
        self.refresh_categories()
        self.refresh_subcategories()
        self.refresh_scripts()

        if self.main_view is None:
            return
        # Reload Scripts (temp save & reopen)
        self.refresh_project_model()
        old_project_model = self.project_model.__dict__
        old_current_project = self.main_model.current_project

        self.new_project()
        if old_current_project is not None:
            self.main_model.current_project = old_current_project
            self.set_window_title("Auri - {0}".format(os.path.basename(self.main_model.current_project)))
        self.project_model.__dict__ = old_project_model
        self.main_view.add_btn.setDisabled(self.main_model.add_btn_disabled)

        # TODO: Extract that
        for index in self.project_model.scripts_in_order:
            category = self.project_model.scripts_in_order[index]["Module Category"]
            subcategory = self.project_model.scripts_in_order[index]["Module SubCategory"]
            script = self.project_model.scripts_in_order[index]["Module Script"]
            model = self.project_model.scripts_in_order[index]["Model"]
            module_name = model["module_name"]
            self.add_script(category, subcategory, script, module_name, self.main_view, model=model)

    def refresh_categories(self):
        categories = get_categories()
        self.main_model.categories = categories
        self.main_model.selected_category = None
        if self.category_combobox is not None:
            self.category_combobox.setCurrentIndex(0)

    def refresh_subcategories(self, new_category=None):
        subcategories = get_subcategories(new_category)
        self.main_model.subcategories = subcategories
        self.main_model.selected_subcategory = None
        if self.subcategory_combobox is not None:
            self.subcategory_combobox.setCurrentIndex(0)

    def refresh_scripts(self, category=None, subcategory=None):
        scripts = get_scripts(category, subcategory)
        self.main_model.scripts = scripts
        self.main_model.selected_script = None
