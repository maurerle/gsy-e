from unittest.mock import patch

from pendulum import now, duration

from gsy_e.models.state import StorageState, ESSEnergyOrigin


class TestStorageState:
    """Test the StorageState class."""

    @staticmethod
    def test_market_cycle_reset_orders():
        """Test the market cycle handler of the storage state.

        TODO: Cover the whole module in context of GSY-E:92
        """
        storage_state = StorageState()
        past_time_slot = now()
        current_time_slot = past_time_slot.add(minutes=15)
        future_time_slots = [current_time_slot.add(minutes=15),
                             current_time_slot.add(minutes=30)]
        storage_state.add_default_values_to_state_profiles(
            [past_time_slot, current_time_slot, *future_time_slots])
        storage_state.offered_buy_kWh[future_time_slots[0]] = 10
        storage_state.offered_sell_kWh[future_time_slots[0]] = 10
        with patch("gsy_e.models.state.GlobalConfig.FUTURE_MARKET_DURATION_HOURS", 5):
            storage_state.market_cycle(past_time_slot, current_time_slot, future_time_slots)
            # The future_time_slots[0] is in the future, so it won't reset
            assert storage_state.offered_buy_kWh[future_time_slots[0]] == 10
            assert storage_state.offered_sell_kWh[future_time_slots[0]] == 10
            storage_state.market_cycle(
                current_time_slot, future_time_slots[0], future_time_slots[1:])
            # The future_time_slots[0] is in the spot market, so it has to reset the orders
            assert storage_state.offered_buy_kWh[future_time_slots[0]] == 0
            assert storage_state.offered_sell_kWh[future_time_slots[0]] == 0

    @staticmethod
    def test_market_cycle_update_used_storage():
        storage_state = StorageState(initial_soc=100,
                                     capacity=100)
        past_time_slot = now()
        current_time_slot = past_time_slot.add(minutes=15)
        future_time_slots = [current_time_slot.add(minutes=15),
                             current_time_slot.add(minutes=30)]
        storage_state.add_default_values_to_state_profiles(
            [past_time_slot, current_time_slot, *future_time_slots])
        storage_state.pledged_sell_kWh[past_time_slot] = 10
        storage_state.pledged_buy_kWh[past_time_slot] = 0
        storage_state.market_cycle(past_time_slot, current_time_slot, future_time_slots)
        assert storage_state.used_storage == 90
        storage_state.pledged_sell_kWh[past_time_slot] = 0
        storage_state.pledged_buy_kWh[past_time_slot] = 10
        storage_state.market_cycle(past_time_slot, current_time_slot, future_time_slots)
        assert storage_state.used_storage == 100

    @staticmethod
    def test_market_cycle_ess_share_time_series_dict():
        storage_state = StorageState(initial_soc=100,
                                     capacity=100,
                                     initial_energy_origin=ESSEnergyOrigin.LOCAL)
        past_time_slot = now()
        current_time_slot = past_time_slot.add(minutes=15)
        future_time_slots = [current_time_slot.add(minutes=15),
                             current_time_slot.add(minutes=30)]
        storage_state.add_default_values_to_state_profiles(
            [past_time_slot, current_time_slot, *future_time_slots])

        energy = 10
        storage_state.update_used_storage_share(energy, ESSEnergyOrigin.LOCAL)
        storage_state.update_used_storage_share(energy, ESSEnergyOrigin.UNKNOWN)
        storage_state.update_used_storage_share(energy, ESSEnergyOrigin.UNKNOWN)

        storage_state.pledged_sell_kWh[past_time_slot] = 10
        storage_state.market_cycle(past_time_slot, current_time_slot, future_time_slots)
        expected_time_series = {ESSEnergyOrigin.LOCAL: storage_state.initial_capacity_kWh + energy,
                                ESSEnergyOrigin.EXTERNAL: 0.0,
                                ESSEnergyOrigin.UNKNOWN: 2 * energy}
        assert storage_state.time_series_ess_share[past_time_slot] == expected_time_series

    @staticmethod
    def _initialize_time_slots():
        past_time_slot = now()
        current_time_slot = past_time_slot.add(minutes=15)
        future_time_slots = [current_time_slot.add(minutes=15),
                             current_time_slot.add(minutes=30)]
        return past_time_slot, current_time_slot, future_time_slots

    @staticmethod
    def _step_in_time_slot(current_time_slot):
        past_time_slot = current_time_slot
        current_time_slot = current_time_slot.add(minutes=15)
        future_time_slots = [current_time_slot.add(minutes=15),
                             current_time_slot.add(minutes=30)]
        return past_time_slot, current_time_slot, future_time_slots

    def test_clamp_energy_to_sell_kwh(self):
        storage_state = StorageState(initial_soc=100,
                                     capacity=100,
                                     min_allowed_soc=20)
        past_time_slot, current_time_slot, future_time_slots = self._initialize_time_slots()
        active_market_slot_time_list = [past_time_slot, current_time_slot, *future_time_slots]
        storage_state.add_default_values_to_state_profiles(active_market_slot_time_list)
        storage_state.set_battery_energy_per_slot(slot_length=duration(minutes=15))
        for time_slot in active_market_slot_time_list:
            storage_state.pledged_sell_kWh[time_slot] = 20
            storage_state.offered_sell_kWh[time_slot] = 20

        storage_dict = storage_state.clamp_energy_to_sell_kWh(active_market_slot_time_list)
        assert storage_dict == storage_state.energy_to_sell_dict
        for time_slot in active_market_slot_time_list:
            assert storage_dict[time_slot] is not None
            assert isinstance(storage_dict[time_slot], float)
            # assert storage_dict[time_slot] >= 0.0

    def test_clamp_energy_to_buy_kwh(self):
        storage_state = StorageState(initial_soc=100,
                                     capacity=100,
                                     min_allowed_soc=20)
        past_time_slot, current_time_slot, future_time_slots = self._initialize_time_slots()
        active_market_slot_time_list = [past_time_slot, current_time_slot, *future_time_slots]
        storage_state.add_default_values_to_state_profiles(active_market_slot_time_list)
        storage_state.set_battery_energy_per_slot(slot_length=duration(minutes=15))
        for time_slot in active_market_slot_time_list:
            storage_state.pledged_buy_kWh[time_slot] = 20
            storage_state.offered_buy_kWh[time_slot] = 20

        storage_state.clamp_energy_to_buy_kWh(active_market_slot_time_list)
        energy_to_buy_dict = storage_state.energy_to_buy_dict
        for time_slot in active_market_slot_time_list:
            assert energy_to_buy_dict[time_slot] is not None
            assert isinstance(energy_to_buy_dict[time_slot], (float, int))
            assert energy_to_buy_dict[time_slot] >= 0.0

    @staticmethod
    def test_check_state():
        """  TODO: Test this method."""

    @staticmethod
    def test_delete_past_state_values():
        """  TODO: Test this method."""
