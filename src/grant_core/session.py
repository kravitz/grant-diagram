class Session(object):
    COMMON = set({'logout','login','get_companies'})
    ADMIN_ONLY = set({'add_developer','add_company'})
    AUTHORIZED_ONLY = set({})
    def __init__(self, application, username=None, password=None, is_admin=False):
        self.application = application
        self.grant = self.application.grant
        self.is_admin = is_admin
        self.username = username
        self.password = password

    def process_commands(self, command, args):
        if self.username is None and command in self.AUTHORIZED_ONLY:
            return "Can't use {0} in unauthorized mode".format(command)
        if (self.is_admin and command in self.ADMIN_ONLY) or (command in self.COMMON):
            return getattr(self, command)(*args)
        return "Unknown command {0}".format(command)

    def get_table(self, tablename):
        return self.grant.get_table(tablename)

    def get_headers(self, tablename):
        return self.grant.get_headers(tablename)

    def get_fields_description(self, tablename):
        return self.grant.get_fields_description(tablename)

    def get_record(self, tablename, pkeys):
        return self.grant.get_record(tablename, pkeys)

    def update_record(self, tablename, values, pk):
        return self.grant.update_record(tablename, values, pk)

    def delete_record(self, tablename, pk):
        return self.grant.delete_record(tablename, pk)

    def add_record(self, tablename, values):
        return self.grant.add_record(tablename, values)

    def get_fk_values(self, field, exclude=None):
        values = self.grant.get_fk_values(field, exclude)
        verbose = field.verbose_field
        result = [(v[0], verbose.convert(v[1])) for v in values]
        return result

    def has_distributed(self):
        return self.grant.has_distributed(self.username)

    def get_developers_tasks(self, username=None):
        return self.grant.get_developers_tasks(username or self.username)

    def get_distributed_developers(self):
        return self.grant.get_distributed_developers()

    def get_tasks_projects_id(self):
        return self.grant.get_tasks_projects_id()

    def get_tasks_dependencies_projects_id(self):
        return self.grant.get_tasks_dependencies_projects_id()

    def get_managed_projects(self):
        return self.grant.get_managed_projects(self.username)

    def get_distributed_to(self):
        return self.grant.get_distributed_to(self.username)

    def get_prj_fk_for_manager(self):
        return self.grant.get_prj_fk_for_manager(self.username)

    def get_available_developers(self, project_id):
        return self.grant.get_available_developers(project_id)

    def get_available_tasks_for_project(self, project_id):
        return self.grant.get_available_tasks_for_project(project_id)

    def get_tasks_for_gantt(self, project_id):
        return self.grant.get_tasks_for_gantt(project_id)

    def get_tasks_fk_for_manager(self):
        return self.grant.get_tasks_fk_for_manager(self.username)

    def countReportsForDateTimeSice(self, begin_date, end_date, exclude=None, username=None):
        return self.grant.countReportsForDateTimeSice(begin_date, end_date, username or self.username, exclude)

    def logout(self):
        self.application.session = None
        return "Successfully logged out"

    def login(self, username, password):
        return self.application.login(username, password)

    def add_developer(self, username, password, fullname, company, is_admin):
        self.grant.add_developer(username, password, fullname, company, is_admin)
        return "developer added"

    def add_company(self, name):
        self.grant.add_company(name)
        return "company added"

    def get_companies(self):
        return self.grant.get_companies()

    def __repr__(self):
        return '<Session (username => "{0}")>'.format(self.username)
