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
        power_coefficient (float): Coefficient of power for tidal energy device

        Be sure to update this with all of the new parameters you want to be
        able to set from the `tech_config.yaml`
        file when instantiating the model, and to add validators as needed.
        You can also add optional parameters with default values.

    """

    # ADD PERFORMANCE INPUTS HERE
    device_rating_kw: float = field(validator=gt_zero)
    num_devices: int = field(validator=gt_zero)
    rotor_radius: float = field(validator=gt_zero)

    # Optional parameter TODO how to set it as optional?
    power_coefficient: float = field(default= 0.41, validator=gt_zero)


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
            "device_rating",
            val=self.config.device_rating_kw,
            units="kW",
            desc="Rated power of the tidal energy device",
        )
        self.add_input(
            "power_coefficient",
            val=self.config.power_coefficient,
            units="unitless",
            desc="Coefficient of power of the tidal energy device",
        )

        ### Can add other outputs if you want them
        self.add_output(
            "power_curve",
            units="kW",
            shape= [2, 41],
            desc="Power curve of the tidal energy device as a function of tidal velocity",
        )
        # self.add_output(
        #     "electricity_out_kw",
        #     units = "kW",
        #     desc="Hourly output electricity (W)"
        # )
        # self.add_output(
        #     "rated_electricity_production",
        #     units = "kW",
        #     desc="Rated electricity production of system"
        # )
        # self.add_output(
        #     "total_electricity_produced",
        #     units = "kW*h",
        #     desc="Total energy produced"
        # )
        # self.add_output(
        #     "annual_electricity_produced",
        #     units = "kW*h/yr",
        #     desc="Annual electricity produced"
        # )
        # self.add_output(
        #     "capacity_factor",
        #     units = "unitless", 
        #     desc="Capacity factor of array"
        # )


    def compute(self, inputs, outputs):
        # assign resource to tidal model
        velocity_mPs = inputs["tidal_velocity"]

        # simplify inputs
        R_r = inputs["rotor_radius"][0]
        P_t_kw = inputs["device_rating"][0]
        power_coefficient = inputs["power_coefficient"][0]
        N_t = inputs["num_devices"][0]

        # calculate system capacity
        system_capacity_kw = N_t * P_t_kw

        # run the necessary calculations

        ##### Add tiger performance model calculations here #####
        
        # constants 
        cut_in_velocity = 0.5 # (m/s) cut in velocity
        cut_out_velocity = 4 # (m/s) cut out velocity
        density_seawater = 1023 # (kg/m3)

        # calculate power production
        pwr_kw = np.zeros(len(velocity_mPs))
        max_pwr_kw = np.zeros(len(velocity_mPs))
        for i in range(len(velocity_mPs)):
            max_pwr_kw[i] = system_capacity_kw
            
            if velocity_mPs[i] >= cut_in_velocity and velocity_mPs[i] <= cut_out_velocity:
                pwr_kw[i] = N_t * 0.5 * density_seawater * power_coefficient * (np.pi * R_r**2) * velocity_mPs[i]**3/1000
                
                if pwr_kw[i] > system_capacity_kw:
                    pwr_kw[i] = system_capacity_kw

        # create power curve
        step = 0.1
        pwr_curve_vel = np.arange(0,cut_out_velocity+step, step) # velocities in power curve
        pwr_curve_pwr_kW = np.zeros(len(pwr_curve_vel)) # power values in power curve
        for i in range(len(pwr_curve_vel)):
            if pwr_curve_vel[i] >= cut_in_velocity:
                pwr_curve_pwr_kW[i] = 0.5 * density_seawater * power_coefficient * (np.pi * R_r**2) * pwr_curve_vel[i]**3/1000

                if pwr_curve_pwr_kW[i] > P_t_kw:
                    pwr_curve_pwr_kW[i] = P_t_kw

        

        ### outputs from the model
        outputs["electricity_out"] = pwr_kw  # Add timeseries of the power output here
        outputs["rated_electricity_production"] = system_capacity_kw
        outputs["power_curve"] = [pwr_curve_vel, pwr_curve_pwr_kW] # TODO check if format is appropriate

        outputs["total_electricity_produced"] = outputs["electricity_out"].sum() * (self.dt / 3600)
        outputs["annual_electricity_produced"] = outputs["electricity_out"].sum() * (self.dt / 3600)
        
        # calculate capacity factor
        max_energy_kWh = sum(max_pwr_kw) * (self.dt / 3600)
        outputs["capacity_factor"] = outputs["total_electricity_produced"] / max_energy_kWh


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

    device_rating (float): Rated power of the MHK device [kW]
    num_devices (int): Number of MHK tidal devices in the system
    rotor_radius (float): Rotor radius of the tidal energy device [m]

    Advanced:
    Factors / assumptions to change for sensitivity analysis
    mod_indep_X_exp (float): Factor applied to modify the exponent applied to rotor radius to estimate blade CAPEX with constant alpha (applied after coefficients alpha, beta, and gamma are calculated)
    mod_indep_Y_exp (float): Factor applied to modify the exponent applied to rotor radius to estimate turbine CAPEX with constant beta (applied after coefficients alpha, beta, and gamma are calculated)
    mod_indep_Z_exp (float): Factor applied to modify the exponent applied to device capacity to estimate turbine CAPEX with constant gamma (applied after coefficients alpha, beta, and gamma are calculated)
    mod_dep_X_exp (float): Factor applied to modify the exponent applied to rotor radius to estimate blade CAPEX with constant alpha (applied before coefficients alpha, beta, and gamma are calculated)
    mod_dep_Y_exp (float): Factor applied to modify the exponent applied to rotor radius to estimate turbine CAPEX with constant beta (applied before coefficients alpha, beta, and gamma are calculated)
    mod_dep_Z_exp (float): Factor applied to modify the exponent applied to device capacity to estimate turbine CAPEX with constant gamma (applied before coefficients alpha, beta, and gamma are calculated)
    mod_indep_alpha (float): Factor applied to alter the calculated value of constant alpha (applied after coefficients alpha, beta, and gamma are calculated)
    mod_indep_beta (float): Factor applied to alter the calculated value of constant beta (applied after coefficients alpha, beta, and gamma are calculated)
    mod_indep_gamma (float): Factor applied to alter the calculated value of constant gamma (applied after coefficients alpha, beta, and gamma are calculated)
    mod_dep_alpha (float): Factor applied to alter the calculated value of constant alpha (applied before coefficients alpha, beta, and gamma are calculated)
    mod_dep_beta (float): Factor applied to alter the calculated value of constant beta (applied before coefficients alpha, beta, and gamma are calculated)
    mod_dep_gamma (float): Factor applied to alter the calculated value of constant gamma (applied before coefficients alpha, beta, and gamma are calculated)
    mod_indep_initial_CapEx (float): Factor applied to alter the initial CAPEX (applied after coefficients alpha, beta, and gamma are calculated)
    mod_indep_initial_OpEx (float): Factor applied to alter the initial OPEX (applied after coefficients alpha, beta, and gamma are calculated)
    mod_dep_initial_CapEx (float): Factor applied to alter the initial CAPEX (applied before coefficients alpha, beta, and gamma are calculated)
    mod_dep_initial_OpEx (float): Factor applied to alter the initial OPEX (applied before coefficients alpha, beta, and gamma are calculated)
    a_cpx (float): Coefficient applied to exponential decay curve fit for CAPEX/kW vs number of units in an array
    b_cpx (float): Coefficient applied to exponential decay curve fit for CAPEX/kW vs number of units in an array
    c_cpx (float): Coefficient applied to exponential decay curve fit for CAPEX/kW vs number of units in an array
    a_opx (float): Coefficient applied to exponential decay curve fit for OPEX/kW/yr vs number of units in an array
    b_opx (float): Coefficient applied to exponential decay curve fit for OPEX/kW/yr vs number of units in an array
    c_opx (float): Coefficient applied to exponential decay curve fit for OPEX/kW/yr vs number of units in an array
    """

    ##### ADD COST MODEL INPUTS HERE

    # if the cost year has to be a specific year update it here
    cost_year: int = field(default=2025, converter=int, validator=must_equal(2025))
    sub_sea_hubs: bool = field(default=False) 
    standard_wet_mates: bool = field(default=False) 
    piled_foundations: bool = field(default=False) 
    advanced_blade_mats: bool = field(default=False)
    cost_reduction_of_advanced_blade_mats: float = field(default = 0.5, validator=gt_zero)
    
    # main inputs
    device_rating_kw: float = field(validator=gt_zero)
    num_devices: int = field(validator=gt_zero)
    rotor_radius: float = field(validator=gt_zero)

    # factors/ assumptions to change for sensitivity analysis
    mod_indep_X_exp: float = field(default=1, validator=gt_zero)
    mod_indep_Y_exp: float = field(default=1, validator=gt_zero)
    mod_indep_Z_exp: float = field(default=1, validator=gt_zero)
    mod_dep_X_exp: float = field(default=1, validator=gt_zero)
    mod_dep_Y_exp: float = field(default=1, validator=gt_zero)
    mod_dep_Z_exp: float = field(default=1, validator=gt_zero)
    mod_indep_alpha: float = field(default=1, validator=gt_zero)
    mod_indep_beta: float = field(default=1, validator=gt_zero)
    mod_indep_gamma: float = field(default=1, validator=gt_zero)
    mod_dep_alpha: float = field(default=1, validator=gt_zero)
    mod_dep_beta: float = field(default=1, validator=gt_zero)
    mod_dep_gamma: float = field(default=1, validator=gt_zero)
    mod_indep_initial_CapEx: float = field(default=1, validator=gt_zero)
    mod_indep_initial_OpEx: float = field(default=1, validator=gt_zero)
    mod_dep_initial_CapEx: float = field(default=1, validator=gt_zero)
    mod_dep_initial_OpEx: float = field(default=1, validator=gt_zero)
    a_cpx: float = field(default = 0.4743, validator=gt_zero)
    b_cpx: float = field(default = -0.0354)
    c_cpx: float = field(default = 0.5884, validator=gt_zero)
    a_opx: float = field(default = 0.6703, validator=gt_zero)
    b_opx: float = field(default = -0.0259)
    c_opx: float = field(default = 0.3957, validator=gt_zero)


