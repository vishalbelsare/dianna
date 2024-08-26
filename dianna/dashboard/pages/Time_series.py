from matplotlib import pyplot as plt
import numpy as np
import streamlit as st
from _model_utils import load_labels
from _model_utils import load_model
from _models_ts import explain_ts_dispatcher
from _models_ts import predict
from _shared import _get_top_indices_and_labels
from _shared import _methods_checkboxes
from _shared import add_sidebar_logo
from _shared import reset_example
from _shared import reset_method
from _ts_utils import _convert_to_segments
from _ts_utils import open_timeseries
from dianna.utils.downloader import download
from dianna.visualization import plot_timeseries

st.title('Time series explanation')

add_sidebar_logo()
st.sidebar.header('Input data')

input_type = st.sidebar.radio(
        label='Select which input to use',
        options = ('Use an example', 'Use your own data'),
        index = None,
        on_change = reset_example,
        key = 'TS_input_type'
    )

# Use the examples
if input_type == 'Use an example':
    load_example = st.sidebar.radio(
        label='Select example',
        options = ('Weather', 'Scientific case: FRB'),
        index = None,
        on_change = reset_method,
        key = 'TS_load_example'
    )

    if load_example == "Weather":
        ts_data_file = download('weather_data.npy', 'data')
        ts_model_file = download(
                        'season_prediction_model_temp_max_binary.onnx', 'model')
        ts_label_file = download('weather_data_labels.txt', 'label')

        st.markdown(
        """
        This example demonstrates the use of DIANNA
        on a pre-trained binary classification model for season prediction. The
        input data is the [weather prediction
        dataset](https://zenodo.org/records/5071376). This classification model
        uses time (days) as function of mean temperature to predict if the whole
        time series is either summer or winter. Using a chosen XAI method the
        relevance scores are displayed on top of the timeseries. The days
        contributing positively towards the classification decision are
        indicated in red and those who contribute negatively in blue.
        """)
    elif load_example == "Scientific case: FRB":
        ts_model_file = download('apertif_frb_dynamic_spectrum_model.onnx', 'model')
        ts_label_file = download('apertif_frb_classes.txt', 'label')
        ts_data_file = download('FRB211024.npy', 'data')

        # FRB data must be preprocessed
        def preprocess(data):
            """Preprocessing function for FRB use case to get the data in the right shape."""
            return np.transpose(data, (0, 2, 1))[..., None].astype(np.float32)

        # Transform FRB data for the model prediction and dianna explanation, which have different
        # requirements for this specific data
        ts_data = open_timeseries(ts_data_file)
        ts_data_explainer = ts_data.T[None, ...]
        ts_data_predictor = ts_data[None, ..., None]

        st.markdown(
            """This example demonstrates the use of DIANNA
            on a pre-trained binary classification model trained to classify
            Fast Radio Burst (FRB) timeseries data.
            The goal of the pre-trained convolutional neural network is to
            determine whether or not the input data contains an
            FRB-like signal, whereby the two classes are noise and FRB.
            """)
    else:
        st.info('Select an example in the left panel to coninue')
        st.stop()


# Option to upload your own data
if input_type == 'Use your own data':
    load_example = None

    ts_data_file = st.sidebar.file_uploader('Select input data',
                                    type='npy')

    ts_model_file = st.sidebar.file_uploader('Select model',
                                            type='onnx')

    ts_label_file = st.sidebar.file_uploader('Select labels',
                                            type='txt')

if input_type is None:
    st.info('Select which input type to use in the left panel to continue')
    st.stop()

if not (ts_data_file and ts_model_file and ts_label_file):
    st.info('Add your input data in the left panel to continue')
    st.stop()

if load_example != "Scientific case: FRB":
    # For normal cases, the input data does not need transformation for either the
    # model explainer nor the model predictor
    ts_data_explainer = ts_data_predictor = open_timeseries(ts_data_file)

model = load_model(ts_model_file)
serialized_model = model.SerializeToString()

labels = load_labels(ts_label_file)

if load_example == "Scientific case: FRB":
    choices = ('RISE',)
    param_key = 'FRB_TS_cb'
else:
    choices = ('RISE', 'LIME')
    param_key = 'TS_cb'

st.text("")
st.text("")

with st.container(border=True):
    prediction_placeholder = st.empty()
    methods, method_params = _methods_checkboxes(choices=choices, key=param_key)

    with st.spinner('Predicting class'):
        predictions = predict(model=serialized_model, ts_data=ts_data_predictor)

    with prediction_placeholder:
        top_indices, top_labels = _get_top_indices_and_labels(
            predictions=predictions[0], labels=labels)

st.text("")
st.text("")

weight = 0.9 / len(methods)
column_spec = [0.1, *[weight for _ in methods]]

_, *columns = st.columns(column_spec)
for col, method in zip(columns, methods):
    col.markdown(f"<h4 style='text-align: center; '>{method}</h4>", unsafe_allow_html=True)

for index, label in zip(top_indices, top_labels):
    index_col, *columns = st.columns(column_spec)
    index_col.markdown(f'##### Class: {label}')

    for col, method in zip(columns, methods):
        kwargs = method_params[method].copy()
        kwargs['labels'] = [index]
        if load_example == "Scientific case: FRB":
            kwargs['_preprocess_function'] = preprocess

        func = explain_ts_dispatcher[method]

        with col:
            with st.spinner(f'Running {method}'):
                explanation = func(serialized_model, ts_data=ts_data_explainer, **kwargs)

            if load_example == "Scientific case: FRB":
                fig, axes = plt.subplots(ncols=2, figsize=(14, 6))
                # FRB: plot original data
                ax = axes[0]
                ax.imshow(ts_data, aspect='auto', origin='lower')
                ax.set_xlabel('Time step')
                ax.set_ylabel('Channel index')
                ax.set_title('Input data')
                # FRB data explanation has to be transposed
                ax = axes[1]
                ax.imshow(explanation[0].T, aspect='auto', origin='lower', cmap='bwr')
                ax.set_xlabel('Time step')
                ax.set_ylabel('Channel index')
                ax.set_title('Explanation')

            else:
                segments = _convert_to_segments(explanation)

                fig, _ = plot_timeseries(range(len(ts_data_explainer[0])), ts_data_explainer[0], segments)

            st.pyplot(fig)

st.stop()
