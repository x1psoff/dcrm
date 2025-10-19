import mysql.connector
dataBase = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="nounposubal1",

)

cursorObjiect = dataBase.cursor()

cursorObjiect.execute('CREATE DATABASE sait')

print('готово')