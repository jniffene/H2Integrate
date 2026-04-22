from attrs import field, define

from h2integrate.core.utilities import BaseConfig, merge_shared_inputs
from h2integrate.core.validators import gt_zero, must_equal
from h2integrate.core.model_baseclasses import (
    CostModelBaseClass,
    CostModelBaseConfig,
    PerformanceModelBaseClass,
)
import numpy as np


@define(kw_only=True)
class TigerTidalPerformanceConfig(BaseConfig):
    """
    Configuration class for TigerTidalPerformanceModel.

    Inputs you want the users to be able to set from the `tech_config.yaml`

    Args:
        device_rating_kw (float): Rated power of the MHK device [kW]
        num_devices (int): Number of MHK tidal devices in the system
        rotor_radius (float): Rotor radius of the tidal energy device [m]

        Be sure to update this with all of the new parameters you want to be
        able to set from the `tech_config.yaml`
        file when instantiating the model, and to add validators as needed.
        You can also add optional parameters with default values.

    """

    # ADD PERFORMANCE INPUTS HERE
    device_rating_kw: float = field(validator=gt_zero)
    num_devices: int = field(validator=gt_zero)
    rotor_radius: float = field(validator=gt_zero)

### Tiger tidal performance model
class TigerTidalPerformanceModel(PerformanceModelBaseClass):
    """An OpenMDAO component for the Tiger tidal performance model.
    It takes tidal parameters as input and outputs power generation data.
    """

    # This is considered an hourly timestep
    _time_step_bounds = (
        3600,
        3600,
    )  # (min, max) time step lengths (in seconds) compatible with this model

    def initialize(self):
        super().initialize()
        self.commodity = "electricity"
        self.commodity_rate_units = "kW"
        self.commodity_amount_units = "kW*h"

    def setup(self):
        super().setup()
        self.config = TigerTidalPerformanceConfig.from_dict(
            merge_shared_inputs(self.options["tech_config"]["model_inputs"], "performance"),
            additional_cls_name=self.__class__.__name__,
        )

        #### Tidal Resource ####
        self.add_input(
            "tidal_velocity",
            val=0.0,
            shape=self.n_timesteps,
            units="m/s",
        )

        #### Tidal Device Parameters ####
        # rotor radius, single turbine capacity, number of turbines,
        self.add_input(
            "rotor_radius",
            val=self.config.rotor_radius,
            units="m",
            desc="Rotor radius of the tidal energy device",
        )

        self.add_input(
            "num_devices",
            val=self.config.num_devices,
            units="unitless",
            desc="Number of tidal devices in the system",
        )

        self.add_input(
            "device_rating_kw",
            val=self.config.device_rating_kw,
            units="kW",
            desc="Rated power of the tidal energy device",
        )

        ### Can add other outputs if you want them
        self.add_output(
            "power_curve",
            units="kW",
            desc="Power curve of the tidal energy device as a function of tidal velocity",
        )

        self.add_output(
            "electricity_out_w",
            units = "W",
            desc="Hourly output electricity (W)"
        )


    def compute(self, inputs, outputs):
        # assign resource to tidal model
        velocity_mPs = inputs["tidal_velocity"]

        # simplify rotor radius and device capacity inputs
        R_r = inputs["rotor_radius"][0]
        P_t = inputs["device_rating_kw"][0]

        # calculate system capacity
        system_capacity_kw = inputs["num_devices"][0] * inputs["device_rating_kw"][0]

        # run the necessary calculations

        ##### Add tiger performance model calculations here #####
        
        # constants 
        cut_in_velocity = 0.5 # (m/s) cut in velocity
        cut_out_velocity = 4 # (m/s) cut out velocity
        C_perf = 0.41 # coefficient of performance
        density_seawater = 1023 # (kg/m3)

        # calculate power production
        pwr_w = np.zeros(len(velocity_mPs))

        for i in range(len(velocity_mPs)):
            if velocity_mPs[i] >= cut_in_velocity and velocity_mPs[i] <= cut_out_velocity:
                pwr_w[i] = 0.5 * density_seawater * C_perf * (np.pi * R_r**2) * velocity_mPs[i]**3
                
                if pwr_w[i] / 1000 > P_t:
                    pwr_w[i] = P_t * 1000

        ### outputs from the model
        outputs["electricity_out_w"] = pwr_w  # Add timeseries of the power output here
        outputs["rated_electricity_production"] = system_capacity_kw

        outputs["total_electricity_produced"] = outputs["electricity_out_w"].sum() * (self.dt / 3600)
        outputs["annual_electricity_produced"] = 0

        outputs["capacity_factor"] = (
            self.system_model.Outputs.capacity_factor / 100
        )  # divide by 100 to make it unitless


@define(kw_only=True)
class TigerTidalCostConfig(CostModelBaseConfig):
    """ 

    Configuration class for TigerTidalCostModel.

    cost_year (int): Cost year in USD (2025)
    sub_sea_hubs (bool): If true applies cost reductions from improved designs and supply chains of subsea hubs
    standard_wet_mates (bool): If true applies cost reductions from standardized designs for wet mate connectors used for tidal turbines
    piled_foundations (bool): If true applies cost reductions from piled foundations becoming more standard vs monopile moorings
    advanced_blade_mats (bool): If true applies cost reductions from using advanced blade materials
    cost_reduction_of_advanced_blade_mats (float): Reduction in blade capital cost if advanced blade materials are considered
    
    """

    ##### ADD COST MODEL INPUTS HERE

    # if the cost year has to be a specific year update it here
    cost_year: int = field(default=2025, converter=int, validator=must_equal(2025))
    sub_sea_hubs: bool = field(default=False) 
    standard_wet_mates: bool = field(default=False) 
    piled_foundations: bool = field(default=False) 
    advanced_blade_mats: bool = field(default=False)
    cost_reduction_of_advanced_blade_mats: float = field(default = 0.5, validator=gt_zero)


class TigerTidalCostModel(CostModelBaseClass):
    """An OpenMDAO component for the Tiger tidal cost model.
    It takes tidal device parameters as input and outputs cost data.
    """

    def setup(self):
        super().setup()
        self.config = TigerTidalCostConfig.from_dict(
            merge_shared_inputs(self.options["tech_config"]["model_inputs"], "cost"),
            additional_cls_name=self.__class__.__name__,
        )

        ##### Add cost model inputs here #####

    def compute(self, inputs, outputs):
        ##### Add tiger cost model calculations here #####

        ### outputs from the model
        outputs["CapEx"] = 0
        outputs["OpEx"] = 0
