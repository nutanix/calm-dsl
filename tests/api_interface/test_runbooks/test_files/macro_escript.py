print("These macros are from parser_test.go --------------")

# basic
print("@@{calm_random}@@")
print("@@{calm_unique}@@")
print("@@{AZ_RANDOM}@@")
print("@@{AZ_UNIQUE}@@")
print("@@{calm_random_hash}@@")
print("@@{calm_random_hex}@@")
print("@@{AZ_RANDOM_HASH}@@")
print("@@{AZ_RANDOM_HEX}@@")

print("@@{AZ_B64ENCODE(calm_unique)}@@")
print("@@{calm_b64encode(calm_unique)}@@")

# Base64 Decode
print("@@{AZ_B64ENCODE(calm_b64encode(calm_random))}@@")
print("@@{calm_b64decode(calm_b64encode(calm_random))}@@")
print('@@{calm_b64decode(calm_b64encode("日本語"))}@@')

# calm_random
print("@@{calm_random_hash(2)}@@")
print("@@{calm_random_hash}@@")
print("@@{calm_random_hex(2)}@@")
print("@@{calm_random_hex}@@")
print("@@{AZ_RANDOM_HASH(2)}@@")
print("@@{AZ_RANDOM_HASH}@@")
print("@@{AZ_RANDOM_HEX(2)}@@")
print("@@{AZ_RANDOM_HEX}@@")

# calm_int
print("@@{calm_int(2)}@@")
print("@@{calm_int(AZ_INT(-3.6))}@@")
print("@@{calm_int(calm_float(4.5))}@@")

# calm_float
print("@@{calm_float(2.5)}@@")
print('@@{AZ_FLOAT("-4")}@@')
print("@@{calm_float(calm_int(1.5))}@@")

# calm_string
print("@@{calm_string(2.505)}@@")
print("@@{calm_string(calm_int(1))}@@")
print('@@{AZ_STRING("string")}@@')
print('@@{calm_string(calm_int(calm_string("123")))}@@')
print("""@@{calm_string(AZ_JSON_LOAD('{"value": false}').get('value'))}@@""")

# AZ_LEN with split
print('@@{AZ_LEN("hello,world,now,forever,moon,sun", ",")}@@')
print('@@{AZ_LEN("hello,world你好！你好吗notbeforecomma,now,forever,moon,sun", ",")}@@')

# AZ_LEN without split
print('@@{AZ_LEN("Hello")}@@')
print('@@{AZ_LEN("€")}@@')

# JSONLoadAndDumpBasic
print("""@@{AZ_JSON_DUMP(AZ_JSON_LOAD('{"strs":["a","b"],"hello":{"1":true}}'))}@@""")
print('@@{AZ_JSON_DUMP(AZ_JSON_LOAD("1"))}@@')

# JSONRelationalBasic
print("""@@{AZ_JSON_LOAD('{"Name":"Platypus","Order":"Monotremata"}').get('Name')}@@""")

# JSON Relational Nested
print(
    """@@{AZ_JSON_LOAD('{"num":6.13,"strs":["a","b"],"hello":{"1":"2"}}').get('hello').get('1')}@@"""
)

# AZ_TIME
print("@@{calm_time}@@")
print("@@{AZ_TIME('%y%m%d-%H%M%S')}@@")
print("@@{AZ_TIME('%y%m%d-%H%M%S', 'gmt')}@@")

# AZ_SPLIT
print('@@{AZ_SPLIT("hello,world你好！你好吗notbeforecomma,now,forever,moon,sun", ",")}@@')

# AZ_DAY
print("@@{AZ_DAY('month','gmt')}@@")
print("@@{AZ_DAY('year','utc')}@@")
print("@@{calm_day('month','gmt')}@@")
print("@@{calm_day('year')}@@")
print("@@{calm_day('year',        'utc')}@@")

# AzMonthShort
print("@@{AZ_MONTH('short')}@@")
print("@@{AZ_MONTH('short','gmt')}@@")
print("@@{calm_month('short','utc')}@@")

# AZ_REPLACE
print('@@{AZ_REPLACE("x(p*)y", "B", "xy--xpppyxxppxy-")}@@')
print('@@{AZ_REPLACE("x(p*)y", "$1P", "xy--xpppyxxppxy-")}@@')
print('@@{AZ_REPLACE("x(p*)y", "${1}Q", "xy--xpppyxxppxy-")}@@')

# AZ_MONTH LONG
print("@@{AZ_MONTH('long','gmt')}@@")
print("@@{calm_month('long')}@@")
print("@@{calm_month('long','gmt')}@@")

# AZ_MONTH
print("@@{AZ_MONTH('mm')}@@")
print("@@{AZ_MONTH('mm','utc')}@@")
print("@@{calm_month('mm','gmt')}@@")

# AZ_JOIN
print("""@@{AZ_JOIN(AZ_JSON_LOAD('["a", "b", "c"]') , ',')}@@""")

# AzYearFormat
print("@@{AZ_YEAR('yy')}@@")
print("@@{calm_year('yy','gmt')}@@")
print("@@{calm_year('yy','utc')}@@")

# AzYear
print("@@{AZ_YEAR('yyyy')}@@")
print("@@{calm_year('yyyy','gmt')}@@")
print("@@{calm_year('yyyy','utc')}@@")

# AzWeekdayShort
print("@@{AZ_WEEKDAY('name_short')}@@")
print("@@{calm_weekday('name_short','gmt')}@@")
print("@@{calm_weekday('name_short','utc')}@@")


