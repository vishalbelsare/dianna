import numpy as np
import pytest
from pandas import DataFrame
from dianna.utils.maskers import _generate_interpolated_float_masks
from dianna.utils.maskers import _generate_interpolated_float_masks_for_timeseries
from dianna.utils.maskers import _project_grids_to_masks_v3
from dianna.utils.maskers import generate_channel_masks
from dianna.utils.maskers import generate_masks
from dianna.utils.maskers import generate_time_step_masks
from dianna.utils.maskers import mask_data


def test_mask_has_correct_shape_univariate():
    """Test masked data has the correct shape for a univariate input."""
    input_data = _get_univariate_input_data()
    number_of_masks = 5

    result = _call_masking_function(input_data,
                                    number_of_masks=number_of_masks)

    assert result.shape == tuple([number_of_masks] + list(input_data.shape))


def test_mask_has_correct_type_univariate():
    """Test masked data has the correct dtype for a univariate input."""
    input_data = _get_univariate_input_data()
    number_of_masks = 5

    result = generate_masks(input_data, number_of_masks=number_of_masks)

    assert result.dtype == np.bool


def test_generate_time_step_masks_dtype_multivariate():
    """Test masked data has the correct dtype for a multivariate input."""
    input_data = _get_multivariate_input_data()
    number_of_masks = 5

    result = generate_time_step_masks(input_data,
                                      number_of_masks=number_of_masks,
                                      number_of_features=8,
                                      p_keep=0.5)

    assert result.dtype == np.bool


def test_generate_segmented_time_step_masks_dtype_multivariate():
    """Test masked data has the correct dtype for a multivariate input."""
    input_data = _get_multivariate_input_data()
    number_of_masks = 5

    result = generate_time_step_masks(input_data,
                                      number_of_masks=number_of_masks,
                                      number_of_features=8,
                                      p_keep=0.5)

    assert result.dtype == np.bool


def test_mask_has_correct_shape_multivariate():
    """Test masked data has the correct shape for a multivariate input."""
    input_data = _get_multivariate_input_data()
    number_of_masks = 5

    result = _call_masking_function(input_data,
                                    number_of_masks=number_of_masks)

    assert result.shape == tuple([number_of_masks] + list(input_data.shape))


@pytest.mark.parametrize(
    'p_keep_and_expected_rate',
    [
        (0.1, 0.1),  # Mask all but one
        (0.1, 0.1),
        (0.3, 0.3),
        (0.5, 0.5),
        (0.99, 0.9),  # Mask only 1
    ])
def test_mask_contains_correct_number_of_unmasked_parts(
        p_keep_and_expected_rate):
    """Number of unmasked parts should be conforming the given p_keep."""
    p_keep, expected_rate = p_keep_and_expected_rate
    input_data = _get_univariate_input_data()

    result = _call_masking_function(input_data, p_keep=p_keep)

    assert np.sum(result == input_data) / np.product(
        result.shape) == expected_rate


def test_mask_contains_correct_parts_are_mean_masked():
    """All parts that are masked should now contain the mean of the input."""
    input_data = _get_univariate_input_data()
    mean = np.mean(input_data)

    result = _call_masking_function(input_data, mask_type='mean')

    masked_parts = result[(result != input_data)]
    assert np.alltrue(
        masked_parts ==
        mean), f'All elements in {masked_parts} should have value {mean}'


def _get_univariate_input_data(num_steps=10) -> np.array:
    """Get some univariate test data."""
    return np.zeros(
        (num_steps, 1)) + np.arange(num_steps).reshape(num_steps, 1)


def _get_multivariate_input_data(number_of_channels: int = 6) -> np.array:
    """Get some multivariate test data."""
    return np.row_stack([
        np.zeros((10, number_of_channels)),
        np.ones((10, number_of_channels))
    ])


def _call_masking_function(
    input_data,
    number_of_masks=5,
    p_keep=.3,
    mask_type='mean',
    feature_res=5,
):
    """Helper function with some defaults to call the code under test."""
    masks = generate_masks(input_data,
                           number_of_masks,
                           feature_res,
                           p_keep=p_keep)
    return mask_data(input_data, masks, mask_type=mask_type)


def test_channel_mask_has_correct_shape_multivariate():
    """Tests the output has the correct shape."""
    number_of_masks = 15
    input_data = _get_multivariate_input_data()

    result = generate_channel_masks(input_data, number_of_masks, 0.5)

    assert result.shape == tuple([number_of_masks] + list(input_data.shape))


