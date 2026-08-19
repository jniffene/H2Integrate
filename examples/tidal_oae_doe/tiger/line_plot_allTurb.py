import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.lines import Line2D

# To simplify selecting between cases set options (tiger_all2nd, tiger_no2nd, modRM1)
turbine = ["tiger_all2nd", "tiger_no2nd", "modRM1"]
baseCSVfile = ["../tiger/outputs/100kt_50x_2-6MW_Cook_Inlet_1M_rca_tiger_all2nd.csv", "../tiger/outputs/100kt_50x_2-6MW_Cook_Inlet_1M_rca_tiger_no2nd.csv", "../tiger/outputs/100kt_50x_1-3MW_Cook_Inlet_1M_rca_modRM1.csv"]
turbineName = ["2.0 MW TIGER (All Secondary Improvements)", "2.0 MW TIGER (No Secondary Improvements)", "1.1 MW RM1"]

# Define the values used on the x,y,z axes
relVals = ['tidal.rotor_radius (m)', 'tidal.device_rating (kW)', 'finance_subgroup_electricity.LCOE (USD/kW/h)', 'oae.carbon_credit_value (USD/t)']

# Create function to rearrange data for radii and capacities values for LCOE and BECC for the line plots
def rad_and_cap_for_lcoe_and_becc(csvFileName, relCols=relVals, nrows=None, skiprows=None, modVar="", modType=""):
    # Create dataframe
    df = pd.read_csv(csvFileName, usecols=relCols, nrows=nrows, skiprows=skiprows)
    # print(df)
    mat = df.to_numpy()
    radii = np.unique(mat[:,0]).tolist()
    # print(len(radii*2))
    capacities = np.unique(mat[:,1]).tolist()
    
    # adjust the capacity step from 0.5x to 1x
    capacities = [capacities[0], 2*capacities[0], 3*capacities[0]]
    # print(capacities)

    # Rearrange target results to be rows as radii and cols as capacities
    lcoe_results = np.zeros((len(radii), len(capacities)))
    becc_results = np.zeros((len(radii), len(capacities)))
    for i in range(len(mat[:,0])):
        if mat[i,1] in capacities:
            r = radii.index(mat[i,0])
            c = capacities.index(mat[i,1])
            lcoe_results[r,c] = mat[i,2]
            becc_results[r,c] = mat[i,3]

    caseDict = {
        "modVar": modVar,
        "modType": modType,
        "radii": radii,
        "capacities": capacities,
        "lcoe": lcoe_results,
        "becc": becc_results,
        
    }
    
    return caseDict

# Define overall dictionary
for i in range(len(turbine)):
    if i == 0:
        baseDict = rad_and_cap_for_lcoe_and_becc(baseCSVfile[i], modVar="Turbine", modType=turbineName[i])
        totDict = {0: baseDict}
    else:
        totDict[i] = rad_and_cap_for_lcoe_and_becc(baseCSVfile[i], modVar="Turbine", modType=turbineName[i])

print(totDict)

# Plot key results for the cases
keyResults = ["lcoe", "becc"]
keyFullNames = ["LCOE ($/kWh)", r"Break-Even Carbon Credit Cost (\$/tCO$_2$)"]
keyNames = ["LCOE", "Break-Even Carbon Credit Cost"]

# Define consistent legend
capsLegend = [""] * len(baseDict["capacities"])
for i in range(len(capsLegend)):
    capsLegend[i] = str(i+1) +"x Capacity"
print(capsLegend)

# Ensure colors are consistent
cmap = plt.colormaps['tab10']
num_colors = len(baseDict["capacities"])
colors = cmap(np.linspace(0, 0.4, num_colors))
plt.rcParams['axes.prop_cycle'] = cycler(color=colors)

# Define legend for modifications
modLegend = [
    Line2D([0], [0], color='k', lw=1.5, linestyle='-', label = turbineName[0]),
    Line2D([0], [0], color='k', lw=1.5, linestyle='--', label = turbineName[1]),
    Line2D([0], [0], color='k', lw=1.5, linestyle='-.', label = turbineName[2]),
]

# Test Plotting Function
# Function to make curves from dict's radii, capacities, and key values
def keyValRCcurve(dict, keyResult=""):
    capacities = dict["capacities"]
    radii = dict["radii"]
    results = dict[keyResult]
    modType = dict["modType"]
    if modType == turbineName[0]:
        curveStyle = '-'
    elif modType == turbineName[1]:
        curveStyle = '--'
    elif modType == turbineName[2]:
        curveStyle = "-."
    for j in range(len(capacities)):
        plt.plot(np.multiply(radii,2), results[:, j], label = f"{j+1}x Capacity", linestyle=curveStyle)

for k in range(len(keyResults)):
    for j in range(3):
        keyValRCcurve(totDict[j], keyResult=keyResults[k])
    plt.xlabel("Tidal Rotor Diameter (m)")
    plt.ylabel(keyFullNames[k])
    plt.title(f"{keyNames[k]} vs Tidal Rotor Diameter & Device Capacity\n(50 Unit Arrays of Each Turbine)")
    first_legend = plt.legend(capsLegend, loc='center right', bbox_to_anchor=(0.265, -0.225))
    plt.gca().add_artist(first_legend)
    second_legend = plt.legend(handles = modLegend, loc='center left', bbox_to_anchor=(0.265, -0.225))
    plt.gca().add_artist(second_legend)
    plt.minorticks_on()
    plt.grid(which='major', linestyle='-', linewidth='0.8', color='darkgray')
    # plt.show()
    plt.savefig(f"allTurb_{keyResults[k]}_baseline.png", dpi = 300, bbox_inches='tight')
    plt.close()