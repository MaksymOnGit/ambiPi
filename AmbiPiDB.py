import sqlite3
import os, sys

class AmbiPiDB:
    def __init__(self):
        self.path = os.path.join(sys.path[0], "ambiPi.db")
        self.createDatabase()

    def getSetting(self, key: str):
        result = self._executeQuery("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return result[0] if result != None else None

    def setSetting(self, key: str, value: int):
        self._executeQuery("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def initSetting(self, key: str, value: int):
        self._executeQuery("INSERT INTO settings (key, value) SELECT ?, ? WHERE NOT EXISTS(SELECT 1 FROM settings WHERE key = ?)", (key, value, key))

    def saveStatistics(self, fps, temp):
        self._executeQuery("INSERT INTO statistics (fps, cpuTemp) VALUES (?, ?)", (fps, temp))

    def getStatistics(self):
        result = self._executeQuery("SELECT fps, round(cpuTemp) FROM statistics")
        return result.fetchall()

    def createDatabase(self):
        self._executeQuery('''CREATE TABLE IF NOT EXISTS settings (
            key VARCHAR PRIMARY KEY,
            value INTEGER NULL)''')

        self._executeQuery('''CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fps INTEGER NULL,
            cpuTemp INTEGER NULL);''')

        self._executeQuery('''
            CREATE TRIGGER IF NOT EXISTS delete_tail AFTER INSERT ON statistics
            BEGIN
                DELETE FROM statistics WHERE id%100=NEW.id%100 AND id!=NEW.id;
            END;''')

    def _executeQuery(self, sql: str, args: tuple = None):
        with sqlite3.connect(self.path) as con:
            if args == None:
                return con.execute(sql)
            else:
                return con.execute(sql, args)