def test_channel_mask_has_does_not_contain_conflicting_values():
    """Tests that only complete channels are masked."""
    number_of_masks = 15
    input_data = _get_multivariate_input_data()

    result = generate_channel_masks(input_data, number_of_masks, 0.5)

    unexpected_results = []
    for mask_i, mask in enumerate(result):
        for channel_i in range(mask.shape[-1]):
            channel = mask[:, channel_i]
            value = channel[0]
            if (not value) in channel:
                unexpected_results.append(
                    f'Mask {mask_i} contains conflicting values in channel {channel_i}. Channel: {channel}'
                )
    assert not unexpected_results


def test_channel_mask_masks_correct_number_of_cells():
    """Tests whether the correct fraction of cells is masked."""
    number_of_masks = 1
    input_data = _get_multivariate_input_data(number_of_channels=10)
    p_keep = 0.3

    result = generate_channel_masks(input_data, number_of_masks, p_keep)

    assert result.sum() / np.product(result.shape) == p_keep


def test_masking_has_correct_shape_multivariate():
    """Test for the correct output shape for the general masking function."""
    number_of_masks = 15
    input_data = _get_multivariate_input_data()

    result = generate_masks(input_data, number_of_masks)

    assert result.shape == tuple([number_of_masks] + list(input_data.shape))


def test_masking_univariate_leaves_anything_unmasked():
    """Tests that something remains unmasked and some parts are masked for the univariate case."""
    number_of_masks = 1
    input_data = _get_univariate_input_data()

    result = generate_masks(input_data, number_of_masks)

    assert np.any(result)
    assert np.any(~result)


def test_masking_keep_first_instance():
    """First instance must be the original data for Lime timeseries.

    Required by `lime_base` explainer, the first instance of masked (or perturbed)
    data must be the original instance.

    More details can be found in the code:
    https://github.com/marcotcr/lime/blob/fd7eb2e6f760619c29fca0187c07b82157601b32/lime/lime_base.py#L148
    """
    input_data = _get_multivariate_input_data()
    number_of_masks = 5
    masks = generate_masks(input_data, number_of_masks, p_keep=0.9)
    masks[0, :, :] = 1.0
    masked = mask_data(input_data, masks, mask_type="mean")
    assert np.array_equal(masked[0, :, :], input_data)


@pytest.mark.parametrize('num_steps', range(3, 20))
def test_masks_approximately_correct_number_of_masked_parts_per_time_step(
        num_steps):
    """Number of unmasked parts should be conforming the given p_keep."""
    p_keep = 0.5
    number_of_masks = 500
    input_data = _get_univariate_input_data(num_steps=num_steps)

    masks = generate_masks(input_data,
                           number_of_masks=number_of_masks,
                           feature_res=num_steps,
                           p_keep=p_keep)[:, :, 0]

    masks_mean = DataFrame(masks).mean()
    print('\n')
    print(masks_mean)
    assert np.allclose(masks_mean, p_keep, atol=0.1)


@pytest.mark.parametrize('num_steps', [
    10,
    3,
])
def test_generate_interpolated_mean_float_masks(num_steps):
    """Mean of float masks should be conforming the given p_keep."""
    p_keep = 0.5
    number_of_masks = 500
    input_data = _get_univariate_input_data(num_steps=num_steps)

    masks = _generate_interpolated_float_masks(
        input_data.shape,
        p_keep=0.5,
        number_of_masks=number_of_masks,
        number_of_features=num_steps,
    )[:, :, 0, 0]

    masks_mean = DataFrame(masks).sum() / number_of_masks
    print('\n')
    print(masks_mean)
    assert np.allclose(masks_mean, p_keep, atol=0.1)


@pytest.mark.parametrize('num_steps', range(2, 20))
def test_generate_interpolated_order_float_masks(num_steps):
    """Number of unmasked parts should be conforming the given p_keep."""
    number_of_masks = 500
    input_data = _get_univariate_input_data(num_steps=num_steps)

    masks = _generate_interpolated_float_masks_for_timeseries(
        input_data.shape,
        number_of_masks=number_of_masks,
        number_of_features=num_steps,
    )[:, :, 0, 0]

    assert_and_print_rank_counts(masks, num_steps)


@pytest.mark.parametrize('num_steps', range(2, 20))
def test_generate_interpolated_order_float_masks_interpolated(num_steps):
    """Number of unmasked parts should be conforming the given p_keep."""
    number_of_masks = 10000
    input_data = _get_univariate_input_data(num_steps=num_steps)

    masks = _generate_interpolated_float_masks_for_timeseries(
        input_data.shape,
        number_of_masks=number_of_masks,
        number_of_features=3,
    )[:, :, 0, 0]

    assert_and_print_rank_counts(masks, num_steps)


