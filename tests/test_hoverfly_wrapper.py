import json
import os

import pytest
import requests

from pytest_hoverfly_wrapper.plugin import generate_logs, template_block_domain_json


def test_raise_hoverflycrashedexc(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        from pytest_hoverfly_wrapper.simulations import GeneratedSimulation
        import pytest
        import requests

        @pytest.mark.simulated(GeneratedSimulation())
        def test_sth(setup_hoverfly, mocker):
            mock_obj = mocker.patch("requests.get")
            mock_obj.side_effect = requests.exceptions.ConnectionError
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest()

    assert result.ret == 1

    result.stdout.fnmatch_lines(
        ["*raise HoverflyCrashedException*",]
    )


def test_custom_test_data_dir(testdir):
    """Test creating a custom directory."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        from pytest_hoverfly_wrapper.simulations import GeneratedSimulation
        import pytest
        import requests
        
        @pytest.fixture
        def test_data_dir():
            return "./this/dir/structure/doesnt/exist"

        @pytest.mark.simulated(GeneratedSimulation())
        def test_sth(setup_hoverfly):
            pass
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest()

    assert result.ret == 0


def test_generate_logs(mocker, tmpdir):
    mock_request = mocker.MagicMock()
    mock_request.node.sensitive = ["sensitive.host"]
    mock_request.node.mode = "simulate"
    mock_journal_api = mocker.MagicMock()
    mock_journal_api.get.return_value = json.load(open("tests/input.json"))
    log_file = os.path.join(tmpdir.strpath, "network.json")
    # golden path
    generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)
    assert os.path.isfile(log_file)
    # exception raised if sensitive host isn't cached
    del mock_journal_api.get.return_value["journal"][0]["response"]["headers"]["Hoverfly-Cache-Served"]
    with pytest.raises(AssertionError):
        generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)

    # useful message dumped if hoverfly crashes during log retrieval
    mock_journal_api.get.side_effect = requests.exceptions.ConnectionError
    generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)
    assert json.load(open(log_file)) == {"msg": "Hoverfly crashed while retrieving logs"}


def test_no_simulation_marker(setup_hoverfly):
    # We should be able to setup Hoverfly without specifying a simulation
    pass


def test_template_block_domain_json():
    template_block_domain_json("reddit.com")


def test_marker_registered(testdir):
    """Make sure that the plugin's markers are registered."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        from pytest_hoverfly_wrapper.simulations import GeneratedSimulation
        import pytest
        import requests

        @pytest.mark.simulated(GeneratedSimulation())
        def test_sth(setup_hoverfly, mocker):
            pass
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--strict")

    assert result.ret == 0


# TODO: end-to-end tests covering:
#  using static sims,
#  recording and using sims,
#  logging output,
#  spying mode,
#  default mode,
#  combining sims,
#  command line parameters,
#  raising exceptions when sensitive host URLs are accessed,
#  unit tests for setup_hoverfly_mode and generate_logs
# crashing hoverfly
