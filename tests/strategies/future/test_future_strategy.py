"""
Copyright 2018 Grid Singularity
This file is part of D3A.

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
import uuid
from unittest.mock import Mock, MagicMock

import pytest
from pendulum import today, duration

from d3a.constants import TIME_ZONE
from d3a.models.market.future import FutureMarkets
from d3a.models.strategy.future.strategy import FutureMarketStrategy
from d3a.models.strategy.load_hours import LoadHoursStrategy
from d3a.models.strategy.pv import PVStrategy


class TestFutureMarketStrategy:

    def setup_method(self):
        self.future_strategy = FutureMarketStrategy(10, 50, 50, 20)
        self.time_slot = today(tz=TIME_ZONE).at(hour=12, minute=0, second=0)
        self.area_mock = Mock()
        self.area_mock.name = "test_name"
        self.area_mock.uuid = str(uuid.uuid4())
        self.future_markets = MagicMock(spec=FutureMarkets)
        self.future_markets.market_time_slots = [self.time_slot]
        self.future_markets.id = str(uuid.uuid4())

    def _setup_strategy_fixture(self, strategy_fixture):
        strategy_fixture.owner = self.area_mock
        strategy_fixture.area = Mock()
        strategy_fixture.area.future_markets = self.future_markets
        strategy_fixture.area.current_tick = 0
        strategy_fixture.area.config = Mock()
        strategy_fixture.area.config.ticks_per_slot = 60
        strategy_fixture.area.config.tick_length = duration(seconds=15)

    @pytest.mark.parametrize(
        "strategy_fixture", [LoadHoursStrategy(100), PVStrategy()])
    def test_event_market_cycle_posts_bids_and_offers(self, strategy_fixture):
        self._setup_strategy_fixture(strategy_fixture)
        if isinstance(strategy_fixture, LoadHoursStrategy):
            strategy_fixture.state.set_desired_energy(1234.0, self.time_slot)
            self.future_strategy.event_market_cycle(strategy_fixture)
            self.future_markets.bid.assert_called_once_with(
                10.0, 1.234, self.area_mock.name, original_price=10.0,
                buyer_origin=self.area_mock.name, buyer_origin_id=self.area_mock.uuid,
                buyer_id=self.area_mock.uuid, attributes=None, requirements=None,
                time_slot=self.time_slot
            )
        if isinstance(strategy_fixture, PVStrategy):
            strategy_fixture.state.set_available_energy(321.3, self.time_slot)
            self.future_strategy.event_market_cycle(strategy_fixture)
            self.future_markets.offer.assert_called_once_with(
                price=50.0, energy=321.3, seller=self.area_mock.name,
                seller_origin=self.area_mock.name,
                seller_origin_id=self.area_mock.uuid, seller_id=self.area_mock.uuid,
                time_slot=self.time_slot
            )

    # @pytest.mark.parametrize(
    #     "strategy_fixture", [LoadHoursStrategy(100), PVStrategy()])
    # @pytest.mark.parametrize("can_post_settlement_bid", [True, False])
    # @pytest.mark.parametrize("can_post_settlement_offer", [True, False])
    # def test_event_tick_updates_bids_and_offers(
    #         self, strategy_fixture, can_post_settlement_bid, can_post_settlement_offer):
    #     self._setup_strategy_fixture(
    #         strategy_fixture, can_post_settlement_bid, can_post_settlement_offer)
    #
    #     strategy_fixture.area.current_tick = 0
    #     strategy_fixture.area.config = Mock()
    #     strategy_fixture.area.config.ticks_per_slot = 60
    #     strategy_fixture.area.config.tick_length = duration(seconds=15)
    #     self.settlement_strategy.event_market_cycle(strategy_fixture)
    #
    #     strategy_fixture.area.current_tick = 30
    #     self.market_mock.bid.reset_mock()
    #     self.market_mock.offer.reset_mock()
    #
    #     strategy_fixture.area.current_tick = 19
    #     self.settlement_strategy.event_tick(strategy_fixture)
    #     strategy_fixture.area.current_tick = 20
    #     self.settlement_strategy.event_tick(strategy_fixture)
    #     if can_post_settlement_bid:
    #         self.market_mock.bid.assert_called_once_with(
    #             30.0, 1.0, self.area_mock.name, original_price=30.0,
    #             buyer_origin=self.area_mock.name, buyer_origin_id=self.area_mock.uuid,
    #             buyer_id=self.area_mock.uuid, attributes=None, requirements=None,
    #             time_slot=self.time_slot
    #         )
    #     if can_post_settlement_offer:
    #         self.market_mock.offer.assert_called_once_with(
    #             35, 1, self.area_mock.name, original_price=35,
    #             seller_origin=None, seller_origin_id=None, seller_id=self.area_mock.uuid,
    #             time_slot=self.time_slot
    #         )
    #
    # @pytest.mark.parametrize(
    #     "strategy_fixture", [LoadHoursStrategy(100), PVStrategy()])
    # def test_event_trade_updates_energy_deviation(self, strategy_fixture):
    #     self._setup_strategy_fixture(strategy_fixture, False, True)
    #     strategy_fixture.state.set_energy_measurement_kWh(10, self.time_slot)
    #     self.settlement_strategy.event_market_cycle(strategy_fixture)
    #     self.settlement_strategy.event_offer_traded(
    #         strategy_fixture, self.market_mock.id,
    #         Trade("456", self.time_slot, self.test_offer,
    #         self.area_mock.name, self.area_mock.name)
    #     )
    #     assert strategy_fixture.state.get_unsettled_deviation_kWh(self.time_slot) == 9
    #
    # @pytest.mark.parametrize(
    #     "strategy_fixture", [LoadHoursStrategy(100), PVStrategy()])
    # def test_event_bid_trade_updates_energy_deviation(self, strategy_fixture):
    #     self._setup_strategy_fixture(strategy_fixture, True, False)
    #     strategy_fixture.state.set_energy_measurement_kWh(15, self.time_slot)
    #     self.settlement_strategy.event_market_cycle(strategy_fixture)
    #     self.settlement_strategy.event_bid_traded(
    #         strategy_fixture, self.market_mock.id,
    #         Trade("456", self.time_slot, self.test_bid, self.area_mock.name, self.area_mock.name)
    #     )
    #     assert strategy_fixture.state.get_unsettled_deviation_kWh(self.time_slot) == 14
