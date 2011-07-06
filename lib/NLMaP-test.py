#!/usr/bin/env python
from math import sqrt
import NLMaP

x = [0.0, 2.0, 0.0, 1.0, 0.0]
y = [0.0, 0.0, 2.0, 1.0, 0.0]
z = [1.0, 1.0, 1.0, 2.0, 1.0]
d = [1.7, sqrt(3.0), sqrt(3.0), 2.1, sqrt(3.0)]
s = [1.0, 1.0, 1.0, 1.0, 10.0]
m = NLMaP.MultiLateration(x,y,z,d,s,5)