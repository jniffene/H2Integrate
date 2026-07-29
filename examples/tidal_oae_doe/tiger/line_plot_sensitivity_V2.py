import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.lines import Line2D

# To simplify selecting between cases set options (tiger_all2nd, tiger_no2nd, modRM1)
turbine = "tiger_no2nd"

if turbine == "tiger_all2nd":
    # Need two CSV files: one for the base case and one for the sensitivity analyses
    baseCSVfile = "outputs/100kt_50x_2-6MW_Cook_Inlet_1M_rca_tiger_all2nd.csv"
    sensCSVfile = "outputs/senseA_100kt_50x_2-6MW_10-30m_Cook_Inlet_1M_rca_tiger_all2nd.csv"
    turbineName = "TIGER 50 Unit Array with All Secondary Improvements"
elif turbine == "tiger_no2nd":
    baseCSVfile = "outputs/100kt_50x_2-6MW_Cook_Inlet_1M_rca_tiger_no2nd.csv"
    sensCSVfile = "outputs/senseA_100kt_50x_2-6MW_10-30m_Cook_Inlet_1M_rca_tiger_no2nd.csv"
    turbineName = "TIGER 50 Unit Array with No Secondary Improvements"
elif turbine == "modRM1":
    baseCSVfile = "outputs/100kt_50x_1-3MW_Cook_Inlet_1M_rca_modRM1.csv"
    sensCSVfile = "outputs/senseA_100kt_50x_1-3MW_10-30m_Cook_Inlet_1M_rca_modRM1.csv"
    turbineName = "RM1 50 Unit Array"

# Define the values used on the x,y,z axes
relVals = ['tidal.rotor_radius (m)', 'tidal.device_rating (kW)', 'finance_subgroup_electricity.LCOE (USD/kW/h)', 'oae.carbon_credit_value (USD/t)']

# Define the sensitivity variables
sens_vars = ["tidal.power_coefficient", "tidal.mod_indep_X_exp", "tidal.mod_indep_Y_exp", "tidal.mod_indep_Z_exp", "tidal.mod_dep_X_exp", "tidal.mod_dep_Y_exp", "tidal.mod_dep_Z_exp", "tidal.mod_indep_alpha", "tidal.mod_indep_beta", "tidal.mod_indep_gamma", "tidal.mod_dep_alpha", "tidal.mod_dep_beta", "tidal.mod_dep_gamma", "tidal.mod_indep_initial_CapEx", "tidal.mod_indep_initial_OpEx", "tidal.mod_dep_initial_CapEx", "tidal.mod_dep_initial_OpEx"]

# Define shorthand names for the sensitivity values
sensNames = ["Power Coefficient", "X Exponent Independently", "Y Exponent Independently", "Z Exponent Independently", "X Exponent Dependently", "Y Exponent Dependently", "Z Exponent Dependently", "Alpha Independently", "Beta Independently", "Gamma Independently", "Alpha Dependently", "Beta Dependently", "Gamma Dependently", "Initial CAPEX Independently", "Initial OPEX Independently", "Initial CAPEX Dependently", "Initial OPEX Dependently"]
sensNickNames = [""] * len(sensNames)
for i in range(len(sens_vars)):
    sensNickNames[i] = sens_vars[i].removeprefix("tidal.")

# Create function to rearrange data for radii and capacities values for LCOE and BECC for the line plots
def rad_and_cap_for_lcoe_and_becc(csvFileName, relCols=relVals, nrows=None, skiprows=None, modVar="", modType=""):
    # Create dataframe
    df = pd.read_csv(csvFileName, usecols=relCols, nrows=nrows, skiprows=skiprows)
    # print(df)
    mat = df.to_numpy()
    radii = np.unique(mat[:,0]).tolist()
    # print(len(radii*2))
    capacities = np.unique(mat[:,1]).tolist()
    # print(capacities)

    # adjust the capacity step from 0.5x to 1x
    capacities = [capacities[0], 2*capacities[0], 3*capacities[0]]

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

# Define base dictionary
baseDict = rad_and_cap_for_lcoe_and_becc(baseCSVfile, modVar="Base", modType="0%")

