from h2integrate.core.dict_utils import update_defaults
from h2integrate.core.file_utils import load_yaml, check_file_format_for_csv_generator
from h2integrate.core.h2integrate_model import H2IntegrateModel
import numpy as np
import matplotlib.pyplot as plt
import math

model = H2IntegrateModel("input_config.yaml")
model.setup()
hours = 24*365
# v = 4 * np.ones(hours)
# model.prob.set_val("tidal.tidal_velocity", v, units="m/s")
hours = 24*365
vel_t = np.zeros(hours)
Amp = (4)/2
periodT = 24
movUp = Amp
movSide = -1*np.pi/2
for i in range(len(vel_t)):
    vel_t[i] = Amp*math.sin(2*np.pi/periodT*(i+1) + movSide) + movUp

model.prob.set_val("tidal.tidal_velocity", vel_t, units="m/s")

# Vary the rotor radius and determine the LCOE and Breakeven Carbon Credit Cost
r_start = 10
r_end = 25
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)

# Initialize arrays to store results
lcoe_results = []
becc_results = []

for rotor_radius in rotor_radii:
    # set the rotor radius directly
    model.model.set_val("tidal.rotor_radius", rotor_radius)

    # Rerun the model with the updated configuration
    model.run()

    # Get the outputs values of interest
    lcoe = model.model.get_val("finance_subgroup_electricity.LCOE", units="USD/kW/h")[0]
    becc = model.model.get_val("oae.carbon_credit_value", units="USD/t")[0]

    # Store the results
    lcoe_results.append(lcoe)
    becc_results.append(becc)

# Create scatter plots
plt.scatter(rotor_radii*2, lcoe_results)
plt.xlabel("Rotor Diameter (m)")
plt.ylabel("LCOE ($/kWh)")
plt.title("LCOE vs Tidal Rotor Diameter\n(TIGER 4 x 2 MW Array with All Secondary Improvements & Sine Current (0 - 4 m/s))")
plt.grid(True)
plt.show()

plt.scatter(rotor_radii*2, becc_results)
plt.xlabel("Rotor Diameter (m)")
plt.ylabel("Break Even Carbon Credit Cost ($/tCO2)")
plt.title("Break Even Carbon Credit Cost vs Tidal Rotor Diameter\n(10 ktCO2/yr Scale OAE Plant with TIGER 4 x 2 MW Array with All Secondary Improvements & Sine Current (0 - 4 m/s))")
plt.grid(True)
plt.show()

