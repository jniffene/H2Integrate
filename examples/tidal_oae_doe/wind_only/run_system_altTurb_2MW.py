from h2integrate.core.dict_utils import update_defaults
from h2integrate.core.file_utils import load_yaml, check_file_format_for_csv_generator
from h2integrate.core.h2integrate_model import H2IntegrateModel
import numpy as np
import pandas as pd
from h2integrate.postprocess.sql_timeseries_to_csv import save_case_timeseries_as_csv
from h2integrate.postprocess.sql_to_csv import convert_sql_to_csv_summary
from h2integrate.core.inputs.validation import load_tech_yaml
from h2integrate.preprocess.wind_turbine_file_tools import export_turbine_to_floris_format


# Load the tech config file
tech_config_path = "tech_config.yaml"
tech_config = load_tech_yaml(tech_config_path)

turbine_name = "COE_2.4MW"

turbine_model_fpath = export_turbine_to_floris_format(turbine_name)

# print(turbine_model_fpath)

# Load the turbine model file formatted for FLORIS
floris_options = load_yaml(turbine_model_fpath)

# Create dictionary of updated inputs for the new turbine formatted for
# the "pysam_wind_plant_performance" model
# Create dictionary of updated inputs for the new turbine formatted for
# the "floris_wind_plant_performance" model
updated_parameters = {
    "hub_height": -1,  # -1 indicates to use the hub-height in the floris_turbine_config
    "floris_turbine_config": floris_options,
}

# Update wind performance parameters with model from PySAM
tech_config["technologies"]["wind"]["model_inputs"]["performance_parameters"].update(
    updated_parameters
)

# The technology input for the updated wind turbine model
# print(tech_config["technologies"]["wind"]["model_inputs"]["performance_parameters"])

# Create the top-level config input dictionary for H2I
h2i_config = {
    # "name": "H2Integrate Config",
    # "system_summary": f"Updated hybrid plant using {turbine_name} turbine",
    "driver_config": "driver_config.yaml",
    "technology_config": tech_config,
    "plant_config": "plant_config.yaml",
}



# Create a H2Integrate model with the updated tech config
h2i = H2IntegrateModel(h2i_config)

# Run the model
h2i.setup()
h2i.run()

# model.post_process()

# Save scalar results as a one-row csv summary
summary_df = convert_sql_to_csv_summary(h2i.recorder_path)

