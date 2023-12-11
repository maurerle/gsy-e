from typing import Dict, Union

from gsy_framework.constants_limits import ConstSettings
from pendulum import DateTime

from gsy_e.models.strategy.energy_parameters.storage_profile import StorageProfileEnergyParameters
from gsy_e.models.strategy.scm import SCMStrategy
from gsy_e.models.strategy.state import ScmStorageState
StorageSettings = ConstSettings.StorageSettings


class SCMStorageStrategy(SCMStrategy):
    """Storage SCM strategy."""

    def __init__(
            self, storage_profile: Union[str, Dict[int, float], Dict[str, float]] = None,
            storage_profile_uuid: str = None):
        self._energy_params = StorageProfileEnergyParameters(
            storage_profile, storage_profile_uuid)
        self.storage_profile_uuid = storage_profile_uuid

        self._state = ScmStorageState()

    def serialize(self) -> Dict:
        """Serialize the strategy parameters."""
        return {**self._energy_params.serialize()}

    def activate(self, _area):
        """Overwriting Base method because there is nothing to be done when activating"""

    def market_cycle(self, _area):
        self._energy_params.market_cycle()

    def _get_from_profile(self, time_slot: DateTime) -> float:
        return self._energy_params.energy_profile.profile.get(time_slot)

    def get_energy_to_sell_kWh(self, time_slot: DateTime) -> float:
        """Get the available energy for production for the specified time slot."""
        energy_value = self._get_from_profile(time_slot)
        return abs(energy_value) if energy_value < 0 else 0

    def get_energy_to_buy_kWh(self, time_slot: DateTime) -> float:
        """Get the available energy for consumption for the specified time slot."""
        energy_value = self._get_from_profile(time_slot)
        return energy_value if energy_value > 0 else 0

    @property
    def state(self) -> "ScmStorageState":
        """Return empty state."""
        return self._state
