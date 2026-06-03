import pandas as pd
import numpy as np

# Variables to consider
vars = ["tidal.rotor_radius", "tidal.device_rating"]

# Vary the rotor radius and capacity
r_start = 5
r_end = 50
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)

Pt_start = 2000
Pt_end = 6000
Pt_step = 1000
capacity_vals = np.arange(Pt_start, Pt_end+Pt_step, Pt_step)

# Make a matrix full of the values
vals = np.zeros((len(rotor_radii) * len(capacity_vals), 2))
counter = 0
for i in range(len(capacity_vals)):
    for j in range(len(rotor_radii)):
        vals[counter,0] = rotor_radii[j]
        vals[counter,1] = capacity_vals[i]
        counter = counter + 1

# Make dataframe and CSV
varsDF = pd.DataFrame(vars)
varsDF = varsDF.transpose()
varsDF.to_csv('input_cases.csv', index=False, header=False)
valsDF = pd.DataFrame(vals)
valsDF.to_csv('input_cases.csv', index=False, header=False, mode ='a')