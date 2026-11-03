from .base_odbc import DBText

try:
    import pyodbc
except ModuleNotFoundError:
    pass


class MySQL_DBText(DBText):
    def __init__(self, database=None, master_connection=None, ansi_sql_mode=False):
        super().__init__(database, master_connection)
        self.ansi_sql_mode = ansi_sql_mode

    def quote(self, tablespec):
        if self.ansi_sql_mode:
            return super().quote(tablespec)
        else:
            return "`" + tablespec + "`"

    @classmethod
    def get_driver(cls):
        drivers = []
        for driver in pyodbc.drivers():
            if driver.startswith("MySQL") or driver.startswith("MariaDB"):
                drivers.append(driver)
        if drivers:
            return max(drivers)
        else:
            raise RuntimeError("No suitable drivers found for MySQL, is it installed?")

    @classmethod
    def make_connection_string_template(cls):
        driver = cls.get_driver()
        return "DRIVER={" + driver + "};SERVER=localhost;USER=root;OPTION=3;DATABASE=%s;"
