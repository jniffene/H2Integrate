import pandas as pd
import numpy as np
from itertools import product

# Sensitivity variables
# sens_vars = ["tidal.power_coefficient", "tidal.mod_indep_X_exp", "tidal.mod_indep_Y_exp", "tidal.mod_indep_Z_exp", "tidal.mod_dep_X_exp", "tidal.mod_dep_Y_exp", "tidal.mod_dep_Z_exp", "tidal.mod_indep_alpha", "tidal.mod_indep_beta", "tidal.mod_indep_gamma", "tidal.mod_dep_alpha", "tidal.mod_dep_beta", "tidal.mod_dep_gamma", "tidal.mod_indep_initial_CapEx", "tidal.mod_indep_initial_OpEx", "tidal.mod_dep_initial_CapEx", "tidal.mod_dep_initial_OpEx"]
sens_vars = ["tidal.num_devices"]
# Variables to consider
vars = ["tidal.rotor_radius", "tidal.device_rating"] + sens_vars

# Vary the rotor radius and capacity
r_start = 10
r_end = 30
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)

Pt_start = 2000
Pt_end = 6000
Pt_step = 1000
capacity_vals = np.arange(Pt_start, Pt_end+Pt_step, Pt_step)

# Vary the sensitivity variables
N_i = 50 # initial array size
# Make a matrix full of the values for radius and capacity and the defaults for the sensitivity analysis
vals = np.ones((len(rotor_radii) * len(capacity_vals) * len(sens_vars) * 2, len(vars)))
counter = 0
for a in range(len(sens_vars) * 2):
    for i in range(len(capacity_vals)):
        for j in range(len(rotor_radii)):
            vals[counter,0] = rotor_radii[j]
            vals[counter,1] = capacity_vals[i]
            vals[counter,2] = N_i
            counter = counter + 1

# Adjust the default values for the sensitivity analysis
rp = len(rotor_radii) * len(capacity_vals)
# vals[0:rp,2] = round(2.7*1.3,2)
# vals[rp:2*rp,2] = round(2.7*0.7,2)
# vals[2*rp:3*rp, 3] = 1.3
# vals[3*rp:4*rp, 3] = 0.7
# vals[4*rp:5*rp, 4] = 1.3
# vals[5*rp:6*rp, 4] = 0.7

for i in range(len(sens_vars)*2):
    if i % 2 == 0:
        col = int(2 + i/2)
        vals[i*rp:(i+1)*rp, col] = round(1.3 * vals[i*rp, col], 4)
    else: 
        col = int(2 + (i-1)/2)
        vals[i*rp:(i+1)*rp, col] = round(0.7 * vals[i*rp, col], 4)

# Make dataframe and CSV
varsDF = pd.DataFrame(vars)
varsDF = varsDF.transpose()
varsDF.to_csv('sensitivity_input_cases_extra.csv', index=False, header=False)
valsDF = pd.DataFrame(vals)
valsDF.to_csv('sensitivity_input_cases_extra.csv', index=False, header=False, mode ='a')