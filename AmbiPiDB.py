import sqlite3
import os, sys

class AmbiPiDB:
    def __init__(self):
        self.path = os.path.join(sys.path[0], "ambiPi.db")
        self.createDatabase()

    def getSettings(self, key: str):
        result = self._executeQuery("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return result[0] if result != None else None

    def setSettings(self, key: str, value: int):
        self._executeQuery("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def createDatabase(self):
        self._executeQuery('''CREATE TABLE IF NOT EXISTS settings (
            key VARCHAR PRIMARY KEY,
            value INTEGER NULL)''')

    def _executeQuery(self, sql: str, args: tuple = None):
        with sqlite3.connect(self.path) as con:
            if args == None:
                return con.execute(sql)
            else:
                return con.execute(sql, args)