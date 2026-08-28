import pandas as pd
import numpy as np

# Variables to consider
vars = ["tidal.rotor_radius", "tidal.device_rating"]

# Vary the rotor radius and capacity
r_start = 10
r_end = 30
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)

capacity_vals = 2400

# Make a matrix full of the values
vals = np.zeros((len(rotor_radii), 2))
counter = 0

for j in range(len(rotor_radii)):
    vals[counter,0] = rotor_radii[j]
    vals[counter,1] = capacity_vals
    counter = counter + 1

# Make dataframe and CSV
varsDF = pd.DataFrame(vars)
varsDF = varsDF.transpose()
varsDF.to_csv('input_cases.csv', index=False, header=False)
valsDF = pd.DataFrame(vals)
valsDF.to_csv('input_cases.csv', index=False, header=False, mode ='a')