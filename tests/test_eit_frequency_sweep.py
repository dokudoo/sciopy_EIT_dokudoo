import struct
from unittest.mock import Mock, call

import pytest

from sciopy.EIT_16_32_64_128 import (
    EIT_16_32_64_128,
)
from sciopy.sciopy_dataclasses import (
    EitFrequencyBlock,
    EitMeasurementSetup,
)


def build_frequency_command(
    f_min,
    f_max,
    f_count,
    f_type,
):
    command = bytearray(
        [0xB0, 0x0C, 0x04]
    )
    command.extend(
        struct.pack(">f", f_min)
    )
    command.extend(
        struct.pack(">f", f_max)
    )
    command.extend(
        f_count.to_bytes(
            2,
            byteorder="big",
            signed=False,
        )
    )
    command.extend(
        [f_type, 0xB0]
    )
    return command


def test_scalar_frequency_remains_supported():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    device.update_ExcitationFrequency(
        100000
    )

    expected = build_frequency_command(
        100000,
        100000,
        1,
        0,
    )

    device.write_command_string.assert_called_once_with(
        expected
    )


def test_linear_and_logarithmic_blocks():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=10,
            f_type="lin",
        ),
        EitFrequencyBlock(
            f_min=10000,
            f_max=100000,
            f_count=20,
            f_type="log",
        ),
    ]

    device.update_ExcitationFrequency(
        blocks
    )

    expected_linear = build_frequency_command(
        1000,
        10000,
        10,
        0,
    )
    expected_logarithmic = build_frequency_command(
        10000,
        100000,
        20,
        1,
    )

    assert (
        device.write_command_string.call_count
        == 2
    )
    device.write_command_string.assert_has_calls(
        [
            call(expected_linear),
            call(expected_logarithmic),
        ]
    )


def test_invalid_frequency_type_is_rejected():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=10,
            f_type="invalid",
        )
    ]

    with pytest.raises(
        ValueError,
        match="f_type",
    ):
        device.update_ExcitationFrequency(
            blocks
        )

    device.write_command_string.assert_not_called()


def test_total_frequency_count_cannot_exceed_128():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=64,
            f_type="lin",
        ),
        EitFrequencyBlock(
            f_min=10000,
            f_max=100000,
            f_count=65,
            f_type="log",
        ),
    ]

    with pytest.raises(
        ValueError,
        match="cannot exceed 128",
    ):
        device.update_ExcitationFrequency(
            blocks
        )

    device.write_command_string.assert_not_called()


def test_set_measurement_setup_forwards_frequency_blocks():
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()
    device.write_command_string = Mock()
    device.update_measurement_mode = Mock()
    device.update_ExcitationFrequency = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=10,
            f_type="lin",
        ),
        EitFrequencyBlock(
            f_min=10000,
            f_max=100000,
            f_count=20,
            f_type="log",
        ),
    ]

    setup = EitMeasurementSetup(
        burst_count=2,
        n_el=16,
        exc_freq=blocks,
        framerate=2,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
    )

    device.SetMeasurementSetup(
        setup
    )

    device.update_ExcitationFrequency.assert_called_once_with(
        blocks
    )