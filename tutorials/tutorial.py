import numpy as np
import dianna
import dianna.visualization

model = "Some model"
input_data = np.ones((5,  3))

heatmap = dianna.explain(model, input_data, method="SHAP")
dianna.visualization.plot_image(heatmap)
dianna.visualization.plot_image(heatmap, original_data=input_data)
