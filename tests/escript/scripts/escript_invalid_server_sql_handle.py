# python3;failure
username="admin"
password="Nutanixinvalid"
server="10.10.10.10"
port="1433"
cnxn = get_sql_handle(server, username, password, port=port, autocommit=True)
cursor = cnxn.cursor()
# List all databases
cursor.execute("""SELECT Name from sys.Databases;""")
for row in cursor:
    print(row[0])
cnxn.close()