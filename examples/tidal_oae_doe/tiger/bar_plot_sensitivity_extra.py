import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# To simplify selecting between cases set options (tiger_all2nd, tiger_no2nd, modRM1)
turbine = "tiger_no2nd"

if turbine == "tiger_all2nd":
    # Need two CSV files: one for the base case and one for the sensitivity analyses
    baseCSVfile = "outputs/100kt_50x_2-6MW_Cook_Inlet_1M_rca_tiger_all2nd.csv"
    sensCSVfile = "outputs/senseA_100kt_50x_2-6MW_10-30m_Cook_Inlet_1M_rca_tiger_all2nd.csv"
    extraCSVfile = "outputs/senseA_Nt_100kt_50x_2-6MW_10-30m_Cook_Inlet_1M_rca_tiger_all2nd.csv"
    turbineName = "TIGER 50 Unit Array with All Secondary Improvements"
elif turbine == "tiger_no2nd":
    baseCSVfile = "outputs/100kt_50x_2-6MW_Cook_Inlet_1M_rca_tiger_no2nd.csv"
    sensCSVfile = "outputs/senseA_100kt_50x_2-6MW_10-30m_Cook_Inlet_1M_rca_tiger_no2nd.csv"
    extraCSVfile = "outputs/senseA_Nt_100kt_50x_2-6MW_10-30m_Cook_Inlet_1M_rca_tiger_no2nd.csv"
    turbineName = "TIGER 50 Unit Array with No Secondary Improvements"
elif turbine == "modRM1":
    baseCSVfile = "outputs/100kt_50x_1-3MW_Cook_Inlet_1M_rca_modRM1.csv"
    sensCSVfile = "outputs/senseA_100kt_50x_1-3MW_10-30m_Cook_Inlet_1M_rca_modRM1.csv"
    extraCSVfile = "outputs/senseA_Nt_100kt_50x_1-3MW_10-30m_Cook_Inlet_1M_rca_modRM1.csv"
    turbineName = "RM1 50 Unit Array"

# Define the values used on the x,y,z axes
relVals = ['tidal.rotor_radius (m)', 'tidal.device_rating (kW)', 'finance_subgroup_electricity.LCOE (USD/kW/h)', 'oae.carbon_credit_value (USD/t)']

# Define the sensitivity variables
sens_vars = ["tidal.power_coefficient", "tidal.mod_indep_X_exp", "tidal.mod_indep_Y_exp", "tidal.mod_indep_Z_exp", "tidal.mod_dep_X_exp", "tidal.mod_dep_Y_exp", "tidal.mod_dep_Z_exp", "tidal.mod_indep_alpha", "tidal.mod_indep_beta", "tidal.mod_indep_gamma", "tidal.mod_dep_alpha", "tidal.mod_dep_beta", "tidal.mod_dep_gamma", "tidal.mod_indep_initial_CapEx", "tidal.mod_indep_initial_OpEx", "tidal.mod_dep_initial_CapEx", "tidal.mod_dep_initial_OpEx"]
extra_var = ["tidal.num_devices"]

# Define shorthand names for the sensitivity values
sensNames = ["Power Coefficient", "X Exponent Independently", "Y Exponent Independently", "Z Exponent Independently", "X Exponent Dependently", "Y Exponent Dependently", "Z Exponent Dependently", "Alpha Independently", "Beta Independently", "Gamma Independently", "Alpha Dependently", "Beta Dependently", "Gamma Dependently", "Initial CAPEX Independently", "Initial OPEX Independently", "Initial CAPEX Dependently", "Initial OPEX Dependently"]
sensNickNames = [""] * len(sensNames)
for i in range(len(sens_vars)):
    sensNickNames[i] = sens_vars[i].removeprefix("tidal.")
extraName = ["Number of Units in Array"]

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

    # Rearrange target results to be rows as radii and cols as capacities
    lcoe_results = np.zeros((len(radii), len(capacities)))
    becc_results = np.zeros((len(radii), len(capacities)))
    for i in range(len(mat[:,0])):
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
rp = len(baseDict["radii"]) * len(baseDict["capacities"])

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

# Define variable names and modification types for extra variable
extraModVars = [""] * len(extra_var) * 2
extraModTypes = [""] * len(extra_var) * 2
for i in range(len(extra_var)*2):
    if i % 2 == 0:
        col = int(i/2)
        extraModVars[i] = extraName[col]
        extraModTypes[i] = "+30%"
    else: 
        col = int((i-1)/2)
        extraModVars[i] = extraName[col]
        extraModTypes[i] = "-30%"
for i in range(len(extra_var)*2):
    if i == 0:
        rowsSkipped = None
    else:
        rowsSkipped = np.arange(1, (i)*rp+1, 1)
    sensDict[i+1+len(sens_vars)*2] = rad_and_cap_for_lcoe_and_becc(extraCSVfile, nrows=rp, skiprows=rowsSkipped, modVar=extraModVars[i], modType=extraModTypes[i])


# Identify Results of Interest
keyResults = ["lcoe", "becc"]
keyNames = ["LCOE", "Break Even Carbon Credit Cost"]

# Determine the minimum values of LCOE and BECC and their corresponding R and C values
def keyValOpt(dict, keyResult=""):
    val_opt = dict[keyResult].min()
    val_opt = val_opt.item()
    opt_row, opt_col = np.unravel_index(dict[keyResult].argmin(), dict[keyResult].shape)
    opt_radii = dict["radii"][opt_row]
    opt_cap = dict["capacities"][opt_col]
    opt_name = "opt_" + keyResult
    dict[opt_name] = [val_opt, opt_radii, opt_cap]
    return

