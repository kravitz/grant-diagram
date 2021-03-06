from PyQt4 import QtGui, QtCore
from grant_core.init_tables import FieldInteger, FieldText, FieldBool,\
    FieldDate, FieldEnum

class RecordForm(QtGui.QDialog):
    def is_hidden(self, field):
        return field.hidden and field.pk

    def __init__(self, parent, tablename, pkey=None):
        super().__init__(parent)
        self.setModal(True)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.gbox = QtGui.QGridLayout(self)

        fields = app.session.get_fields_description(tablename)
        self.rectype = "add" if pkey is None else "update"
        self.pkey = pkey
        self.tablename = tablename
        rec = pkey and app.session.get_record(tablename, pkey)
        self.rec = rec
        row = 0
        self.ctrls = []
        for i, f in enumerate(fields):
            if not self.is_hidden(f):
                self.place_label(row, f)
                self.place_control(row, f, rec and rec[i])
                row += 1
        self.gbox.addWidget(self.buttonBox, row, 1, 1, 1)
        self.setLayout(self.gbox)

        self.buttonBox.accepted.connect(self.handleAccept)
        self.buttonBox.rejected.connect(self.reject)

        if pkey is not None:
            self.accepted.connect(self.updateRecord)
        else:
            self.accepted.connect(self.addRecord)

    def handleAccept(self):
        for ctrl in self.ctrls:
            if type(ctrl) is QtGui.QDateTimeEdit:
                dt = ctrl.dateTime()
                if dt.date().dayOfWeek() > 5:
                    self.error("Date '{0}' is at a weekend".format(dt.date().toString()))
                    break
                if not 8 <= dt.time().hour() <= 16:
                    self.error("Time '{0}' doesn't fit at work time 8:00 - 16:00".format(dt.time().toString()))
                    break
        else:
            self.accept()

    def error(self, text):
        mbox = QtGui.QMessageBox(
            QtGui.QMessageBox.Critical,
            'Error',
            text,
            QtGui.QMessageBox.Ok)
        mbox.exec()

    def _get_values(self):
        values = []
        for ctrl in self.ctrls:
            if type(ctrl) is QtGui.QLineEdit:
                value = ctrl.text()
            elif type(ctrl) is QtGui.QCheckBox:
                value = ctrl.isChecked()
            elif type(ctrl) is QtGui.QComboBox:
                value = ctrl.itemData(ctrl.currentIndex())
                if value is None:
                    value = ctrl.currentText()
            elif type(ctrl) is QtGui.QDateTimeEdit:
                dt = ctrl.dateTime()
                t = dt.time()
                t.setHMS(t.hour(), 0, 0)
                dt.setTime(t)
                value = dt.toString(QtCore.Qt.ISODate)
            elif type(ctrl) is QtGui.QSpinBox:
                value = ctrl.value()
            values.append(value)
        return values

    def updateRecord(self):
        values = self._get_values()
        app.session.update_record(self.tablename, values, list(self.pkey))
        for w in app.mainwindow.ui.mdiArea.subWindowList():
            w.widget().updateTable()

    def addRecord(self):
        values = self._get_values()
        app.session.add_record(self.tablename, values)
        for w in app.mainwindow.ui.mdiArea.subWindowList():
            w.widget().updateTable()

    def place_label(self, row, field):
        label = QtGui.QLabel(self)
        label.setText(field.verbose_name)
        self.gbox.addWidget(label, row, 0, 1, 1)

    def createComboBox(self, field, value):
        ctrl = QtGui.QComboBox(self)
        items = app.session.get_fk_values(field)
        for n, i in enumerate(items):
            ctrl.addItem(i[1], i[0])
            if value is not None and value == i[0]:
                ctrl.setCurrentIndex(n)
        return ctrl

    def createCheckBox(self, field, value):
        ctrl = QtGui.QCheckBox(self)
        if value is not None:
            ctrl.setChecked(value == 1)
        return ctrl

    def createDateTimeEdit(self, field, value):
        if value is not None:
            datetime = QtCore.QDateTime.fromString(value, QtCore.Qt.ISODate)
        else:
            datetime = QtCore.QDateTime.currentDateTime()
        ctrl = QtGui.QDateTimeEdit(datetime, self)
        ctrl.setCalendarPopup(True)
        ctrl.setDisplayFormat("yyyy.MM.dd hh:00") # Precise to +-1 hour
        return ctrl

    def createEnumComboBox(self, field, value):
        ctrl = QtGui.QComboBox(self)
        items = field.values
        for n, i in enumerate(items):
            ctrl.addItem(i)
            if value is not None and value == i:
                ctrl.setCurrentIndex(n)
        return ctrl

    def createSpinEdit(self, field, value):
        ctrl = QtGui.QSpinBox(self)
        if value is not None:
            ctrl.setValue(value)
        ctrl.setMinimum(1)
        ctrl.setMaximum(9999)
        return ctrl

    def createLineEdit(self, field, value):
        ctrl = QtGui.QLineEdit(self)
        if value is not None:
            ctrl.setText(field.convert(value))
        return ctrl

    def place_control(self, row, field, value=None):
        if field.fk:
            ctrl = self.createComboBox(field, value)
        elif type(field) is FieldBool:
            ctrl = self.createCheckBox(field, value)
        elif type(field) is FieldDate:
            ctrl = self.createDateTimeEdit(field, value)
        elif type(field) is FieldEnum:
            ctrl = self.createEnumComboBox(field, value)
        elif type(field) is FieldInteger:
            ctrl = self.createSpinEdit(field, value)
        else:
            ctrl = self.createLineEdit(field, value)
        self.ctrls.append(ctrl)
        self.gbox.addWidget(ctrl, row, 1, 1, 1)


