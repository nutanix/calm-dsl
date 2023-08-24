# python3;success

username="xxx"
password="xxxx"
server="xxx"
port="1433"
try:
    cnxn = get_sql_handle(server, username, password, port=port, autocommit=True)
    cursor = cnxn.cursor()
    # List all databases
    cursor.execute("""SELECT Name from sys.Databases;""")
    for row in cursor:
        print(row[0])
    cnxn.close()
except Exception as exp:
    print(str(exp) == "Connection to the database failed for an unknown reason.")