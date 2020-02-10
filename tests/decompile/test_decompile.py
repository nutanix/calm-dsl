from calm.dsl.builtins import BlueprintType, read_spec

spec = read_spec("sample.json")


bl = BlueprintType.decompile(spec)

print(bl)
