import pandas as pd
import numpy as np
from itertools import product
import math

# Sensitivity variables
sens_vars = ["tidal.num_devices", "wind.num_turbines"]
# Variables to consider
vars = ["tidal.rotor_radius", "tidal.device_rating"] + sens_vars

# Vary the rotor radius and capacity
r_start = 10
r_end = 30
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)

Pt_start = 1115
Pt_end = 1115*3
Pt_step = 1115/2
capacity_vals = np.arange(Pt_start, Pt_end+Pt_step, Pt_step)

# fractions of array that is wind
windFracs = [0.3, 0.5, 0.7]

# Vary the sensitivity variables
N_i = 50 # initial array size
# Make a matrix full of the values for radius and capacity and the defaults for the sensitivity analysis
vals = np.ones((len(rotor_radii) * len(capacity_vals) * len(windFracs), len(vars)))
counter = 0
for a in range(len(windFracs)):
    for i in range(len(capacity_vals)):
        for j in range(len(rotor_radii)):
            vals[counter,0] = rotor_radii[j]
            vals[counter,1] = capacity_vals[i]
            vals[counter,2] = N_i
            vals[counter,3] = N_i
            counter = counter + 1

# Adjust the default values for the sensitivity analysis
rp = len(rotor_radii) * len(capacity_vals)

for i in range(len(windFracs)):
    vals[i*rp:(i+1)*rp, 2] = round((1-windFracs[i])*vals[i*rp,2]) # tidal 
    vals[i*rp:(i+1)*rp, 3] = round(windFracs[i]*vals[i*rp,3]) # wind

# print(vals)

# for i in range(len(sens_vars)*2):
#     if i % 2 == 0:
#         col = int(2 + i/2)
#         vals[i*rp:(i+1)*rp, col] = round(1.3 * vals[i*rp, col], 4)
#     else: 
#         col = int(2 + (i-1)/2)
#         vals[i*rp:(i+1)*rp, col] = round(0.7 * vals[i*rp, col], 4)

# Make dataframe and CSV
varsDF = pd.DataFrame(vars)
varsDF = varsDF.transpose()
varsDF.to_csv('hybrid_input_cases.csv', index=False, header=False)
valsDF = pd.DataFrame(vals)
valsDF.to_csv('hybrid_input_cases.csv', index=False, header=False, mode ='a')