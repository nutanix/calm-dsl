# python3;success
names_yaml = """
- 'eric'
- 'justin'
- 'mary-kate'
"""
names = yaml.safe_load(names_yaml)
print(names)