for i in range(len(sens_vars)*2+1+len(extra_var)*2):
    for j in range(2):
        keyValOpt(sensDict[i], keyResult=keyResults[j])
# print(np.min(sensDict[0]["lcoe"]))


# To make bar plot, calculate the relative differences between the key vals, opt R, and opt C, 
# split the datasets into the +/- 30% cases and the titles. Make 3 subplots one for each parameter

# Calculate percent differences
def optDiff(dictI, dictBase, keyResult=""):
    opt_name = "opt_" + keyResult
    opt_diff_name = "optDiff_" + keyResult
    optDiffs = np.zeros(len(dictBase[opt_name]))
    for i in range(len(dictBase[opt_name])):
        optDiffs[i] = (dictI[opt_name][i] - dictBase[opt_name][i])/ dictBase[opt_name][i]
    dictI[opt_diff_name] = optDiffs
    return

for i in range(len(sens_vars)*2+len(extra_var)*2):
    for j in range(2):
        optDiff(sensDict[i+1], sensDict[0], keyResult=keyResults[j])

# Calculate average change in a key value
def avgDiff(dictI, dictBase, keyResult=""):
    avgDiffName = "avgDiff_" + keyResult
    iVals = dictI[keyResult]
    baseVals = dictBase[keyResult]
    diffVals = iVals - baseVals
    percVals = diffVals / baseVals
    dictI[avgDiffName] = np.mean(percVals)
    return

for i in range(len(sens_vars)*2+len(extra_var)*2):
    for j in range(2):
        avgDiff(sensDict[i+1], sensDict[0], keyResult=keyResults[j])

print(sensDict[34])
# print(sensDict[0])

# Create one plot for LCOE alone first
# Obtain the avgDiff percentages for the different cases separated by the +/- 30% options
def sensBarPlotPlusMinusSplit(keyResult):
    plus30_valDiff = np.zeros(len(sens_vars)+len(extra_var))
    minus30_valDiff = np.zeros(len(sens_vars)+len(extra_var))
    p = 0
    m = 0
    avgDiffName = "avgDiff_" + keyResult

    for i in range(len(sens_vars)*2+len(extra_var)*2):
        if sensDict[i+1]["modType"] == '+30%':
            plus30_valDiff[p] = sensDict[i+1][avgDiffName] * 100
            p = p+1
        elif sensDict[i+1]["modType"] == '-30%':
            minus30_valDiff[m] = sensDict[i+1][avgDiffName] * 100
            m = m+1
    return plus30_valDiff, minus30_valDiff

plus30_lcoeDiff, minus30_lcoeDiff = sensBarPlotPlusMinusSplit(keyResults[0])


varSymbols = [r"$c_{\text{p}}$", r"$x_{\text{indep}}$", r"$y_{\text{indep}}$", r"$z_{\text{indep}}$", r"$x_{\text{dep}}$", r"$y_{\text{dep}}$", r"$z_{\text{dep}}$", r"$ \alpha _{\text{indep}}$", r"$ \beta _{\text{indep}}$", r"$ \gamma _{\text{indep}}$", r"$ \alpha _{\text{dep}}$", r"$ \beta _{\text{dep}}$", r"$ \gamma _{\text{dep}}$", r"$C_{\text{indep}}$", r"$O_{\text{indep}}$", r"$C_{\text{dep}}$", r"$O_{\text{dep}}$", r"$N_{\text{t}}$"]
# varSymbols.reverse()
# print(plus30_lcoeDiff)
# print(varSymbols)



# # Plot the LCOE changes
# X = np.arange(len(sensNames))
# fig, ax = plt.subplots()
# ax.barh(X, plus30_lcoeDiff)
# ax.barh(X, minus30_lcoeDiff)
# ax.invert_yaxis()
# ax.legend(["Parameter change by +30%", "Parameter change by -30%"])
# ax.set_yticks(X, labels=varSymbols)
# ax.plot([30,30],[-1, len(sensNames)], "k--")
# ax.plot([-30,-30],[-1, len(sensNames)], "k--")
# ax.set_xlabel("Change of LCOE [% to reference]")
# ax.set_title(f"Average Change in LCOE for {turbineName}")
# plt.show()

for k in range(len(keyResults)-1):
    plus30_valDiff, minus30_valDiff = sensBarPlotPlusMinusSplit(keyResults[k])
    X = np.arange(len(sensNames)+len(extraName))
    fig, ax = plt.subplots(figsize=(7.8,4.8))
    ax.barh(X, plus30_valDiff)
    ax.barh(X, minus30_valDiff)
    ax.invert_yaxis()
    ax.legend(["Parameter change by +30%", "Parameter change by -30%"], loc="center right")
    ax.set_yticks(X, labels=varSymbols)
    ax.plot([30,30],[-1, len(sensNames + extraName)], "k--")
    ax.plot([-30,-30],[-1, len(sensNames + extraName)], "k--")
    ax.set_xlabel(f"Change of {keyNames[k]} [% to reference]")
    ax.set_title(f"Average Change in {keyNames[k]} for {turbineName}")
    plt.savefig(f"{turbine}_{keyResults[k]}_sensBarPlot.png", dpi = 300, bbox_inches='tight')
    plt.close()