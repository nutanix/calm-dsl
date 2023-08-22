# python2;success

print uuid.uuid4() == uuid.uuid4()

val = """number: 3.14
string: !!str 3.14
"""
pprint(yaml.safe_load(val))
