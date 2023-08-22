# List the current tables present in the database
PGPASSWORD=@@{database_password}@@ psql -h @@{user_provided_static_ip}@@ -p 5432 -U @@{database_user}@@ @@{initial_database_name}@@ -c '\dt'

# Create a new table
PGPASSWORD=@@{database_password}@@ psql -h @@{user_provided_static_ip}@@ -p 5432 -U @@{database_user}@@ @@{initial_database_name}@@ -c 'CREATE TABLE employee_details(id int PRIMARY KEY, name VARCHAR(40), designation VARCHAR(50));'

# Verify the table creation
PGPASSWORD=@@{database_password}@@ psql -h @@{user_provided_static_ip}@@ -p 5432 -U @@{database_user}@@ @@{initial_database_name}@@ -c '\dt'