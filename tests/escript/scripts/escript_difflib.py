# python3;success

import difflib  
from difflib import SequenceMatcher  
  
# defining the strings  
str_1 = "Welcome to"  
str_2 = "Welcome to"  
  
# using the SequenceMatcher() function  
my_seq = SequenceMatcher(a = str_1, b = str_2)  
print(my_seq.ratio())