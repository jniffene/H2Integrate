import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.lines import Line2D

# Turbine set to only modRM1
turbine = "modRM1"
baseCSVfile = "../tiger/outputs/1,5MW_modRM1.csv"
sensCSVfile = "outputs/hybrid_1cap_modRM1_1,5MW_30-50-70_wind.csv"
turbineName = "50 Unit Hybrid Arrays: 1.5 MW Wind & 1.5 MW RM1"

# Define the values used on the x,y,z axes
relVals = ['tidal.rotor_radius (m)', 'tidal.device_rating (kW)', 'finance_subgroup_electricity.LCOE (USD/kW/h)', 'oae.carbon_credit_value (USD/t)', 'oae.profitability_index (unitless)']

# Define the sensitivity variable (just number of tidal devices)
sens_vars = ["tidal.num_devices"]
sensNames = ["Number of Units in Array"]
sensNickNames = [""] * len(sensNames)
for i in range(len(sens_vars)):
    sensNickNames[i] = sens_vars[i].removeprefix("tidal.")

# Obtain wind data for comparison
windCSVfile_CookInlet = "../wind_only/outputs/100kt_50x_1,5MW_wind_Cook_Inlet_1M_rca_V2.csv"
windVals = ['finance_subgroup_electricity.LCOE (USD/kW/h)', 'oae.carbon_credit_value (USD/t)', 'oae.profitability_index (unitless)']
df_wind_CI = pd.read_csv(windCSVfile_CookInlet, usecols=windVals)
r_start = 10
r_end = 30
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)
keyVals_wind_CookInlet = df_wind_CI.to_numpy()[0] * np.ones([len(rotor_radii),3])

# Create function to rearrange data for radii and capacities values for LCOE, BECC, and PI for the line plots
def rad_and_cap_for_lcoe_and_becc(csvFileName, relCols=relVals, nrows=None, skiprows=None, modVar="", modType=""):
    # Create dataframe
    df = pd.read_csv(csvFileName, usecols=relCols, nrows=nrows, skiprows=skiprows)
    # print(df)
    mat = df.to_numpy()
    radii = np.unique(mat[:,0]).tolist()
    # print(len(radii*2))
    capacities = np.unique(mat[:,1]).tolist()
    
    # # adjust the capacity step from 0.5x to 1x
    # capacities = [capacities[0], 2*capacities[0], 3*capacities[0]]
    # print(capacities)

    # Rearrange target results to be rows as radii and cols as capacities
    lcoe_results = np.zeros((len(radii), len(capacities)))
    becc_results = np.zeros((len(radii), len(capacities)))
    pi_results = np.zeros((len(radii), len(capacities)))
    for i in range(len(mat[:,0])):
        if mat[i,1] in capacities:
            r = radii.index(mat[i,0])
            c = capacities.index(mat[i,1])
            lcoe_results[r,c] = mat[i,2]
            becc_results[r,c] = mat[i,3]
            pi_results[r,c] = mat[i,4]

    caseDict = {
        "modVar": modVar,
        "modType": modType,
        "radii": radii,
        "capacities": capacities,
        "lcoe": lcoe_results,
        "becc": becc_results,
        "pi": pi_results,
        
    }
    
    return caseDict

# Define base dictionary
baseDict = rad_and_cap_for_lcoe_and_becc(baseCSVfile, modVar="Base", modType="0% Wind")

# Define interval for cases in sensitivity analysis
rp = len(baseDict["radii"])

# Define variable names and modification types for sensDict
sensModVars = [""] * len(sens_vars) * 3
for i in range(len(sens_vars)*3):
    sensModVars[i] = sensNames[0]
sensModTypes = ["30% Wind", "50% Wind", "70% Wind"]

# Define the sensitivity dictionary
sensDict = {0: baseDict}
for i in range(len(sens_vars)*3):
    if i == 0:
        rowsSkipped = None
    else:
        rowsSkipped = np.arange(1, (i)*rp+1, 1)
    sensDict[i+1] = rad_and_cap_for_lcoe_and_becc(sensCSVfile, nrows=rp, skiprows=rowsSkipped, modVar=sensModVars[i], modType=sensModTypes[i])

# Plot key results for the cases
# keyResults = ["lcoe", "becc", "pi"]
# keyFullNames = ["LCOE ($/kWh)", r"Break-Even Carbon Credit Cost (\$/tCO$_2$)", "Profitability Index"]
# keyNames = ["LCOE", "Break-Even Carbon Credit Cost\n", "Profitability Index"]

keyResults = ["pi"]
keyFullNames = ["Profitability Index"]
keyNames = ["Profitability Index"]

# Ensure colors are consistent
cmap = plt.colormaps['tab10']
num_colors = len(baseDict["capacities"])
colors = cmap(np.linspace(0, 0, num_colors))
plt.rcParams['axes.prop_cycle'] = cycler(color=colors)

# Define legend for modifications
modLegend = [
    Line2D([0], [0], color='k', lw=1.5, linestyle='-', label ='  0 Wind | 50 Tidal'),
    Line2D([0], [0], color='k', lw=1.5, linestyle='--', label ='15 Wind | 35 Tidal'),
    Line2D([0], [0], color='k', lw=1.5, linestyle='-.', label ='25 Wind | 25 Tidal'),
    Line2D([0], [0], color='k', lw=1.5, linestyle=':', label ='35 Wind | 15 Tidal'),
    # Line2D([0], [0], color='k', lw=1.5, linestyle=(0,(1,5)), label ='50 Wind |   0 Tidal'),
    # Line2D([0], [0], color='k', lw=1.5, linestyle=(0,(5,5)), label ='50 Wind Toksook Bay'),
]

# Test Plotting Function
# Function to make curves from dict's radii, capacities, and key values
def keyValRCcurve(dict, keyResult=""):
    capacities = dict["capacities"]
    radii = dict["radii"]
    results = dict[keyResult]
    modType = dict["modType"]
    if modType == "0% Wind":
        curveStyle = '-'
    elif modType == "30% Wind":
        curveStyle = '--'
    elif modType == "50% Wind":
        curveStyle = "-."
    elif modType == "70% Wind":
        curveStyle = ":"
    for j in range(len(capacities)):
        plt.plot(np.multiply(radii,2), results[:, j], label = f"{capacities[j]/1000} MW Tidal", linestyle=curveStyle)

for k in range(len(keyResults)):
    for j in range(len(sens_vars)):
        keyValRCcurve(sensDict[0], keyResult=keyResults[k])
        for i in range(3):
            keyValRCcurve(sensDict[i+1+2*j], keyResult=keyResults[k])
        plt.xlabel("Tidal Rotor Diameter (m)")
        plt.ylabel(keyFullNames[k])
        plt.title(f"{keyNames[k]} vs Tidal Rotor Diameter & Device Capacity\n({turbineName})")
        plt.legend(["  0 Wind | 50 Tidal", "15 Wind | 35 Tidal", "25 Wind | 25 Tidal", "35 Wind | 15 Tidal"], loc='center left')
        plt.minorticks_on()
        plt.grid(which='major', linestyle='-', linewidth='0.8', color='darkgray')
        plt.plot(np.multiply(rotor_radii,2), keyVals_wind_CookInlet[:,k+2], color='grey', linestyle='-')
        # plt.show()
        plt.savefig(f"{turbine}_{keyResults[k]}_hybrid_30-50-70_wind_1cap_1,5MW.png", dpi = 300, bbox_inches='tight')
        plt.close()
