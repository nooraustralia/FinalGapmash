from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
import time
from flask_cors import CORS, cross_origin
from datetime import datetime, date

import scraper
import db

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/",  methods=['GET'])
@cross_origin()
def start():
    return render_template('index.html')

@app.route('/scraping', methods=['POST'])
@cross_origin()
def scraping():
  error = None
  if request.method == 'POST':
    defaultValues = dict({
      "fbUrl": "",
      "totalEvent": "5",
      "university": [],
      "dateFrom": "",
      "dateTo": ""
    })
    formData = request.form
    payload = defaultValues

    for key in formData:
      if key == 'university':
        payload[key] = formData.getlist('university');
      else:
        payload[key] = formData.get(key, defaultValues[key])

    print('Payload', payload)

    objDb = db.Database()
    objDb.setDbConnection('./db/event_data.db')
    dbConnection = objDb.getDbConnection();

    # clearing event table
    eventTable = objDb.checkTableExistance('events')
        
    if len(eventTable) > 0:
      objDb.clearTable('events')
    
    objScraper = scraper.Scraper(payload);
    
    allDataFrames = []

    if len(payload["fbUrl"])>0:
      fbDataFrame = objScraper.scrapeFb()
      allDataFrames.append(fbDataFrame)

    if len(payload["university"]) > 0:
      for uni in payload["university"]:
        if uni == 'unsw':
          resultUnsw = objScraper.scrapeUnsw()
          allDataFrames.append(resultUnsw)
        elif uni == 'uts':
          resultUts = objScraper.scrapeUts()
          allDataFrames.append(resultUts)
        elif uni == 'usyd':
          resultUsyd = objScraper.scrapeUsyd()
          allDataFrames.append(resultUsyd)
        elif uni == 'wsu':
          resultWsu = objScraper.scrapeWsu()
          allDataFrames.append(resultWsu)

    if len(payload["fbUrl"]) == 0 and len(payload["university"]) == 0:
      return "Please attach 1 source", 400

    print('pre merge',allDataFrames)

    print('merging')
    mergedEvents = objScraper.validateDate(allDataFrames)
    print('after merge: ',mergedEvents)
     
    mergedEvents.to_sql("events", dbConnection, if_exists="replace", index=False)

    objDb.closeDbConnection()
  return jsonify({"status": 200, "message": "success"})

@app.route('/events', methods=['GET'])
@cross_origin()
def events():
  error = None
  if request.method == 'GET':
    objDb = db.Database()
    objDb.setDbConnection('./db/event_data.db')

    mappedData = []
    queryTo = request.args.get("to", 0)
    queryFrom = request.args.get("from", 0)
    queryEventName = request.args.get("eventName", '')
    querySources = request.args.get("sources", '')

    querySourceList = []
    sqlSources = ''
    if querySources:
      querySourceList = list(querySources.split(','))
      for i in range(0, len(querySourceList)):
        if(querySourceList[i] == 'all'):
          sqlSources = "'fb', 'unsw', 'uts', 'wsu', 'usyd'"
          break
        if i == len(querySourceList)-1:
          sqlSources += "'{}'".format(querySourceList[i])
        else:
          sqlSources += "'{}',".format(querySourceList[i])

    today = date.today()
    thisYear = today.strftime("%Y")

    result = objDb.searchEvent(sqlSources, queryEventName)

    if len(result) > 0:
      time.sleep(1)
      for data in result:
        isAllValid = data[10] == 1 and data[11] == 1 and data[12] == 1

        if isAllValid:
          dateFrom = ''
          dateTo = ''
          if data[2]:
            dateFrom = data[2]
            dateFrom = dateFrom+' '+thisYear
            dateFrom = datetime.strptime(dateFrom, "%d %b %Y")

          if data[3]:
            dateTo = data[3]
            dateTo = dateTo+' '+thisYear
            dateTo = datetime.strptime(dateTo, "%d %b %Y")

            
          
          newFromDate = datetime.strptime(queryFrom, "%Y-%m-%d")
          newToDate = datetime.strptime(queryTo, "%Y-%m-%d") 
          
          isWithinFromDate = newFromDate <= dateFrom
          isWithinToDate = newToDate >= dateTo
          isBetweenDate = newToDate <= dateTo and newFromDate >= dateFrom
          isInBetween = isBetweenDate

          if isInBetween or (isWithinFromDate and isWithinToDate):
            newData = {
              "title": data[0],
              "location": data[1],
              "dateFrom": data[2],
              "dateTo": data[3],
              "time": data[4] if data[4] != 'no time available' else "NULL",
              "image": data[5] if data[5] != 'no image available' else "NULL",
              "description": data[6] if data[6] != 'no description available' else "NULL",
              "link": data[7] if data[7] != 'no link available' else 'NULL',
              "fbInterest": data[8] if data[8] != "NA" else "NULL",
              "sourceCode": data[9] if data[9] != None else ""
            }
            mappedData.append(newData)

  return jsonify({"status": 200, "message": "success", "data": mappedData})

@app.route('/event-table', methods=['GET'])
@cross_origin()
def event_table():
  return render_template('event-table.html')

@app.errorhandler(404)
@cross_origin()
def page_not_found(e):
  return render_template('404.html'), 404

if(__name__) == "__main__":
  app.run(debug=True)