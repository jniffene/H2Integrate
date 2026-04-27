import numpy as np
import pytest
import openmdao.api as om
from pytest import fixture

from h2integrate import EXAMPLE_DIR
from h2integrate.resource.river import RiverResource
from h2integrate.converters.water_power.tiger_tidal import (
    TigerTidalPerformanceModel, TigerTidalCostModel
)


@fixture
def plant_config():
    plant_config = {
        "plant": {
            "plant_life": 30,
            "simulation": {
                "n_timesteps": 8760,
                "dt": 3600,
            },
        },
    }
    return plant_config

# To test performance model on its own
@fixture
def performance_tech_config():
    performance_tech_config = {
        "model_inputs": {
            "performance_parameters": {
                "device_rating_kw": 2000,
                "num_devices": 4,
                "rotor_radius": 10,
            }
        }
    }
    return performance_tech_config


@fixture
def cost_tech_config():
    cost_tech_config = {
        "model_inputs": {
            "cost_parameters": {
                "device_rating_kw": 2000,
                "num_devices": 4,
                "rotor_radius": 10,
                "sub_sea_hubs":        False,
                "standard_wet_mates":  False,
                "piled_foundations":   False,
                "advanced_blade_mats": False,
            }
        }
    }
    return cost_tech_config


# May be unnecessary
# @fixture
# def tech_config():
#     model_inputs = { # TODO add inputs from performance model config
#         "shared_parameters": {
#             # TODO add the shared parameters
#         },
#         "performance_parameters":{
#             # TODO
#         },
#         "cost_parameters":{
#             # TODO
#         },
#         "plant_capacity_mw": 10.0,
#         "water_density": 1023,
#         "acceleration_gravity": 9.81,
#         "turbine_efficiency": 0.9,
#         "head": 10.0,  # m
#     }
#     return {"model_inputs": model_inputs}

@pytest.mark.unit # marks as a unit type test
def test_tidal_power_performance_outputs(performance_tech_config, plant_config, subtests): # can swap between configs here
    prob = om.Problem()

    # START HERE (comp = performance)
    comp = TigerTidalPerformanceModel(
        plant_config=plant_config,
        tech_config=performance_tech_config,
        driver_config={},
    )
    prob.model.add_subsystem("comp", comp, promotes=["*"])
    prob.setup()
    # add velocity input
    vel_t = 4 * np.ones(24*365)
    prob.set_val("tidal_velocity", vel_t, units="m/s") # TODO set as an array of a constant power signal Ex. model.prob.set_val("battery.electricity_demand", demand_profile, units="MW") (ex. constant velocity above power rating)
    prob.run_model()

    commodity = "electricity"
    commodity_amount_units = "kW*h"
    commodity_rate_units = "kW"
    plant_life = int(plant_config["plant"]["plant_life"])
    n_timesteps = int(plant_config["plant"]["simulation"]["n_timesteps"])

    # Check that replacement schedule is between 0 and 1
    # with subtests.test("0 <= replacement_schedule <=1"):
    #     assert np.all(prob.get_val("comp.replacement_schedule", units="unitless") >= 0)
    #     assert np.all(prob.get_val("comp.replacement_schedule", units="unitless") <= 1)

    # with subtests.test("replacement_schedule length"):
    #     assert len(prob.get_val("comp.replacement_schedule", units="unitless")) == plant_life

    # Check that capacity factor is between 0 and 1 with units of "unitless"
    with subtests.test("0 <= capacity_factor (unitless) <=1"):
        assert np.all(prob.get_val("comp.capacity_factor", units="unitless") >= 0)
        assert np.all(prob.get_val("comp.capacity_factor", units="unitless") <= 1)

    # Check that capacity factor is between 1 and 100 with units of "percent"
    with subtests.test("1 <= capacity_factor (percent) <=1"):
        assert np.all(prob.get_val("comp.capacity_factor", units="percent") >= 1)
        assert np.all(prob.get_val("comp.capacity_factor", units="percent") <= 100)

    with subtests.test("capacity_factor length"):
        assert len(prob.get_val("comp.capacity_factor", units="unitless")) == plant_life

    # Test that rated commodity production is greater than zero
    with subtests.test(f"rated_{commodity}_production > 0"):
        assert np.all(
            prob.get_val(f"comp.rated_{commodity}_production", units=commodity_rate_units) > 0
        )

    with subtests.test(f"rated_{commodity}_production length"):
        assert (
            len(prob.get_val(f"comp.rated_{commodity}_production", units=commodity_rate_units)) == 1
        )

    # Test that total commodity production is greater than zero
    with subtests.test(f"total_{commodity}_produced > 0"):
        assert np.all(
            prob.get_val(f"comp.total_{commodity}_produced", units=commodity_amount_units) > 0
        )
    with subtests.test(f"total_{commodity}_produced length"):
        assert (
            len(prob.get_val(f"comp.total_{commodity}_produced", units=commodity_amount_units)) == 1
        )

    # Test that annual commodity production is greater than zero
    with subtests.test(f"annual_{commodity}_produced > 0"):
        assert np.all(
            prob.get_val(f"comp.annual_{commodity}_produced", units=f"{commodity_amount_units}/yr")
            > 0
        )

    with subtests.test(f"annual_{commodity}_produced[1:] == annual_{commodity}_produced[0]"):
        annual_production = prob.get_val(
            f"comp.annual_{commodity}_produced", units=f"{commodity_amount_units}/yr"
        )
        assert np.all(annual_production[1:] == annual_production[0])

    with subtests.test(f"annual_{commodity}_produced length"):
        assert len(annual_production) == plant_life

    # Test that commodity output has some values greater than zero
    with subtests.test(f"Some of {commodity}_out > 0"):
        assert np.any(prob.get_val(f"comp.{commodity}_out", units=commodity_rate_units) > 0)

    with subtests.test(f"{commodity}_out length"):
        assert len(prob.get_val(f"comp.{commodity}_out", units=commodity_rate_units)) == n_timesteps

    # Test default values
    with subtests.test("operational_life default value"):
        assert prob.get_val("comp.operational_life", units="yr") == plant_life
    with subtests.test("replacement_schedule value"):
        assert np.all(prob.get_val("comp.replacement_schedule", units="unitless") == 0)
    

    