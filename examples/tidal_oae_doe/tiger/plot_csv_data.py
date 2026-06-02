import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Inputs
csvFileName = "outputs/100kt_50x_1-3MW_5-1-50m_Cook_Inlet_1M_rca_modRM1.csv"
relVals = ['tidal.rotor_radius (m)', 'tidal.device_rating (kW)', 'finance_subgroup_electricity.LCOE (USD/kW/h)', 'oae.carbon_credit_value (USD/t)']

# Create dataframe
df = pd.read_csv(csvFileName, usecols=relVals)
# print(df)
mat = df.to_numpy()
radii = np.unique(mat[:,0]).tolist()
# print(len(radii*2))
capacities = np.unique(mat[:,1]).tolist()
# print(capacities)

# Rearrange target results to be rows as radii and cols as capacities
lcoe_results = np.zeros((len(radii), len(capacities)))
becc_results = np.zeros((len(radii), len(capacities)))
for i in range(len(mat[:,0])):
    r = radii.index(mat[i,0])
    c = capacities.index(mat[i,1])
    lcoe_results[r,c] = mat[i,2]
    becc_results[r,c] = mat[i,3]
# print(len(lcoe_results[:,0]))

# Create scatter plots
for j in range(len(capacities)):
    plt.plot(np.multiply(radii,2), lcoe_results[:, j], label = f"{capacities[j]/1000:.1f} MW", marker='none')
plt.xlabel("Rotor Diameter (m)")
plt.ylabel("LCOE ($/kWh)")
plt.title("LCOE vs Tidal Rotor Diameter & Device Capacity\n(RM1 50 Unit Array with Cook Inlet, AK Currents)")
plt.legend()
plt.minorticks_on()
plt.grid(which='major', linestyle='-', linewidth='0.8', color='gray')
plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
plt.show()

for j in range(len(capacities)):
    plt.plot(np.multiply(radii,2), becc_results[:, j], label = f"{capacities[j]/1000:.1f} MW", marker='none')
plt.xlabel("Rotor Diameter (m)")
plt.ylabel("Break Even Carbon Credit Cost ($/tCO2)")
plt.title("Break Even Carbon Credit Cost vs Tidal Rotor Diameter & Device Capacity\n(100 ktCO2/yr Scale OAE Plant with RM1 50 Unit Array with Cook Inlet, AK Currents)")
plt.legend()
plt.minorticks_on()
plt.grid(which='major', linestyle='-', linewidth='0.8', color='gray')
plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
plt.show()