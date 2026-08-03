from h2integrate.core.dict_utils import update_defaults
from h2integrate.core.file_utils import load_yaml, check_file_format_for_csv_generator
from h2integrate.core.h2integrate_model import H2IntegrateModel
import numpy as np
import pandas as pd
from h2integrate.postprocess.sql_timeseries_to_csv import save_case_timeseries_as_csv
from h2integrate.postprocess.sql_to_csv import convert_sql_to_csv_summary


model = H2IntegrateModel("input_config.yaml")
model.setup()

# model.model.set_val("oae.max_ed_system_flow_rate", 0.324, units = "m**3/s")
# model.model.set_val("oae.max_ed_system_power", 35*10**6, units = "W")
# model.model.set_val("tidal.num_devices", 50, units="unitless")

# hours = 24*365
# # v = 4 * np.ones(hours)
# # model.prob.set_val("tidal.tidal_velocity", v, units="m/s")


# # vel_t = np.zeros(hours)
# time = np.zeros(hours)

# # Amp = (4)/2
# # # periodT = 24
# # periodT = 12
# # # movUp = Amp
# # movUp = 0
# # # movSide = -1*np.pi/2
# # movSide = 0
# # for i in range(len(vel_t)):
# #     # vel_t[i] = Amp*math.sin(2*np.pi/periodT*(i+1) + movSide) + movUp
# #     vel_t[i] = abs(Amp*math.sin(2*np.pi/periodT*(i+1) + movSide) + movUp)
# #     time[i] = i+1

# df = pd.read_csv('AK_cook_inlet_tidal_resource_2005.csv', usecols=['Mean Current Speed (m/s)'])
# vel_t = df.values.tolist()
# for i in range(len(vel_t)):
#     time[i] = i+1

# model.prob.set_val("tidal.tidal_velocity", vel_t, units="m/s")
model.run()
# model.post_process()

# Save scalar results as a one-row csv summary
summary_df = convert_sql_to_csv_summary(model.recorder_path)

# # Save all timeseries data to a csv file
# timeseries_data = save_case_timeseries_as_csv(model.recorder_path)

# Create an H2I model

# # Load the configurations and run the model
# config = load_yaml("input_config.yaml")

# driver_config = load_yaml(config["driver_config"])
# csv_config_fn = driver_config["driver"]["design_of_experiments"]["filename"]

# try:
#     model = H2IntegrateModel(config)
#     # Run the model
#     model.run()
# except UserWarning as e:
#     print(f"Caught UserWarning: {e}")

# """
# To fix the issue with the UserWarning, we'll take the following steps to try and fix
# the bug in our CSV file:
# 1. Run the `check_file_format_for_csv_generator` method mentioned in the UserWarning
#   and create a new csv file that is hopefully free of errors
# 2. Make a new driver config file that has "filename" point to the new csv file created
#   in Step 1.
# 3. Make a new top-level config file that points to the updated driver config file
#   created in Step 2.
# """

# # # Step 1
# new_csv_filename = check_file_format_for_csv_generator(
#     csv_config_fn,
#     driver_config,
#     check_only=False,
#     overwrite_file=False,
# )

# # Step 2
# updated_driver = update_defaults(
#     driver_config["driver"],
#     "filename",
#     new_csv_filename.name,
# )
# driver_config["driver"].update(updated_driver)
# print(f"New DOE driver CSV file: {new_csv_filename}")

# # Step 3
# config["driver_config"] = driver_config

# # Rerun the model
# model = H2IntegrateModel(config)
# model.run()

# # Saves results to a CSV in outputs folder
# model.post_process(summarize_sql=True)