def _count_ranks(masks):
    number_of_masks = masks.shape[0]
    num_steps = masks.shape[1]
    indices = np.argsort(-masks,
                         axis=1)  # negation to end up with a descending sort
    counts = np.empty((num_steps, num_steps))
    for time_step in range(num_steps):
        for rank in range(num_steps):
            p_rank = np.sum(indices[:, time_step] == rank) / number_of_masks
            counts[time_step, rank] = p_rank
    return counts


def test_projection():
    """Number of unmasked parts should be conforming the given p_keep."""
    grid_source = np.array([0.9, 0.5, 0.0])
    permutations = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1],
                    [2, 1, 0]]
    grid = np.concatenate([
        grid_source[[a, b, c]].reshape(1, 3, 1, 1) for a, b, c in permutations
    ],
                          axis=0)
    repetitions = 1000
    grids = np.tile(grid, (repetitions, 1, 1, 1))
    assert_and_print_rank_counts(grids.reshape(grids.shape[:2]),
                                 grid_source.shape[0])

    num_steps = 3
    number_of_masks = grids.shape[0]
    masks = _project_grids_to_masks_v3(grids,
                                       masks_shape=(number_of_masks, num_steps,
                                                    1),
                                       offset=0.25)[:, :, 0]

    assert_and_print_rank_counts(masks, num_steps)


@pytest.mark.skip(reason='draft')
def test_projection_draft():
    """Number of unmasked parts should be conforming the given p_keep with a set of evenly distributed offsets."""
    grid_source = np.array([0.0, 0.1, 0.9])
    permutations = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1],
                    [2, 1, 0]]

    grids_list = []
    for i, permutation in enumerate(permutations):
        grid = np.concatenate([
            grid_source[[a, b, c]].reshape(1, 3, 1, 1)
            for a, b, c in permutations[i:i + 1]
        ],
                              axis=0)
        repetitions = 1
        grids = np.tile(grid, (repetitions, 1, 1, 1))
        # assert_and_print_rank_counts(grids.reshape(grids.shape[:2]), grid_source.shape[0])
        grids_list.append(grids)

    num_steps = 3

    offsets = np.linspace(start=0, stop=1, num=100, endpoint=False)

    all_masks_list = []
    for grids in grids_list:
        counts = []
        number_of_masks = grids.shape[0]
        masks_list = []
        for offset in offsets:
            mask = _project_grids_to_masks_v3(grids,
                                              masks_shape=(number_of_masks,
                                                           num_steps, 1),
                                              offset=offset)[:, :, 0]
            masks_list.append(mask)
            all_masks_list.append(mask)
            counts.append(_count_ranks(mask))
        masks = np.concatenate(masks_list)
        title = str(grids[0, :, 0, 0])
        print(title)
        _plot_ranks(counts, offsets, title)

        assert_and_print_rank_counts(masks, num_steps)
    all_masks = np.concatenate(all_masks_list)
    assert_and_print_rank_counts(all_masks, num_steps)
    # _plot(grids, masks, 0)


def _plot_ranks(counts, offsets, title):
    from matplotlib import pyplot as plt
    colors = ['r', 'g', 'b']
    for i_channel in range(len(counts[0])):
        plt.plot(offsets, [np.argmax(count[i_channel]) for count in counts],
                 color=colors[i_channel],
                 label=i_channel)
    plt.title(title)
    plt.legend()
    plt.show()


def _plot(grids=None, masks=None, _offset=None):
    from matplotlib import pyplot as plt
    grid_size = grids.shape[1]
    mask_size = masks.shape[1]

    x_masks = np.linspace(start=0 + _offset,
                          stop=grid_size - 2 + _offset,
                          num=mask_size)
    x_grids = np.linspace(start=0, stop=grid_size - 1, num=grid_size)
    mask_vals = masks[0, :, 0]
    grid_vals = grids[0, :, 0]
    plt.scatter(x=x_masks, y=mask_vals, color='r')
    plt.scatter(x=x_grids, y=grid_vals)


def assert_and_print_rank_counts(masks, num_steps):
    """Asserts even first rank distribution."""
    counts = _count_ranks(masks)
    index = [['timestep #' for _ in range(num_steps)], list(range(num_steps))]
    columns = [['rank #' for _ in range(num_steps)], list(range(num_steps))]
    print(DataFrame(counts, index=index, columns=columns))

    assert np.allclose(counts, 1 / num_steps, atol=0.1)
