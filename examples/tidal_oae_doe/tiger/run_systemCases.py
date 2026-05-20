from h2integrate.tools.run_cases import modify_tech_config, load_tech_config_cases
from h2integrate.core.h2integrate_model import H2IntegrateModel
import pandas as pd
import numpy as np

# Cases to Investigate
# Vary the rotor radius and determine the LCOE and Breakeven Carbon Credit Cost
r_start = 10
r_end = 11
r_step = 1
rotor_radii = np.arange(r_start, r_end+r_step, r_step)
total_tests = len(rotor_radii)

# Build CSV file for cases (only if it actually works)
# Make header
max_hierarchy_level = 5
index_list = []
for i in range(max_hierarchy_level):
    index_list.append(f"Index {i}")
filled_list = ["Type"]
case_list = []
for i in range(total_tests):
    case_list.append(f"Case {i+1}")
header = index_list + filled_list + case_list
# Define relevant variables
var1 = ["technologies", "tidal", "model_inputs", "shared_parameters", "rotor_radius", "float"]
for i in range(len(rotor_radii)):
    var1.append(str(rotor_radii[i]))
# Build CSV file
headerDF = pd.DataFrame(header)
headerDF = headerDF.transpose()
headerDF.to_csv('input_casesTest.csv', index=False, header=False)
var1DF = pd.DataFrame(var1)
var1DF = var1DF.transpose()
var1DF.to_csv('input_casesTest.csv', mode='a', index=False, header=False)

# Create H2I model
model = H2IntegrateModel("input_config.yaml")

# Load cases
cases = load_tech_config_cases("input_casesTest.csv")

# Run the model for different cases
counter = 1
for casename in case_list:
    # Indicate which simulation is active
    print(f"Running simulation {counter} of {total_tests} total")
    counter = counter + 1
    
    case = cases[casename]
    model = modify_tech_config(model, case)
    model.run()
    model.post_process()