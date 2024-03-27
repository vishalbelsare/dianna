import numpy as np
import dianna
from tests.utils import run_model


def assert_tabular_regression_correct_output_shape(method):
    """Runs the explainer class with random data and asserts the output shape."""
    training_data = np.random.random((10, 2))
    input_data = np.random.random(2)
    feature_names = ["feature_1", "feature_2"]
    exp = dianna.explain_tabular(run_model,
                                 input_tabular=input_data,
                                 method=method,
                                 mode='regression',
                                 training_data=training_data,
                                 feature_names=feature_names,
                                 class_names=['class_1'])
    assert len(exp) == len(feature_names)


def assert_tabular_classification_correct_output_shape(explainer_class):
    """Runs the explainer class with random data and asserts the output shape."""
    training_data = np.random.random((10, 2))
    input_data = np.random.random(2)
    feature_names = ["feature_1", "feature_2"]
    explainer = explainer_class(training_data,
                                mode='classification',
                                feature_names=feature_names,
                                class_names=["class_1", "class_2"])
    exp = explainer.explain(
        run_model,
        input_data,
        labels=[0],
    )
    assert len(exp[0]) == len(feature_names)


def assert_tabular_simple_dummy_model(explainer_class):
    """Tests if the explainer can find the single important feature in otherwise random data."""
    np.random.seed(0)
    training_data = np.random.random((100, 10))
    num_features = 25
    input_data = np.array(num_features // 2 * [1.0] +
                          (num_features - num_features // 2) * [0.0])
    feature_names = [f"feature_{i}" for i in range(num_features)]
    important_feature_i = 2

    def dummy_model(tabular_data):
        """Model with output dependent on a single feature of the first instance."""
        prediction = tabular_data[:, important_feature_i]
        return np.vstack([prediction, -prediction + 1]).T

    explainer = explainer_class(
        training_data,
        mode='classification',
        feature_names=feature_names,
        class_names=["class_1", "class_2"],
        keep_masks=True,
        keep_predictions=True,
    )
    explanations = explainer.explain(
        dummy_model,
        input_data,
        labels=[0, 1],
    )

    assert np.argmax(explanations[0]) == important_feature_i
    assert np.argmin(explanations[1]) == important_feature_i
