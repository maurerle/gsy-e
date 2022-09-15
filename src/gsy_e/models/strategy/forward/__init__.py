from abc import ABC, abstractmethod
from typing import Union, TYPE_CHECKING, Dict

from gsy_framework.enums import AvailableMarketTypes
from pendulum import DateTime

from gsy_e.events import EventMixin, AreaEvent, MarketEvent
from gsy_e.models.base import AreaBehaviorBase
from gsy_e.models.strategy.forward.order_updater import OrderUpdater, OrderUpdaterParameters

if TYPE_CHECKING:
    from gsy_e.models.market.forward import ForwardMarketBase


class ForwardStrategyBase(EventMixin, AreaBehaviorBase, ABC):
    """Base class for the forward market strategies."""
    def __init__(self,
                 order_updater_parameters: Dict[AvailableMarketTypes, OrderUpdaterParameters]):
        super().__init__()
        self.enabled = True
        self._allowed_disable_events = [
            AreaEvent.ACTIVATE, MarketEvent.OFFER_TRADED, MarketEvent.BID_TRADED]
        self._order_updater_params = order_updater_parameters
        self._order_updaters = {}

    def _order_updater_for_market_slot_exists(self, market: "ForwardMarketBase", market_slot):
        if market.id not in self._order_updaters:
            return False
        return market_slot in self._order_updaters[market.id]

    def _update_open_orders(self):
        for market, market_slot_updater_dict in self._order_updaters.items():
            for market_slot, updater in market_slot_updater_dict.items():
                if updater.is_time_for_update(self.area.now):
                    self.remove_open_orders(market, market_slot)
                    self.post_order(market, market_slot)

    def _post_orders_to_new_markets(self):
        forward_markets = self.area.forward_markets
        for market_type, market in forward_markets.items():
            if market not in self._order_updaters:
                self._order_updaters[market] = {}

            for market_slot in market.market_time_slots:
                market_parameters = market.get_market_parameters_for_market_slot(market_slot)
                if market_parameters.close_timestamp <= market_parameters.open_timestamp:
                    continue
                if not self._order_updater_for_market_slot_exists(market, market_slot):
                    self._order_updaters[market][market_slot] = OrderUpdater(
                        self._order_updater_params[market_type],
                        market_parameters
                    )
                    self.post_order(market, market_slot)

    def _delete_past_order_updaters(self):
        for market_slot_updater_dict in self._order_updaters.values():
            slots_to_delete = [
                market_slot
                for market_slot in market_slot_updater_dict.keys()
                if market_slot < self.area.now
            ]
            for slot in slots_to_delete:
                market_slot_updater_dict.pop(slot)

    @abstractmethod
    def remove_open_orders(self, market: "ForwardMarketBase", market_slot: DateTime):
        """Remove the open orders on the forward markets."""
        raise NotImplementedError

    @abstractmethod
    def post_order(self, market: "ForwardMarketBase", market_slot: DateTime):
        """Post orders to the forward markets that just opened."""
        raise NotImplementedError

    def event_listener(self, event_type: Union[AreaEvent, MarketEvent], **kwargs):
        """Dispatches the events received by the strategy to the respective methods."""
        if self.enabled or event_type in self._allowed_disable_events:
            super().event_listener(event_type, **kwargs)

    def event_offer_traded(self, *, market_id, trade):
        """Method triggered by the MarketEvent.OFFER_TRADED event."""

    def event_bid_traded(self, *, market_id, bid_trade):
        """Method triggered by the MarketEvent.BID_TRADED event."""

    def event_tick(self):
        self._update_open_orders()

    def event_market_cycle(self):
        self._post_orders_to_new_markets()
