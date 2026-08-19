from h2integrate.core.h2integrate_model import H2IntegrateModel

# Build the model from the top-level config file
h2i_model = H2IntegrateModel("input_config.yaml")

# Write XDSM output to connections_xdsm.pdf
h2i_model.create_xdsm(outfile="connections_xdsm")