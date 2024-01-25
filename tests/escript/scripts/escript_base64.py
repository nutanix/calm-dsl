# python3;success

import base64

# Encoding
data = "Python 3 supported script"
data_bytes = data.encode('ascii')
base64_bytes = base64.b64encode(data_bytes)
base64_string = base64_bytes.decode('ascii')
print(base64_string == "UHl0aG9uIDMgc3VwcG9ydGVkIHNjcmlwdA==")

# Decoding
base64_bytes_decode = base64_string.encode('ascii')
data_bytes = base64.b64decode(base64_bytes_decode)
decoded_data = data_bytes.decode('ascii')
pprint(decoded_data == "Python 3 supported script")