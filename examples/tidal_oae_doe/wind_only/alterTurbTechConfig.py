import os
import numpy as np

from h2integrate.core.file_utils import load_yaml
from h2integrate.core.inputs.validation import load_tech_yaml
from h2integrate.preprocess.wind_turbine_file_tools import export_turbine_to_pysam_format
from h2integrate.core.h2integrate_model import H2IntegrateModel

# Load the tech config file
tech_config_path = "tech_config.yaml"
tech_config = load_tech_yaml(tech_config_path)

turbine_name = "NREL_3MW"

turbine_model_fpath = export_turbine_to_pysam_format(turbine_name)

# print(turbine_model_fpath)

# Load the turbine model file formatted for the PySAM Windpower module
pysam_options = load_yaml(turbine_model_fpath)
# print(pysam_options)

# Create dictionary of updated inputs for the new turbine formatted for
# the "pysam_wind_plant_performance" model
updated_parameters = {
    "turbine_rating_kw": np.max(pysam_options["Turbine"].get("wind_turbine_powercurve_powerout")),
    "rotor_diameter": pysam_options["Turbine"].pop("wind_turbine_rotor_diameter"),
    "hub_height": pysam_options["Turbine"].pop("wind_turbine_hub_ht"),
    "pysam_options": pysam_options,
}

# Update wind performance parameters with model from PySAM
tech_config["technologies"]["wind"]["model_inputs"]["performance_parameters"].update(
    updated_parameters
)

# The technology input for the updated wind turbine model
print(tech_config["technologies"]["wind"]["model_inputs"]["performance_parameters"])