# TestAzWeekdayLong
print("@@{AZ_WEEKDAY('name_long')}@@")
print("@@{calm_weekday('name_long','gmt')}@@")
print("@@{calm_weekday('name_long','utc')}@@")

# TestAzIsWeekday
print("@@{AZ_IS_WEEKDAY()}@@")
print("@@{calm_is_weekday()}@@")
print("@@{AZ_IS_LONG_WEEKDAY()}@@")
print("@@{calm_is_long_weekday()}@@")
print("@@{AZ_IS_WEEKDAY('gmt')}@@")
print("@@{AZ_IS_WEEKDAY('utc')}@@")
print("@@{calm_is_weekday('gmt')}@@")
print("@@{calm_is_weekday('utc')}@@")
print("@@{AZ_IS_LONG_WEEKDAY('gmt')}@@")
print("@@{AZ_IS_LONG_WEEKDAY('utc')}@@")
print("@@{calm_is_long_weekday('gmt')}@@")
print("@@{calm_is_long_weekday('utc')}@@")

# TestAzWeekNumber
print("@@{AZ_WEEKNUMBER}@@")
print("@@{AZ_WEEKNUMBER('gmt')}@@")
print("@@{AZ_WEEKNUMBER('utc')}@@")
print("@@{AZ_WEEKNUMBER('gmt','iso')}@@")
print("@@{calm_weeknumber()}@@")
print("@@{calm_weeknumber('iso')}@@")
print("@@{calm_weeknumber('iso','gmt')}@@")
print("@@{calm_weeknumber('utc','iso')}@@")

# TestAzMinute
print("@@{AZ_MINUTE()}@@")
print("@@{AZ_MINUTE('gmt')}@@")
print("@@{calm_minute()}@@")
print("@@{calm_minute('utc')}@@")

# TestAzSecond
print("@@{AZ_SECOND()}@@")
print("@@{AZ_SECOND('gmt')}@@")
print("@@{calm_second}@@")
print("@@{calm_second('utc')}@@")

# TestAzHour
print("@@{AZ_HOUR('am_pm')}@@")
print("@@{AZ_HOUR('12')}@@")
print("@@{AZ_HOUR('am_pm','utc')}@@")
print("@@{calm_hour('am_pm','gmt')}@@")
print("@@{calm_hour('12','gmt')}@@")
print("@@{calm_hour('12','utc')}@@")

# TestAzNow
print("@@{calm_now()}@@")
print("@@{calm_now}@@")
print("@@{calm_today}@@")
print("@@{AZ_TODAY()}@@")
print("@@{AZ_TODAY('gmt')}@@")

# calm_hour
print("@@{AZ_HOUR('24')}@@")
print("@@{calm_hour('24','gmt')}@@")
print("@@{calm_hour('24','utc')}@@")

# TestAzRunID
print("@@{AZ_RUN_ID()}@@")
print("@@{AZ_ID()}@@")

# TestAzNoOp
print("@@{AZ_NOOP()}@@")

# TestAzEntityMachineCredentialShort
print("@@{AZ_ENTITY('machine-ids')}@@")
print("@@{AZ_ENTITY('machine-uuids')}@@")
print("@@{AZ_MACHINE('machine-uuids')}@@")
print("@@{AZ_MACHINE('credential-uids')}@@")
print("@@{AZ_CREDENTIAL('credential-uids')}@@")
print("@@{AZ_ENTITY('credential-uids')}@@")

# AZ_Task
print("@@{AZ_TASK('trlid')}@@")
print("@@{AZ_TASK('status')}@@")
print("@@{AZ_TASK('exitcode')}@@")
print("@@{AZ_TASK('reason')}@@")

# These macros are from parser_cp_test.go
print("These macros are from parser_cp_test.go --------------")

# TestAzList
print("""@@{AZ_LIST(Entity(id=entity_id).get(Machine('name')))}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Credential('name')))}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Machine('name')),delimiter=';')}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Credential('name')),delimiter=';')}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Machine('address')))}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Credential('uid')))}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Machine('address')),delimiter=';')}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Credential('uid')),delimiter=';')}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Machine('ssh_port')))}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Credential('secret')))}@@""")
print("""@@{AZ_LIST(Entity(id=entity_id).get(Machine('ssh_port')), delimiter=';')}@@""")
print(
    """@@{AZ_LIST(Entity(id=entity_id).get(Credential('secret')), delimiter=';')}@@"""
)

# TestAzListProperty
print("""@@{AZ_LIST(Machine(id=machine_id).get(Property("error_detail")))}@@""")
print("""@@{AZ_LIST(Credential(name="cred1").get(Property("passphrase")))}@@""")
print("""@@{AZ_LIST(Entity(name="macro-entity").get(Property("prop1")))}@@""")
print(
    """@@{AZ_LIST(Entity(name="macro-entity").get(Property("ALL")), delimiter=' ')}@@"""
)

# TestAzListPropertyFailure
print("""@@{AZ_LIST(Machine(id=machine_id).get(Property("does-not-exist")))}@@""")
print("""@@{AZ_LIST(Credential(name="cred1").get(Property("does-not-exit")))}@@""")
print("""@@{AZ_LIST(Entity(name="macro-entity").get(Property("does-not-exit")))}@@""")

# calm_jwt
print("""@@{calm_jwt}@@""")
