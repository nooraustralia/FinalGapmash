import sqlite3
from sqlite3 import Error

class Database:
  def __init__(self):
    self.dbConnection = None
  
  def setDbConnection(self, dbPath):
    try:
      self.dbConnection = sqlite3.connect(dbPath)
    except Error as e:
      print('DB Conn error: ', e)

  def getDbConnection(self):
    return self.dbConnection
  
  def closeDbConnection(self):
    if self.dbConnection:
      self.dbConnection.close()

  def clearTable(self, tableName):
    sql = 'DELETE FROM {}'.format(tableName)
    cur = self.dbConnection.cursor()
    cur.execute(sql)
    self.dbConnection.commit()
  
  def checkTableExistance(self, tableName):
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format(tableName)
    cur = self.dbConnection.cursor()
    result = cur.execute(sql).fetchall()
    self.dbConnection.commit()
    return result
  
  def selectAllFromTable(self, tableName):
    sql = "SELECT * FROM {}".format(tableName)
    cur = self.dbConnection.cursor()
    records = cur.execute(sql).fetchall()
    return records
  
  def searchEvent(self, sources, eventName):
    baseSources = ""
    if sources:
      baseSources= "AND [Source Code] IN ({})".format(sources)
    searchSql = "SELECT * FROM events WHERE [Title] LIKE '%{}%' {};".format(eventName, baseSources);
    cur = self.dbConnection.cursor()
    records = cur.execute(searchSql).fetchall()
    return records