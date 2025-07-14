import numpy as np
import pandas
import scipy
import matplotlib.pyplot as plt
import numpy
from matplotlib import cm


class MeshData:
    def __init__(self, data_file_path: str, variable_name: str):
        try:
            self.data_file = pandas.read_csv(data_file_path)
        except ValueError as error:
            raise Exception(f"{data_file_path} not found. Throwing {error}.")

        self.variable_name = variable_name
        self.x_coordinate = numpy.array(self.data_file["x"])
        self.y_coordinate = numpy.array(self.data_file["y"])
        self.z_coordinate = numpy.array(self.data_file["z"])
        self.metric_variable_data = numpy.array(self.data_file[self.variable_name])

    def interpolate(self):
        interpolator = scipy.interpolate.Rbf(
            self.x_coordinate,
            self.y_coordinate,
            self.z_coordinate,
            self.metric_variable_data,
        )
        return interpolator


class CalculateDiscrepancyMatrix:
    def __init__(self, amr: MeshData, amr_with_mesh_amalgamation: MeshData):
        self.amr = amr
        self.amr_with_mesh_amalgamation = amr_with_mesh_amalgamation
        self.amr_rbf = self.amr.interpolate()  # amr mapping
        self.amr_with_mesh_amalgamation_rbf = (
            self.amr_with_mesh_amalgamation.interpolate()
        )  # mesh amalgamation mapping

    def get_discrepancy_matrix(self, x, y, z):
        amr = self.amr_rbf(x, y, z)
        mesh_amalgamation = self.amr_with_mesh_amalgamation_rbf(x, y, z)
        return (amr - mesh_amalgamation) / amr

    def plot_data(self, project_random_point=True, n_points=1000):
        cmap = cm.viridis
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        if project_random_point:
            x_ = np.random.uniform(
                np.min(self.amr.x_coordinate), np.max(self.amr.x_coordinate), n_points
            )
            y_ = np.random.uniform(
                np.min(self.amr.y_coordinate), np.max(self.amr.y_coordinate), n_points
            )
            z_ = np.random.uniform(
                np.min(self.amr.z_coordinate), np.max(self.amr.z_coordinate), n_points
            )
        else:
            x_ = self.amr.x_coordinate
            y_ = self.amr.y_coordinate
            z_ = self.amr.z_coordinate

        value = self.get_discrepancy_matrix(x_, y_, z_)

        sc = ax.scatter(x_, y_, z_, c=value, cmap="viridis", linewidth=0)

        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        ax.set_zlabel("Z-axis")

        cbar = fig.colorbar(
            sc, aspect=10, label=f"{self.amr.variable_name}_discrepancy"
        )

        plt.show()

    def plot_partial_sample(self, x_dim, y_dim, z_dim, n_points=1000):

        cmap = cm.viridis
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        x_ = np.random.uniform(x_dim[0], x_dim[1], n_points)
        y_ = np.random.uniform(y_dim[0], y_dim[1], n_points)
        z_ = np.random.uniform(z_dim[0], z_dim[1], n_points)

        value = self.get_discrepancy_matrix(x_, y_, z_)

        sc = ax.scatter(x_, y_, z_, c=value, cmap="viridis", linewidth=0)

        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        ax.set_zlabel("Z-axis")

        cbar = fig.colorbar(
            sc, aspect=10, label=f"{self.amr.variable_name}_discrepancy"
        )

        plt.show()
