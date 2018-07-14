Feature: Run integration tests

  Scenario Outline: Run integration tests on console
     Given we have a scenario named <scenario>
     And d3a is installed
     When we run the d3a simulation on console with <scenario>
     Then we test the export functionality of <scenario>
  Examples: Scenarios
     | scenario |
     | integration_test_setup |

  Scenario Outline: Run integration tests
     Given we have a scenario named <scenario>
     And d3a is installed
     When we run the d3a simulation with <scenario> [<duration>, <slot_length>, <tick_length>]
     Then we test the output of the simulation of <scenario> [<duration>, <slot_length>, <tick_length>]
  Examples: Settings
     | scenario               | duration | slot_length | tick_length |
     | integration_test_setup |    2     |      20     |      1      |
     | integration_test_setup |    4     |      10     |      5      |
     |         default        |    24    |      60     |      60     |
     |         default_2      |    24    |      60     |      60     |
     |        default_2a      |    24    |      60     |      60     |
     |        default_2b      |    24    |      60     |      60     |
     |        default_3       |    24    |      60     |      60     |
     |        default_3a      |    24    |      60     |      60     |
     |        default_3b      |    24    |      60     |      60     |
     |    default_3_pv_only   |    24    |      60     |      60     |
     |        default_4       |    24    |      60     |      60     |
     |        default_5       |    24    |      60     |      60     |
     |    default_appliance   |    24    |      60     |      60     |
     |        default_csv     |    24    |      60     |      60     |

  Scenario: Predefined PV follows the csv profile provided by the user
     Given a PV profile csv as input to predefined PV
     And the scenario includes a predefined PV
     When the simulation is running
     Then the predefined PV follows the PV profile from the csv

  Scenario: Predefined load follows the csv profile provided by the user
     Given a load profile csv as input to predefined load
     And the scenario includes a predefined load that will not be unmatched
     When the simulation is running
     Then the predefined load follows the load profile from the csv

  Scenario: UserProfile PV follows the profile provided by the user as dict
     Given we have a scenario named strategy_tests/user_profile_pv_dict
     And d3a is installed
     When we run the d3a simulation with strategy_tests.user_profile_pv_dict [24, 15, 15]
     Then the UserProfile PV follows the PV profile as dict

  Scenario: Predefined PV follows the profile provided by the user as csv
     Given we have a scenario named strategy_tests/user_profile_pv_csv
     And d3a is installed
     When we run the d3a simulation with strategy_tests.user_profile_pv_csv [24, 15, 15]
     Then the UserProfile PV follows the PV profile of csv

  Scenario: Predefined PV follows the profile provided by the user
     Given we have a scenario named strategy_tests/predefined_pv
     And d3a is installed
     When we run the d3a simulation with strategy_tests.predefined_pv [24, 15, 15]
     Then the predefined PV follows the PV profile

  Scenario: Predefined load follows the profile provided by the user
     Given a load profile hourly dict as input to predefined load
     And the scenario includes a predefined load that will not be unmatched
     When the simulation is running
     Then the predefined load follows the load profile

  Scenario Outline: Simulation subscribes on the appropriate channels
     Given d3a is installed
     When a simulation is created for scenario <scenario>
     And the method <method> is registered
     And the configured simulation is running
     And a message is sent on <channel>
     Then <method> is called
  Examples: Incoming events
     | scenario   | channel    | method       |
     | default_2a | 1234/stop  | stop         |
     | default_2a | 1234/pause | toggle_pause |
     | default_2a | 1234/reset | reset        |

  Scenario: Simulation publishes intermediate and final results
     Given d3a is installed
     When a simulation is created for scenario default_2a
     And the simulation is able to transmit intermediate results
     And the simulation is able to transmit final results
     And the configured simulation is running
     Then intermediate results are transmitted on every slot
     And final results are transmitted once


  Scenario Outline: Run integration tests with settings file
     Given we have a scenario named default
     And d3a is installed
     When we run simulation on console with default settings file
     Then we test the export functionality of default

  Scenario: Storage break even range profile
     Given we have a scenario named strategy_tests/storage_strategy_break_even_range
     And d3a is installed
     When we run the d3a simulation with strategy_tests.storage_strategy_break_even_range [24, 15, 15]
     Then the storage devices buy and sell energy respecting the break even prices

  Scenario Outline: Run integration tests for config parameters
     Given we have a scenario named <scenario>
     And d3a is installed
     And we have a profile of market_maker_rate for <scenario>
     When we run the d3a simulation with config parameters [<cloud_coverage>, <iaa_fee>] and <scenario>
     Then we test that config parameters are correctly parsed for <scenario> [<cloud_coverage>, <iaa_fee>]
  Examples: Settings
     |      scenario               | cloud_coverage  |    iaa_fee    |
     |      default_2a             |        1        |       5       |


  Scenario: Storage break even profile
     Given we have a scenario named strategy_tests/storage_strategy_break_even_hourly
     And d3a is installed
     When we run the d3a simulation with strategy_tests.storage_strategy_break_even_hourly [24, 15, 15]
     Then the storage devices buy and sell energy respecting the hourly break even prices

  Scenario: Finite power plant
     Given we have a scenario named strategy_tests/finite_power_plant
     And d3a is installed
     When we run the d3a simulation with strategy_tests.finite_power_plant [24, 15, 15]
     Then the Finite Commercial Producer always sells energy at the defined energy rate
     And the Finite Commercial Producer never produces more power than its max available power

  Scenario: Finite power plant profile
     Given we have a scenario named strategy_tests/finite_power_plant_profile
     And d3a is installed
     When we run the d3a simulation with strategy_tests.finite_power_plant_profile [24, 15, 15]
     Then the Finite Commercial Producer Profile always sells energy at the defined energy rate
     And the Finite Commercial Producer Profile never produces more power than its max available power
