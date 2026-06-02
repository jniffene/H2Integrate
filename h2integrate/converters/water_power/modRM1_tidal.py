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
class ModRM1TidalPerformanceConfig(BaseConfig):
    """
    Configuration class for ModRM1TidalPerformanceModel.

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
    power_coefficient: float = field(default= 0.3, validator=gt_zero)


### Modified RM1 tidal performance model
class ModRM1TidalPerformanceModel(PerformanceModelBaseClass):
    """An OpenMDAO component for the modified RM1 tidal performance model.
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
        self.config = ModRM1TidalPerformanceConfig.from_dict(
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
            shape= [2, 34], # TODO adjust shape
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

        ##### Add modified RM1 performance model calculations here #####
        
        # constants 
        cut_in_velocity = 0.6 # (m/s) cut in velocity
        cut_out_velocity = 3.3 # (m/s) cut out velocity
        density_seawater = 1023 # (kg/m3)

        # calculate power production
        pwr_kw = np.zeros(len(velocity_mPs))
        max_pwr_kw = np.zeros(len(velocity_mPs))
        for i in range(len(velocity_mPs)):
            max_pwr_kw[i] = system_capacity_kw
            
            if velocity_mPs[i] >= cut_in_velocity and velocity_mPs[i] <= cut_out_velocity:
                pwr_kw[i] = N_t * 0.5 * density_seawater * power_coefficient * (2*np.pi * R_r**2) * velocity_mPs[i]**3/1000
                
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
        outputs["power_curve"] = [pwr_curve_vel, pwr_curve_pwr_kW]

        outputs["total_electricity_produced"] = outputs["electricity_out"].sum() * (self.dt / 3600)
        outputs["annual_electricity_produced"] = outputs["electricity_out"].sum() * (self.dt / 3600)
        
        # calculate capacity factor
        max_energy_kWh = sum(max_pwr_kw) * (self.dt / 3600)
        outputs["capacity_factor"] = outputs["total_electricity_produced"] / max_energy_kWh


@define(kw_only=True)
class ModRM1TidalCostConfig(CostModelBaseConfig):
    """ 

    Configuration class for ModRM1TidalCostModel.

    cost_year (int): Cost year in USD (2025)

    device_rating (float): Rated power of the MHK device [kW]
    num_devices (int): Number of MHK tidal devices in the system
    rotor_radius (float): Rotor radius of the tidal energy device [m]

    Advanced:
    Factors / assumptions to change for sensitivity analysis
    alpha_exp (float): Exponent applied to rotor radius to estimate blade CAPEX with constant alpha
    beta_exp (float): Exponent applied to rotor radius to estimate turbine CAPEX with constant beta
    gamma_exp (float): Exponent applied to device capacity to estimate turbine CAPEX with constant gamma
    mod_alpha (float): Factor applied to alter the calculated value of constant alpha
    mod_beta (float): Factor applied to alter the calculated value of constant beta
    mod_gamma (float): Factor applied to alter the calculated value of constant gamma
    """

    ##### ADD COST MODEL INPUTS HERE

    # if the cost year has to be a specific year update it here
    cost_year: int = field(default=2025, converter=int, validator=must_equal(2025))
    
    # main inputs
    device_rating_kw: float = field(validator=gt_zero)
    num_devices: int = field(validator=gt_zero)
    rotor_radius: float = field(validator=gt_zero)

    # factors/ assumptions to change for sensitivity analysis
    alpha_exp: float = field(default=2.7, validator=gt_zero)
    beta_exp: float = field(default=1, validator=gt_zero)
    gamma_exp: float = field(default=1, validator=gt_zero)
    mod_alpha: float = field(default=1, validator=gt_zero)
    mod_beta: float = field(default=1, validator=gt_zero)
    mod_gamma: float = field(default=1, validator=gt_zero)

class ModRM1TidalCostModel(CostModelBaseClass):
    """An OpenMDAO component for the modified RM1 tidal cost model.
    It takes tidal device parameters as input and outputs cost data.
    """
    # This is considered an hourly timestep
    _time_step_bounds = (
        3600,
        3600,
    )  # (min, max) time step lengths (in seconds) compatible with this model

    def setup(self):
        
        self.config = ModRM1TidalCostConfig.from_dict(
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

        # Sensitivity analysis inputs
        self.add_input(
            "alpha_exp",
            val=self.config.alpha_exp,
            units="unitless",
            desc="Exponent applied to rotor radius to estimate blade CAPEX with constant alpha"
        )
        self.add_input(
            "beta_exp",
            val=self.config.beta_exp,
            units="unitless",
            desc="Exponent applied to rotor radius to estimate turbine CAPEX with constant beta"
        )
        self.add_input(
            "gamma_exp",
            val=self.config.gamma_exp,
            units="unitless",
            desc="Exponent applied to device capacity to estimate turbine CAPEX with constant gamma"
        )
        self.add_input(
            "mod_alpha",
            val=self.config.mod_alpha,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant alpha"
        )
        self.add_input(
            "mod_beta",
            val=self.config.mod_beta,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant beta"
        )
        self.add_input(
            "mod_gamma",
            val=self.config.mod_gamma,
            units="unitless",
            desc="Factor applied to alter the calculated value of constant gamma"
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
        ##### Add modified RM1 cost model calculations here #####
        # Simplify inputs
        R_r = inputs["rotor_radius"][0]
        P_t_kw = inputs["device_rating"][0]
        N_t = inputs["num_devices"][0]

        alpha_exp = inputs["alpha_exp"][0]
        beta_exp = inputs["beta_exp"][0]
        gamma_exp = inputs["gamma_exp"][0]
        
        # Currency Conversions
        usd14_usd25 = 1.3581 # January 2014$ to January 2025$ from CPI (https://www.bls.gov/data/inflation_calculator.htm)
        
        # Original Modified RM1 Array Costs
        N_i = 100 # Number of turbines in array
        P_tI_kw = 1115 # (kW) Rated power
        R_rI = 10 # (m) Rotor radius
        X_cpx2014 = 3170 # (2014$/kW) for a 100 unit array
        Y_opx2014 = 86 # (2014$/kW/yr) for a 100 unit array
        X_cpxI = X_cpx2014 * usd14_usd25 # (2025$/kW) initial CAPEX of 100 unit array
        Y_opxI = Y_opx2014 * usd14_usd25 # (2025$/kW/yr) initial OPEX of 100 unit array
        CPX_i = X_cpxI * P_tI_kw * N_i # (2025$) CAPEX
        OPX_i = Y_opxI * P_tI_kw * N_i # (2025$/yr) OPEX

        # Costs per kW from RM1
        x_blades = 14 * usd14_usd25 # (2025$/kW) blade costs from Table 3-9 of RM Report
        x_rotor_core = 2 * usd14_usd25 # (2025$/kW) remaining rotor costs after subtracting blade costs from RM1-CBS spreadsheet for 100 unit array
        x_pitch_system = 12 * usd14_usd25 # (2025$/kW) pitch system costs from Table 3-9 of RM report
        x_low_speed_shaft = 3 * usd14_usd25 # (2025$/kW) low speed shaft costs from Table 3-9 of RM Report
        x_gearbox = 251 * usd14_usd25 # (2025$/kW) gearbox and driveshaft costs from RM1-CBS spreadsheet for 100 unit array
        x_generator = 172 * usd14_usd25 # (2025$/kW) generator costs from RM1-CBS spreadsheet for 100 unit array
        x_pto_frame = 69 * usd14_usd25 # (2025$/kW) PTO mounting costs from RM1-CBS spreadsheet for 100 unit array
        x_bearing = 239 * usd14_usd25 # (2025$/kW) bearings and linear guides costs from RM1-CBS spreadsheet for 100 unit array
        x_hydraulic = 29 * usd14_usd25 # (2025$/kW) hydraulic system costs (used as stand-in for cooling system) from RM1-CBS spreadsheet for 100 unit array
        x_cms = 170 * usd14_usd25 # (2025$/kW) control system costs (used as stand-in for condition monitoring system) from RM1-CBS spreadsheet for 100 unit array

        # Estimate constants for alpha, beta, and gamma
        alpha = x_blades * P_tI_kw / (R_rI**alpha_exp)
        x_beta = x_rotor_core + x_pitch_system + x_low_speed_shaft
        beta = x_beta * P_tI_kw / (R_rI**beta_exp)
        x_gamma = x_gearbox + x_generator + x_pto_frame + x_bearing + x_hydraulic + x_cms
        gamma = x_gamma * P_tI_kw / (P_tI_kw ** gamma_exp) # place holder to later modify exponents

        # Modify the coefficient values for sensitivity analysis
        alpha = inputs["mod_alpha"][0] * alpha
        beta = inputs["mod_beta"][0] * beta
        gamma = inputs["mod_gamma"][0] * gamma

        def rNcTurbCosts(R_rot,P_turb_kw):
            # Calculate blade CAPEX
            Z_a = alpha*R_rot**alpha_exp            
            # Determine CAPEX of components dependent on blade length
            Z_b = beta*R_rot**beta_exp
            
            # Determine CAPEX of components dependent on turbine capacity
            Z_c = gamma*(P_turb_kw/1000**gamma_exp)*1000

            Z_sum = Z_a + Z_b + Z_c
            return Z_sum
        
        ### Determine change in DEVICE CAPEX from changes in the rotor radius and turbine capacity
        # Calculate base turbine costs
        turbCPX_i = rNcTurbCosts(R_rI, P_tI_kw)
        
        # Calculate new turbine costs
        turbCPX_f = rNcTurbCosts(R_r, P_t_kw) 
        
        # Change in turbine capital costs for initial array size
        DturbCPX = N_i*(turbCPX_f - turbCPX_i)
        CPX_f100 = DturbCPX + CPX_i
        
        # Change in turbine operational costs for initial array size
        OPX_f100 = OPX_i # since altering the turbine is assumed to not change OPEX

        # CAPEX and OPEX per system capacity for initial 4 unit array size
        X_cpxF100 = CPX_f100/(P_t_kw*N_i)
        Y_opxF100 = OPX_f100/(P_t_kw*N_i)

        # Coefficients from power curve fit for the 100 unit array 
        # CAPEX coefficients 
        a_cpx = 1.6204 
        b_cpx = -0.0522
        c_cpx = 0.9912

        # OPEX coefficients
        a_opx = 4.1585
        b_opx = -0.0508
        c_opx = 0.9741

        # Calculate CAPEX and OPEX per system capacity for new array size based on exponential decay curve fit
        X_cpxF = X_cpxF100*(a_cpx * np.exp(N_t*b_cpx) + c_cpx)
        Y_opxF = Y_opxF100*(a_opx * np.exp(N_t*b_opx) + c_opx)

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
