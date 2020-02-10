from calm.dsl.builtins import BlueprintType, read_spec

spec = read_spec("/Users/abhijeet.kaurav/Desktop/aa.json")


bl = BlueprintType.decompile(spec)
import pdb; pdb.set_trace()