# Define interval for cases in sensitivity analysis
rp = len(baseDict["radii"]) * (len(baseDict["capacities"])+2)

# Define variable names and modification types for sensDict
sensModVars = [""] * len(sens_vars) * 2
sensModTypes = [""] * len(sens_vars) * 2
for i in range(len(sens_vars)*2):
    if i % 2 == 0:
        col = int(i/2)
        sensModVars[i] = sensNames[col]
        sensModTypes[i] = "+30%"
    else: 
        col = int((i-1)/2)
        sensModVars[i] = sensNames[col]
        sensModTypes[i] = "-30%"

# Define the sensitivity dictionary
sensDict = {0: baseDict}
for i in range(len(sens_vars)*2):
    if i == 0:
        rowsSkipped = None
    else:
        rowsSkipped = np.arange(1, (i)*rp+1, 1)
    sensDict[i+1] = rad_and_cap_for_lcoe_and_becc(sensCSVfile, nrows=rp, skiprows=rowsSkipped, modVar=sensModVars[i], modType=sensModTypes[i])
# print(sensDict[34])

# Plot key results for the cases
keyResults = ["lcoe", "becc"]
keyFullNames = ["LCOE ($/kWh)", "Break Even Carbon Credit Cost ($/tCO2)"]
keyNames = ["LCOE", "Break Even Carbon Credit Cost"]

# Define consistent legend
capsLegend = [""] * len(baseDict["capacities"])
for i in range(len(capsLegend)):
    capsLegend[i] = str(round(baseDict["capacities"][i]/1000,1)) +" MW"

# Ensure colors are consistent
# custom_colors = ["#1f77b4", '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
cmap = plt.colormaps['tab10']
num_colors = len(baseDict["capacities"])
colors = cmap(np.linspace(0, 0.4, num_colors))
plt.rcParams['axes.prop_cycle'] = cycler(color=colors)

# Define legend for modifications
modLegend = [
    Line2D([0], [0], color='k', lw=1.5, linestyle='--', label ='-30%'),
    Line2D([0], [0], color='k', lw=1.5, linestyle='-', label ='0%'),
    Line2D([0], [0], color='k', lw=1.5, linestyle=':', label ='+30%'),
]

# Test Plotting Function
# Function to make curves from dict's radii, capacities, and key values
def keyValRCcurve(dict, keyResult=""):
    capacities = dict["capacities"]
    radii = dict["radii"]
    results = dict[keyResult]
    modType = dict["modType"]
    if modType == "+30%":
        curveStyle = ':'
        curveMarker = 'None'
    elif modType == "-30%":
        curveStyle = '--'
        curveMarker = 'None'
    elif modType == "0%":
        curveStyle = "-"
        curveMarker = 'None'
    
    for j in range(len(capacities)):
        plt.plot(np.multiply(radii,2), results[:, j], label = f"{capacities[j]/1000} MW", linestyle=curveStyle, marker = curveMarker)

for k in range(len(keyResults)):
    for j in range(len(sens_vars)):
        keyValRCcurve(sensDict[0], keyResult=keyResults[k])
        for i in range(2):
            keyValRCcurve(sensDict[i+1+2*j], keyResult=keyResults[k])
        plt.xlabel("Rotor Diameter (m)")
        plt.ylabel(keyFullNames[k])
        plt.title(f"{keyNames[k]} vs Tidal Rotor Diameter & Device Capacity\n{sensNames[j]} Modified by +/- 30%\n({turbineName})")
        first_legend = plt.legend(capsLegend, loc='center right', bbox_to_anchor=(1.225, 0.75))
        plt.gca().add_artist(first_legend)
        second_legend = plt.legend(handles = modLegend, loc='upper right', bbox_to_anchor=(1.225, 1.05))
        plt.gca().add_artist(second_legend)
        plt.minorticks_on()
        plt.grid(which='major', linestyle='-', linewidth='0.8', color='gray')
        plt.savefig(f"{turbine}_{keyResults[k]}_{sensNickNames[j]}_labeled.png", dpi = 300, bbox_inches='tight')
        plt.close()
