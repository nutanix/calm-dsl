
load-db-data:
	# Load data from db to create some files
	# get_data_from_file.py True -> to load data from db
	# get_data_from_file.py False -> to not load data from db
	../../venv/bin/python3 get_data_from_db.py False

mock-db-location:
	# Create and point init.ini to mock db location.
	../../venv/bin/python3 mock_dsl_config.py True

mock-db:
	# Load current data to db
	# mock_dsl_db.py True -> to initialize mock db
	# mock_dsl_db.py False -> to use existing db in cache
	../../venv/bin/python3 mock_dsl_db.py True