class TigerTidalCostModel(CostModelBaseClass):
    """An OpenMDAO component for the Tiger tidal cost model.
    It takes tidal device parameters as input and outputs cost data.
    """
    # This is considered an hourly timestep
    _time_step_bounds = (
        3600,
        3600,
    )  # (min, max) time step lengths (in seconds) compatible with this model

    def setup(self):
        
        self.config = TigerTidalCostConfig.from_dict(
            merge_shared_inputs(self.options["tech_config"]["model_inputs"], "cost"),
            additional_cls_name=self.__class__.__name__,
        )
        super().setup()

        ##### Add cost model inputs here #####
        # May be redundant
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
            "device_rating",
            val=self.config.device_rating_kw,
            units="kW",
            desc="Rated power of the tidal energy device",
        )

        # Main cost specific inputs
        self.add_input(
            "sub_sea_hubs",
            val= self.config.sub_sea_hubs,
            units="unitless",
            desc= "Inclusion of advancements in sub-sea hubs",
        )
        self.add_input(
            "standard_wet_mates",
            val=self.config.standard_wet_mates,
            units="unitless",
            desc="Inclusion of advancements in standardized wet mates"
        )
        self.add_input(
            "piled_foundations",
            val=self.config.piled_foundations,
            units="unitless",
            desc="Inclusion of advancements in piled foundations"
        )
        self.add_input(
            "advanced_blade_mats",
            val=self.config.advanced_blade_mats,
            units="unitless",
            desc="Inclusion of advancements in blade materials"
        )
        self.add_input(
            "cost_reduction_of_advanced_blade_mats",
            val=self.config.cost_reduction_of_advanced_blade_mats,
            units="unitless",
            desc="Reduction of blade CAPEX due to advancements in blade materials"
        )

        # Sensitivity analysis inputs
        self.add_input(
            "mod_indep_X_exp",
            val=self.config.mod_indep_X_exp,
            units="unitless",
            desc="Factor applied to modify the exponent applied to rotor radius to estimate blade CAPEX with constant alpha (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_X_exp",
            val=self.config.mod_dep_X_exp,
            units="unitless",
            desc="Factor applied to modify the exponent applied to rotor radius to estimate blade CAPEX with constant alpha (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_indep_Y_exp",
            val=self.config.mod_indep_Y_exp,
            units="unitless",
            desc="Factor applied to modify the exponent applied to rotor radius to estimate turbine CAPEX with constant beta (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_Y_exp",
            val=self.config.mod_dep_Y_exp,
            units="unitless",
            desc="Factor applied to modify the exponent applied to rotor radius to estimate turbine CAPEX with constant beta (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_indep_Z_exp",
            val=self.config.mod_indep_Z_exp,
            units="unitless",
            desc="Factor applied to modify the exponent applied to device capacity to estimate turbine CAPEX with constant gamma (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_Z_exp",
            val=self.config.mod_dep_Z_exp,
            units="unitless",
            desc="Factor applied to modify the exponent applied to device capacity to estimate turbine CAPEX with constant gamma (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_indep_alpha",
            val=self.config.mod_indep_alpha,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant alpha (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_alpha",
            val=self.config.mod_dep_alpha,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant alpha (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_indep_beta",
            val=self.config.mod_indep_beta,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant beta (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_beta",
            val=self.config.mod_dep_beta,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant beta (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_indep_gamma",
            val=self.config.mod_indep_gamma,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant gamma (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_gamma",
            val=self.config.mod_dep_gamma,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant gamma (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_indep_initial_CapEx",
            val=self.config.mod_indep_initial_CapEx,
            units="unitless",
            desc="Factor applied to alter the initial CAPEX (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_initial_CapEx",
            val=self.config.mod_dep_initial_CapEx,
            units="unitless",
            desc="Factor applied to alter the initial CAPEX (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_indep_initial_OpEx",
            val=self.config.mod_indep_initial_OpEx,
            units="unitless",
            desc="Factor applied to alter the initial OPEX (applied after coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "mod_dep_initial_OpEx",
            val=self.config.mod_dep_initial_OpEx,
            units="unitless",
            desc="Factor applied to alter the initial OPEX (applied before coefficients alpha, beta, and gamma are calculated)"
        )
        self.add_input(
            "a_cpx",
            val=self.config.a_cpx,
            units="unitless",
            desc="Coefficient applied for exponential decay curve fit for CAPEX/kW vs number of units in an array"
        )
        self.add_input(
            "b_cpx",
            val=self.config.b_cpx,
            units="unitless",
            desc="Coefficient applied for exponential decay curve fit for CAPEX/kW vs number of units in an array"
        )
        self.add_input(
            "c_cpx",
            val=self.config.c_cpx,
            units="unitless",
            desc="Coefficient applied for exponential decay curve fit for CAPEX/kW vs number of units in an array"
        )
        self.add_input(
            "a_opx",
            val=self.config.a_opx,
            units="unitless",
            desc="Coefficient applied for exponential decay curve fit for OPEX/kW/yr vs number of units in an array"
        )
        self.add_input(
            "b_opx",
            val=self.config.b_opx,
            units="unitless",
            desc="Coefficient applied for exponential decay curve fit for OPEX/kW/yr vs number of units in an array"
        )
        self.add_input(
            "c_opx",
            val=self.config.c_opx,
            units="unitless",
            desc="Coefficient applied for exponential decay curve fit for OPEX/kW/yr vs number of units in an array"
        )

        # define outputs
        # self.add_output(
        #     "CapEx",
        #     units = "$",
        #     desc="Total capital costs of system"
        # )
        # self.add_output(
        #     "OpEx",
        #     units = "$/yr",
        #     desc="Total operational costs of system"
        # )
        self.add_output(
            "CapEx_per_kW",
            units = "USD/kW",
            desc="Capital costs per kW of capacity of system"
        )
        self.add_output(
            "OpEx_per_kW",
            units = "USD/kW/year",
            desc="Operational costs per kW of capacity of system"
        )
        self.add_output(
            "alpha",
            units = "unitless",
            desc="Constant applied to rotor radius to calculate blade capital cost"
        )
        self.add_output(
            "beta",
            units = "unitless",
            desc="Constant applied to rotor radius to calculate turbine capital cost"
        )
        self.add_output(
            "gamma",
            units = "unitless",
            desc="Constant applied to device capacity to calculate turbine capital cost"
        )



    def compute(self, inputs, outputs, discrete_inputs, discrete_outputs):
        ##### Add tiger cost model calculations here #####
        # Simplify inputs
        R_r = inputs["rotor_radius"][0]
        P_t_kw = inputs["device_rating"][0]
        N_t = inputs["num_devices"][0]

        # Boolean inputs
        advBlades = inputs["advanced_blade_mats"]
        subSeaHub = inputs["sub_sea_hubs"]
        stdWetM8s = inputs["standard_wet_mates"]
        pldFndtns = inputs["piled_foundations"]
        
        # Currency Conversions
        pnd21_usd21 = 1.3757 # Avg conversion from UK pounds in 2021 to USD (https://www.exchangerates.org.uk/GBP-USD-spot-exchange-rates-history-2021.html)
        usd21_usd25 = 1.2144 # January 2021$ to January 2025$ from CPI (https://www.bls.gov/data/inflation_calculator.htm)
        
        # Original TIGER Array Costs
        N_i = 4 # Number of turbines in array
        P_tI_kw = 2000 # (kW) Rated power
        R_rI = 10 # (m) Rotor radius
        X_cpxPnd = 6660 # (2021 UK pound/kW) CAPEX from TIGER 2022
        Y_opxPnd = 200 # (2021 UK pound/kW/yr) OPEX from TIGER 2022
        X_cpxI = X_cpxPnd * pnd21_usd21 * usd21_usd25 # (2025$/kW) CAPEX from TIGER 2022 adjusted from 2021 UK pound/kW 
        Y_opxI = Y_opxPnd * pnd21_usd21 * usd21_usd25 # (2025$/kW/yr) OPEX from TIGER 2022 adjusted from 2021 UK pound/kW/yr
        CPX_i = X_cpxI * P_tI_kw * N_i * inputs["mod_dep_initial_CapEx"][0] # (2025$) CAPEX
        OPX_i = Y_opxI * P_tI_kw * N_i * inputs["mod_dep_initial_OpEx"][0] # (2025$/yr) OPEX

        # Calculate constants alpha, beta, and gamma
        w_b = 4.2/100 # change in CAPEX from change in blade material
        alpha = 2*w_b*CPX_i/(N_i*R_rI**(2.7*inputs["mod_dep_X_exp"][0])) # $/m^2.7 or $/m^2.7
        alpha = inputs["mod_dep_alpha"][0] * alpha
        w_r = 8.9/100 # change in CAPEX from change in blade length
        r1 = R_rI # initial blade length considered
        r2 = 13 # (m) new blade length considered
        beta = (w_r*CPX_i/N_i - alpha*(r2**(2.7*inputs["mod_dep_X_exp"][0]) - r1**(2.7*inputs["mod_dep_X_exp"][0])))/(r2**(inputs["mod_dep_Y_exp"][0]) - r1**(inputs["mod_dep_Y_exp"][0])) # $/m
        beta = inputs["mod_dep_beta"][0] * beta
        w_c = -32.9/100 # change in CAPEX from change in capacity
        p1 = P_tI_kw # initial capacity
        p2 = 3000 # new capacity
        gamma = ((X_cpxI*((1+w_c)*p2 - p1))/(((p2/1000)**(inputs["mod_dep_Z_exp"][0]) - (p1/1000)**(inputs["mod_dep_Z_exp"][0]))*1000)) # $/kW
        gamma = inputs["mod_dep_gamma"][0] * gamma

        # Modify the coefficient values independently for sensitivity analysis
        alpha = inputs["mod_indep_alpha"][0] * alpha
        beta = inputs["mod_indep_beta"][0] * beta
        gamma = inputs["mod_indep_gamma"][0] * gamma

        def rNcTurbCosts(R_rot,P_turb_kw, advB=False):
            # Calculate blade CAPEX
            Z_a = alpha*R_rot**(2.7*inputs["mod_indep_X_exp"][0])
            if advB: 
                Z_a = Z_a*(1 - inputs["cost_reduction_of_advanced_blade_mats"][0])
            
            # Determine CAPEX of components dependent on blade length
            Z_b = beta*R_rot**(inputs["mod_indep_Y_exp"][0])
            
            # Determine CAPEX of components dependent on turbine capacity
            Z_c = gamma*((P_turb_kw/1000)**(inputs["mod_indep_Z_exp"][0]))*1000

            Z_sum = Z_a + Z_b + Z_c
            return Z_sum
        
        ### Determine change in DEVICE CAPEX from changes in the rotor radius and turbine capacity
        # Calculate base turbine costs
        turbCPX_i = rNcTurbCosts(R_rI, P_tI_kw)
        
        # Calculate new turbine costs
        turbCPX_f = rNcTurbCosts(R_r, P_t_kw, advB=advBlades) 
        
        # Change in turbine capital costs for initial array size
        DturbCPX = N_i*(turbCPX_f - turbCPX_i)
        CPX_f4 = DturbCPX + CPX_i * inputs["mod_indep_initial_CapEx"][0]
        
        # Change in turbine operational costs for initial array size
        OPX_f4 = OPX_i * inputs["mod_indep_initial_OpEx"][0] # since altering the turbine is assumed to not change OPEX

        ### Apply other cost reductions due to other improvements
        if subSeaHub or stdWetM8s or pldFndtns:
            if subSeaHub:
                CPX_ssh = -11.1/100*X_cpxI*P_tI_kw*N_i # (2025$) BOS CAPEX reduction from subsea hub improvements
                CPX_f4 = CPX_f4 + CPX_ssh

            if stdWetM8s:
                CPX_wm = -5.8/100*X_cpxI*P_tI_kw*N_i # (2025$) BOS CAPEX reduction from wet mate improvements
                OPX_wm = -9.4/100*Y_opxI*P_tI_kw*N_i # (2025$/yr) OPEX reduction from wet mate improvements
                CPX_f4 = CPX_f4 + CPX_wm
                OPX_f4 = OPX_f4 + OPX_wm

            if pldFndtns:
                CPX_plf = -4.8/100*X_cpxI*P_tI_kw*N_i # (2025$) BOS CAPEX reduction from piled foundations improvements
                CPX_f4 = CPX_f4 + CPX_plf

        # CAPEX and OPEX per system capacity for initial 4 unit array size
        X_cpxF4 = CPX_f4/(P_t_kw*N_i)
        Y_opxF4 = OPX_f4/(P_t_kw*N_i)
        
        # Calculate CAPEX and OPEX per system capacity for new array size based on exponential decay curve fit
        X_cpxF = X_cpxF4 * (inputs["a_cpx"][0] * np.exp(N_t*inputs["b_cpx"][0]) + inputs["c_cpx"][0])
        Y_opxF = Y_opxF4 * (inputs["a_opx"][0] * np.exp(N_t*inputs["b_opx"][0]) + inputs["c_opx"][0])

        # Calculate final CAPEX and OPEX for new array size
        CPX_f = X_cpxF * P_t_kw * N_t
        OPX_f = Y_opxF * P_t_kw * N_t        

        ### outputs from the model
        outputs["CapEx"] = CPX_f
        outputs["OpEx"] = OPX_f
        outputs["CapEx_per_kW"] = X_cpxF
        outputs["OpEx_per_kW"] = Y_opxF
        outputs["alpha"] = alpha
        outputs["beta"] = beta
        outputs["gamma"] = gamma
