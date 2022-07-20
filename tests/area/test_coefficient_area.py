"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from math import isclose
from unittest.mock import MagicMock

import pytest
from gsy_framework.constants_limits import ConstSettings
from gsy_framework.enums import SpotMarketTypeEnum
from pendulum import duration, today
from pendulum import now

from gsy_e import constants
from gsy_e.models.area import CoefficientArea
from gsy_e.models.area.scm_manager import SCMManager, AreaEnergyBills
from gsy_e.models.config import SimulationConfig
from gsy_e.models.strategy.scm.load import SCMLoadHoursStrategy
from gsy_e.models.strategy.scm.pv import SCMPVStrategy


class TestCoefficientArea:
    # pylint: disable=protected-access
    """Test the Area class behavior and state controllers."""

    @staticmethod
    @pytest.fixture(name="config")
    def config_fixture():
        """Instantiate a mocked configuration."""
        config = MagicMock(spec=SimulationConfig)
        config.slot_length = duration(minutes=15)
        config.tick_length = duration(seconds=15)
        config.ticks_per_slot = int(config.slot_length.seconds / config.tick_length.seconds)
        config.start_date = today(tz=constants.TIME_ZONE)
        config.sim_duration = duration(days=1)

        return config

    @staticmethod
    def setup_method():
        ConstSettings.MASettings.MARKET_TYPE = SpotMarketTypeEnum.COEFFICIENTS.value

    @staticmethod
    def teardown_method():
        ConstSettings.MASettings.MARKET_TYPE = SpotMarketTypeEnum.ONE_SIDED.value

    @staticmethod
    def _create_2_house_grid():
        strategy = MagicMock(spec=SCMPVStrategy)
        strategy.get_energy_to_sell_kWh = MagicMock(return_value=0.5)
        strategy.get_energy_to_buy_kWh = MagicMock(return_value=0.0)
        pv = CoefficientArea(name="pv", strategy=strategy)

        strategy = MagicMock(spec=SCMPVStrategy)
        strategy.get_energy_to_sell_kWh = MagicMock(return_value=0.2)
        strategy.get_energy_to_buy_kWh = MagicMock(return_value=0.0)
        pv2 = CoefficientArea(name="pv 2", strategy=strategy)

        strategy = MagicMock(spec=SCMLoadHoursStrategy)
        strategy.get_energy_to_sell_kWh = MagicMock(return_value=0.0)
        strategy.get_energy_to_buy_kWh = MagicMock(return_value=0.7)
        load = CoefficientArea(name="load", strategy=strategy)

        strategy = MagicMock(spec=SCMLoadHoursStrategy)
        strategy.get_energy_to_sell_kWh = MagicMock(return_value=0.0)
        strategy.get_energy_to_buy_kWh = MagicMock(return_value=0.1)
        load2 = CoefficientArea(name="load 2", strategy=strategy)

        house1 = CoefficientArea(name="House 1", children=[load, pv],
                                 coefficient_percentage=0.6,
                                 feed_in_tariff=0.1,
                                 market_maker_rate=0.3)
        house2 = CoefficientArea(name="House 2", children=[load2, pv2],
                                 coefficient_percentage=0.4,
                                 feed_in_tariff=0.05,
                                 market_maker_rate=0.24)
        return CoefficientArea(name="Grid", children=[house1, house2])

    def test_calculate_after_meter_data(self):
        grid_area = self._create_2_house_grid()
        house1 = grid_area.children[0]
        house2 = grid_area.children[1]
        time_slot = now()
        scm = SCMManager(grid_area, time_slot)
        grid_area.calculate_home_after_meter_data(time_slot, scm)
        assert scm._home_data[house1.uuid].sharing_coefficient_percent == 0.6
        assert scm._home_data[house1.uuid].feed_in_tariff == 0.1
        assert scm._home_data[house1.uuid].market_maker_rate == 0.3
        assert isclose(scm._home_data[house1.uuid].consumption_kWh, 0.7)
        assert isclose(scm._home_data[house1.uuid].production_kWh, 0.5)
        assert isclose(scm._home_data[house1.uuid].self_consumed_energy_kWh, 0.5)
        assert isclose(scm._home_data[house1.uuid].energy_surplus_kWh, 0.0)
        assert isclose(scm._home_data[house1.uuid].energy_need_kWh, 0.2)

        assert scm._home_data[house2.uuid].sharing_coefficient_percent == 0.4
        assert scm._home_data[house2.uuid].feed_in_tariff == 0.05
        assert scm._home_data[house2.uuid].market_maker_rate == 0.24
        assert isclose(scm._home_data[house2.uuid].consumption_kWh, 0.1)
        assert isclose(scm._home_data[house2.uuid].production_kWh, 0.2)
        assert isclose(scm._home_data[house2.uuid].self_consumed_energy_kWh, 0.1)
        assert isclose(scm._home_data[house2.uuid].energy_surplus_kWh, 0.1)
        assert isclose(scm._home_data[house2.uuid].energy_need_kWh, 0.0)

    def test_calculate_community_after_meter_data(self):
        grid_area = self._create_2_house_grid()
        house1 = grid_area.children[0]
        house2 = grid_area.children[1]
        time_slot = now()
        scm = SCMManager(grid_area, time_slot)
        grid_area.calculate_home_after_meter_data(time_slot, scm)
        scm.calculate_community_after_meter_data()

        assert scm._home_data[house1.uuid].community_production_kWh == 0.1
        assert isclose(scm._home_data[house1.uuid].allocated_community_energy_kWh, 0.06)
        assert isclose(scm._home_data[house1.uuid].energy_bought_from_community_kWh, 0.06)
        assert isclose(scm._home_data[house1.uuid].energy_sold_to_grid_kWh, 0.0)

        assert scm._home_data[house2.uuid].community_production_kWh == 0.1
        assert isclose(scm._home_data[house2.uuid].allocated_community_energy_kWh, 0.04)
        assert isclose(scm._home_data[house2.uuid].energy_bought_from_community_kWh, 0.00)
        assert isclose(scm._home_data[house2.uuid].energy_sold_to_grid_kWh, 0.04)

    def test_trigger_energy_trades(self):
        grid_area = self._create_2_house_grid()
        house1 = grid_area.children[0]
        house2 = grid_area.children[1]
        time_slot = now()
        scm = SCMManager(grid_area, time_slot)
        grid_area.calculate_home_after_meter_data(time_slot, scm)
        scm.calculate_community_after_meter_data()
        grid_area.trigger_energy_trades(scm)

        # energy need * normal market maker fees for the case of positive energy need
        assert isclose(scm._bills[house1.uuid].base_energy_bill, 0.06)
        assert isclose(scm._bills[house1.uuid].gsy_energy_bill, 0.06)
        assert isclose(scm._bills[house1.uuid].savings, 0.0)
        assert isclose(scm._bills[house1.uuid].savings_percent, 0.0)
        # energy surplus * feed in tariff for the case of positive energy surplus
        assert isclose(scm._bills[house2.uuid].base_energy_bill, -0.005)
        assert isclose(scm._bills[house2.uuid].gsy_energy_bill, -0.0164)
        assert isclose(scm._bills[house2.uuid].savings, 0.0114)
        assert isclose(scm._bills[house2.uuid].savings_percent, -228.0)
        assert len(scm._home_data[house1.uuid].trades) == 2
        trades = scm._home_data[house1.uuid].trades
        assert isclose(trades[0].trade_rate, 0.3)
        assert isclose(trades[0].traded_energy, 0.06)
        assert trades[0].seller == "Community"
        assert trades[0].buyer == "House 1"
        assert isclose(trades[1].trade_rate, 0.3)
        assert isclose(trades[1].traded_energy, 0.14)
        assert trades[1].seller == "Grid"
        assert trades[1].buyer == "House 1"
        assert len(scm._home_data[house2.uuid].trades) == 2
        trades = scm._home_data[house2.uuid].trades
        assert isclose(trades[0].trade_rate, 0.24)
        assert isclose(trades[0].traded_energy, 0.06)
        assert trades[0].seller == "Community"
        assert trades[0].buyer == "House 2"
        assert isclose(trades[1].trade_rate, 0.05)
        assert isclose(trades[1].traded_energy, 0.04)
        assert trades[1].seller == "House 2"
        assert trades[1].buyer == "Grid"

    @staticmethod
    def test_calculate_energy_benchmark():
        bills = AreaEnergyBills()
        bills.set_min_max_community_savings(10, 90)
        bills.base_energy_bill = 1.0
        bills.gsy_energy_bill = 0.4
        assert isclose(bills.savings_percent, 60.0)
        assert isclose(bills.energy_benchmark, (60 - 10) / (90 - 10))
