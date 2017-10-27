import pytest
import requests_mock

from d3a.models.area import DEFAULT_CONFIG
from d3a.models.events import AreaEvent
from d3a.models.overview import Overview


class FakeArea:
    def __init__(self):
        self.current_tick = 0

    @property
    def config(self):
        return DEFAULT_CONFIG

    ticks_per_slot = DEFAULT_CONFIG.slot_length / DEFAULT_CONFIG.tick_length


@pytest.fixture
def fixture():
    area = FakeArea()
    area.current_tick = FakeArea.ticks_per_slot
    return Overview(area, "http://mock.com")


def test_overview_sends(fixture):
    with requests_mock.Mocker() as mocker:
        mocker.post("http://mock.com")
        fixture.event_listener(AreaEvent.TICK)
        assert mocker.call_count == 1
        assert mocker.request_history[0].json()['todo'] == 'post data'


def test_overview_ignores_other_events(fixture):
    with requests_mock.Mocker() as mocker:
        mocker.post("http://mock.com")
        fixture.event_listener(AreaEvent.ACTIVATE)
        fixture.area.current_tick = 1
        fixture.event_listener(AreaEvent.TICK)
        assert mocker.call_count == 0
