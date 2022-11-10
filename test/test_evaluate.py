import pytest

from ..src.evaluate import mark_true_positives


@pytest.mark.parametrize(
    "ground_truth,onsets,tolerance,expected",[
        ([5], [5], 1, ({5: True}, {5: True})),
        (
            [1, 2],
            [1.1, 1.9],
            0.1,
            ({1: True, 2: True}, {1.1: True, 1.9: True}),
        ),
        (
            [1, 2, 3, 4],
            [1, 5],
            0.1,
            ({1: True, 2: False, 3: False, 4: False}, {1: True, 5: False})
        )
    ]
)
def test_mark_true_positives(ground_truth, onsets, tolerance, expected):
    marked_true_positives = mark_true_positives(ground_truth, onsets, tolerance)
    assert marked_true_positives == expected