class CompaniesRecordForm(RecordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = self.ctrls[0].text()

    def handleAccept(self):
        name_edit = self.ctrls[0]
        name = name_edit.text()
        if not len(name):
            self.error("Company name cann't be empty")
        elif (not self.pkey or name != self.name) and not app.grant.check_company_name_is_free(name):
            self.error("This name is already occupied")
        else:
            super().handleAccept()


class DevelopersRecordForm(RecordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handleAccept(self):
        fname = self.ctrls[0].text()
        username = self.ctrls[1].text()
        password = self.ctrls[-2].text()
        is_admin = self.ctrls[-1].isChecked()
        if any(not(len(f)) for f in (fname, username, password)):
            self.error("Text fields cann't be empty")
        elif (not self.pkey or self.pkey[0] != username) and not app.grant.check_username_is_free(username):
            self.error("User with such username already exists")
        elif not is_admin and not app.grant.has_admins(self.pkey and self.pkey[0]):
            self.error("You can't leave database without admins")
        else:
            super().handleAccept()


class ProjectsRecordForm(RecordForm):
    def handleAccept(self):
        prjname = self.ctrls[0].text()
        datebegin = self.ctrls[1].dateTime()
        dateend = self.ctrls[2].dateTime()
        if not len(prjname):
            self.error("Project name cann't be empty")
        elif dateend <= datebegin:
            self.error("Project end date must be greater than begin date")
        else:
            super().handleAccept()


class ContractsRecordForm(RecordForm):
    def createComboBox(self, field, value):
        if field.name == 'company_id':
            ctrl = QtGui.QComboBox(self)
            items = app.session.get_fk_values(field, exclude=1)
            for n, i in enumerate(items):
                ctrl.addItem(i[1], i[0])
                if value is not None and value == i[0]:
                    ctrl.setCurrentIndex(n)
        else:
            ctrl = super().createComboBox(field, value)
        return ctrl

class Developers_distributionRecordForm(RecordForm):
    # TODO:
    # fix pkey violation integrity error
    def handleAccept(self):
        if app.grant.has_distributed_pkey(
            self.ctrls[0].itemData(self.ctrls[0].currentIndex()),
            self.ctrls[1].itemData(self.ctrls[1].currentIndex())):
            self.error("You already assigned this user to this project")
        else:
            super().handleAccept()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctrls[1].currentIndexChanged.connect(self.refillDevelopers)
        self.ctrls[1].currentIndexChanged.emit(self.ctrls[1].currentIndex())

    def createComboBox(self, field, value):
        if app.session.is_admin:
            ctrl = super().createComboBox(field, value)
        else:
            ctrl = QtGui.QComboBox(self)
            items = app.session.get_prj_fk_for_manager()
            for n, (i, v) in enumerate(items):
                ctrl.addItem(v, i)
                if value is not None and value == i:
                    ctrl.setCurrentIndex(n)
        return ctrl

    @QtCore.pyqtSlot(int)
    def refillDevelopers(self, index):
        project_id = self.ctrls[1].itemData(index)
        ctrl = self.ctrls[0]
        ctrl.clear()
        developers = app.grant.get_available_developers(project_id)
        for i, d in developers:
            ctrl.addItem(d, i)
        if self.rec and self.rec[1] == project_id:
            for i in range(0, len(ctrl)):
                if self.rec[0] == ctrl.itemData(i):
                    ctrl.setCurrentIndex(i)
                    break


class TasksRecordForm(RecordForm):
    def handleAccept(self):
        if self.is_not_manager and self.ctrls[-1].currentText() == 'delayed':
            self.error("You can\'t mark task as delayed")
        elif self.ctrls[-1].currentText() == 'finished' and self.unfinishedDependencies():
            self.error("You can't close task with unfinished dependencies")
        elif len(self.ctrls[0].text()) == 0:
            self.error("Can't leave task title empty")
        elif len(self.ctrls[1].text()) == 0:
            self.error("Can't leave task description empty")
        else:
            super().handleAccept()

    def __init__(self, parent, tablename, pkey=None, is_not_manager=False):
        self.is_not_manager = is_not_manager
        super().__init__(parent, tablename, pkey)
        if self.is_not_manager:
            for ctrl in self.ctrls[:-1]:
                ctrl.setDisabled(True)

    def createComboBox(self, field, value):
        if app.session.is_admin or self.is_not_manager:
            ctrl = super().createComboBox(field, value)
        else:
            ctrl = QtGui.QComboBox(self)
            items = app.session.get_prj_fk_for_manager()
            for n, (i, v) in enumerate(items):
                ctrl.addItem(v, i)
                if value is not None and value == i:
                    ctrl.setCurrentIndex(n)
        return ctrl

    def unfinishedDependencies(self):
        if self.pkey is None:
            return False
        task_id = self.pkey[0]
        return app.grant.has_unfinished_dependencies(task_id)

class ReportsRecordForm(RecordForm):
    def handleAccept(self):
        if self.moreThanOneWorkAtSameTime():
            self.error("You can't do more than one job at same time")
        elif self.unfinishedDependencies():
            self.error("You can't work on task with unfinished dependencies")
        elif len(self.ctrls[-1].text()) == 0:
            self.error("You can't leave an empty description")
        else:
            super().handleAccept()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctrls[-4].currentIndexChanged.emit(self.ctrls[-4].currentIndex())

    def unfinishedDependencies(self):
        i = 0
        if app.session.is_admin:
            i = 1
        task_id = self.ctrls[i].itemData(self.ctrls[i].currentIndex())
        return app.grant.has_unfinished_dependencies(task_id)


    def moreThanOneWorkAtSameTime(self):
        values = self._get_values()
        count = app.session.countReportsForDateTimeSice(values[2], values[3], exclude=self.pkey, username=values[0])
        return count > 0

    def is_hidden(self, field):
        return super().is_hidden(field) or (field.name == 'developer_username'
            and not app.session.is_admin)

    def _get_values(self):
        values = super()._get_values()
        if not app.session.is_admin:
            values.insert(0, app.session.username)
        return values

    @QtCore.pyqtSlot(int)
    def refillTasksSelect(self, index):
        ctrl = self.ctrls[1]
        data = ctrl.itemData(ctrl.currentIndex())
        ctrl.currentIndexChanged.disconnect(self.getProjectInfo)
        ctrl.clear()
        username = self.ctrls[0].currentText()
        items = app.session.get_developers_tasks(username)
        for n, (i, v) in enumerate(items):
            ctrl.addItem(v, i)
            if data == i:
                ctrl.setCurrentIndex(n)
        ctrl.currentIndexChanged.connect(self.getProjectInfo)
        ctrl.currentIndexChanged.emit(ctrl.currentIndex())

    @QtCore.pyqtSlot(int)
    def getProjectInfo(self, index):
        if app.session.is_admin:
            ctrl = self.ctrls[1]
        else:
            ctrl = self.ctrls[0]
        task_id = ctrl.itemData(index)
        print(task_id)
        project_begin = QtCore.QDateTime.fromString(app.grant.get_project_begin_for_task(task_id)[0], QtCore.Qt.ISODate)
        bctrl = self.ctrls[-3]
        ectrl = self.ctrls[-2]
        for ctrl in (bctrl, ectrl):
            ctrl.setMinimumDateTime(project_begin)


    def createComboBox(self, field, value):
        if field.name == 'task_id':
            ctrl = QtGui.QComboBox(self)
            if app.session.is_admin:
                username = self.ctrls[0].currentText()
            else:
                username = app.session.username
            items = app.session.get_developers_tasks(username)
            for n, (i, v) in enumerate(items):
                ctrl.addItem(v, i)
                if value is not None and value == i:
                    ctrl.setCurrentIndex(n)
            ctrl.currentIndexChanged.connect(self.getProjectInfo)
        elif app.session.is_admin and field.name == 'developer_username':
            ctrl = QtGui.QComboBox(self)
            items = app.session.get_distributed_developers()
            for n, (i, v) in enumerate(items):
                ctrl.addItem(v, i)
                if value is not None and value == i:
                    ctrl.setCurrentIndex(n)
            ctrl.currentIndexChanged.connect(self.refillTasksSelect)
        else:
            ctrl = super().createComboBox(field, value)
        return ctrl


class Tasks_dependenciesRecordForm(RecordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctrls[0].currentIndexChanged.connect(self.refillTasks)
        self.ctrls[0].currentIndexChanged.emit(self.ctrls[0].currentIndex())

    def handleAccept(self):
        cicle_error = "Circular dependency detected"
        if self.ctrls[0].currentText() == self.ctrls[1].currentText():
            self.error(cicle_error)
        elif self.haveCicle():
            self.error(cicle_error)
        else:
            super().handleAccept()

    def haveCicle(self):
        t, d = [c.itemData(c.currentIndex()) for c in self.ctrls]
        deps = app.grant.get_available_tasks_dependencies(t)
        if self.rec:
            deps.remove(self.rec)
        graph = {}
        for t, d in deps + [(t, d)]:
            if t in graph:
                graph[t].append(d)
            else:
                graph[t] = [d]
        trace = set((t,))

        def dfs(i):
            if i in trace:
                return True
            trace.add(i)
            if i in graph and any(dfs(d) for d in graph[i]):
                return True
            trace.remove(i)
            return False

        return dfs(d)

    def createComboBox(self, field, value):
        if app.session.is_admin or field.name != 'task_id':
            ctrl = super().createComboBox(field, value)
        else:
            ctrl = QtGui.QComboBox(self)
            items = app.session.get_tasks_fk_for_manager()
            for n, (i, v) in enumerate(items):
                ctrl.addItem(v, i)
                if value is not None and value == i:
                    ctrl.setCurrentIndex(n)
        return ctrl

    @QtCore.pyqtSlot(int)
    def refillTasks(self, index):
        task_id = self.ctrls[0].itemData(index)
        ctrl = self.ctrls[1]
        ctrl.clear()
        tasks = app.grant.get_available_tasks(task_id)
        for n, (i, v) in enumerate(tasks):
            ctrl.addItem(v, i)
            if self.rec is not None and self.rec[1] == i:
                ctrl.setCurrentIndex(n)

