from h2integrate.core.dict_utils import update_defaults
from h2integrate.core.file_utils import load_yaml, check_file_format_for_csv_generator
from h2integrate.core.h2integrate_model import H2IntegrateModel
import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd

model = H2IntegrateModel("input_config.yaml")
model.setup()
hours = 24*365
vel_t = np.zeros(hours)
time = np.zeros(hours)
# Amp = (4)/2
# # periodT = 24
# periodT = 12
# # movUp = Amp
# movUp = 0
# # movSide = -1*np.pi/2
# movSide = 0
# for i in range(len(vel_t)):
#     # vel_t[i] = Amp*math.sin(2*np.pi/periodT*(i+1) + movSide) + movUp
#     vel_t[i] = abs(Amp*math.sin(2*np.pi/periodT*(i+1) + movSide) + movUp)
#     time[i] = i+1

df = pd.read_csv('AK_cook_inlet_tidal_resource_2005.csv', usecols=['Mean Current Speed (m/s)'])
vel_t = df.values.tolist()
for i in range(len(vel_t)):
    time[i] = i+1

model.prob.set_val("tidal.tidal_velocity", vel_t, units="m/s")

# Vary the rotor radius and capacity and determine the LCOE and Breakeven Carbon Credit Cost
r_start = 10
r_end = 30
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)

Pt_start = 2000
Pt_end = 4000
Pt_step = 500
capacity_vals = np.arange(Pt_start, Pt_end+Pt_step, Pt_step)

# Initialize arrays to store results
lcoe_results = np.zeros((len(rotor_radii), len(capacity_vals)))
becc_results = np.zeros((len(rotor_radii), len(capacity_vals)))

# Make counter to track progress
counter = 1
total_runs = len(rotor_radii)*len(capacity_vals)

for i in range(len(rotor_radii)):
    for j in range(len(capacity_vals)):
        # Indicate which simulation is active
        print(f"Running simulation {counter} of {total_runs} total", end="\r")
        counter = counter + 1

        # set the rotor radius and capacity directly
        model.model.set_val("tidal.rotor_radius", rotor_radii[i])
        model.model.set_val("tidal.device_rating", capacity_vals[j])

        # Rerun the model with the updated configuration
        model.run()

        # Get the outputs values of interest
        lcoe = model.model.get_val("finance_subgroup_electricity.LCOE", units="USD/kW/h")[0]
        becc = model.model.get_val("oae.carbon_credit_value", units="USD/t")[0]

        # Store the results
        lcoe_results[i,j] = lcoe
        becc_results[i,j] = becc

# Plot velocity used
plt.plot(time, vel_t)
plt.xlabel("Time (Hours)")
plt.ylabel("Tidal Velocity (m/s)")
plt.title("Annual Tidal Resource Considered in Analysis")
plt.grid(True)
plt.show()

# Create scatter plots
for j in range(len(capacity_vals)):
    plt.scatter(rotor_radii*2, lcoe_results[:, j], label = f"{capacity_vals[j]/1000} MW")
plt.xlabel("Rotor Diameter (m)")
plt.ylabel("LCOE ($/kWh)")
plt.title("LCOE vs Tidal Rotor Diameter & Device Capacity\n(TIGER 50 Unit Array with All Secondary Improvements & Cook Inlet, AK Currents)")
plt.legend()
plt.grid(True)
plt.show()

for j in range(len(capacity_vals)):
    plt.scatter(rotor_radii*2, becc_results[:, j], label = f"{capacity_vals[j]/1000} MW")
plt.xlabel("Rotor Diameter (m)")
plt.ylabel("Break Even Carbon Credit Cost ($/tCO2)")
plt.title("Break Even Carbon Credit Cost vs Tidal Rotor Diameter & Device Capacity\n(100 ktCO2/yr Scale OAE Plant with TIGER 50 Unit Array with All Secondary Improvements & Cook Inlet, AK Currents)")
plt.legend()
plt.grid(True)
plt.show()

