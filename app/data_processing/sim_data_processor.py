import json
import os
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import scipy.stats as stats
import imageio

from data_processing.data_processor import DataProcessor
from regression_toolbox.model import Model
from matplotlib import pyplot as plt
from numpyencoder import NumpyEncoder
from sklearn.model_selection import train_test_split
from visualisation_toolbox.domain import Domain


class SimDataProcessor(DataProcessor):
    """
    A class to simulate data for the Bayesian Inference tool.
    It's a subclass of DataProcessor.
    This class generates data using an analytical model within a specified domain using the processor parameters.
    The processed data are saved as a csv file.
    The construction (configuration) parameters are saved as a json file.

    Args:
        - processed_data_name (str): The name of the simulated data. This will indicate the name of the folder where the data is saved within the data directory, and the name of the folder where the inference results will be saved in the results directory.
        - model (Model): The model used for data simulation.
        - domain (Domain): The domain used for data simulation.
        - train_test_split (float, optional): Ratio of training to test data. Defaults to 0.8.
        - noise_dist (str, optional): The distribution of noise. Defaults to 'no_noise'. Options are:
            - 'gaussian': Gaussian noise. Takes the noise_level as the standard deviation of the Gaussian distribution.
            - 'no_noise': No noise.
            - Add more noise distributions as needed.
        - noise_level (float, optional): The level of noise of the simulated data. Defaults to None. Can be used interchangeably with noise_percentage.
        - noise_percentage (float, optional): The percentage of noise of the simulated data reletive to the predicted values of the model. Defaults to None. Can be used interchangeably with noise_level.
        - data_path (str, optional): The path to save the simulated data. Defaults to '/data'.
        - plot_data (bool, optional): Whether to plot the simulated data. Defaults to True.

    Attributes:
        - processed_data_name (str): The name of the simulated data. This indicates the name of the folder where the data is saved within the data directory, and the name of the folder where the inference results are saved in the results directory.
        - model (Model): The model used for data simulation.
        - domain (Domain): The domain used for data simulation.
        - train_test_split (float): Ratio of training to test data.
        - noise_dist (str): The distribution of noise. Defaults to 'no_noise'.
        - noise_level (float): The level of noise. Can be used interchangeably with noise_percentage.
        - noise_percentage (float): The percentage of noise reletive to the predicted values of the model. Can be used interchangeably with noise_level.
        - simulated_data (pd.DataFrame): The simulated data.
        - data_path (str): The root data path.
        - plot_data (bool): Whether to plot the simulated
        - dependent_variable (str): The dependent variable of the model.
        - independent_variables (list): The independent variables of the model.

    """

    def __init__(self,
                 processed_data_name: str,
                 model: Model,
                 domain: Domain,
                 train_test_split: float = 0.8,
                 noise_dist='no_noise',
                 noise_level=None,
                 noise_percentage=None,
                 data_path='/data',
                 plot_data=True):

        super().__init__(processed_data_name, None,
                         train_test_split, data_path)
        """
        Initialises the SimDataProcess class.

        Args:
            - processed_data_name (str): The name of the simulated data. This will indicate the name of the folder where the data is saved within the data directory, and the name of the folder where the inference results will be saved in the results directory.
            - model (Model): The model used for data simulation.
            - domain (Domain): The domain used for data simulation.
            - train_test_split (float, optional): Ratio of training to test data. Defaults to 0.8.
            - noise_dist (str, optional): The distribution of noise. Defaults to 'no_noise'. Options are:
                - 'gaussian': Gaussian noise. Takes the noise_level as the standard deviation of the Gaussian distribution.
                - 'truncate_gaussian': Truncated Gaussian noise. Takes the noise_level as the standard deviation of the Gaussian distribution.
                - 'no_noise': No noise.
            - noise_level (float, optional): The level of noise. Defaults to None. Can be used interchangeably with noise_percentage.
            - noise_percentage (float, optional): The percentage of noise reletive to the predicted values of the model. Defaults to None. Can be used interchangeably with noise_level.
            - data_path (str, optional): The path to save the simulated data. Defaults to '/PhD_project/data/'.
            - plot_data (bool, optional): Whether to plot the simulated data. Defaults to True.

        """

        self.model = model
        self.domain = domain
        self.noise_dist = noise_dist
        self.noise_level = noise_level
        self.noise_percentage = noise_percentage
        self.plot_data = plot_data
        self.dependent_variable = model.dependent_variable
        self.independent_variables = model.independent_variables

        if self.noise_dist == 'no_noise':
            if self.noise_level is not None or self.noise_percentage is not None:
                raise ValueError('SimDataProcess - noise_level and noise_percentage must be None when noise_dist is "no_noise"')
        else:
            if (self.noise_level is None and self.noise_percentage is None) or (self.noise_level is not None and self.noise_percentage is not None):
                raise ValueError('SimDataProcess - either noise_level or noise_percentage must be specified, but not both, when noise_dist is not "no_noise"')

    def get_construction(self) -> dict:
        """
        Gets the construction parameters.
        The construction parameters includes all of the config information used to simulate the data.
        This checks if the simulated data already exists. It includes:
        - processed_data_name: The name of the processed data.
        - noise_dist: The distribution of noise.
        - noise_level: The level of noise.
        - noise_percentage: The percentage of noise.
        - train_test_split: Ratio of training to test data.
        - model_params: The parameters for the model.
        - domain_params: The parameters for the domain.

        Returns:
            - dict: The construction parameters.
        """
        construction = {
            'processed_data_name': self.processed_data_name,
            'noise_dist': self.noise_dist,
            'noise_level': self.noise_level,
            'noise_percentage': self.noise_percentage,
            'train_test_split': self.train_test_split,
        }
        construction['model_params'] = {}
        construction['domain_params'] = {}
        construction['model_params'] = self.model.get_construction()
        construction['domain_params'] = self.domain.get_construction()

        return construction

    def _check_data_exists(self):
        """
        Check if the simulated data already exists.

        Returns:
            - bool: True if the data exists, False otherwise.

        Raises:
            - FileNotFoundError: If the construction.json file is not found.
            - Exception: Mismatched construction.json vs simulator parameters.
        """

        data_filepath = self.data_path + '/processed_sim_data/' + \
            self.processed_data_name
        if not os.path.exists(data_filepath):
            return False
        else:
            try:
                with open(data_filepath + '/construction.json', 'r') as f:
                    construction_data = json.load(f)
                    
            except:
                raise FileNotFoundError(
                    'SimDataProcessor - construction.json file not found')

            if construction_data == self.get_construction():
                return True
            else:
                raise Exception(
                    'SimDataProcessor - construction.json file under the data_name ' + self.processed_data_name + ' does not match simulator parameters')

    def _save_data(self, simulated_data):
        """
        Save simulated data as a csv file.
        Save the construction parameters as a json file.

        Args:
            - simulated_data (pd.DataFrame): The simulated data.
        """

        data_file_path = self.data_path + '/processed_sim_data/' + \
            self.processed_data_name
        if not os.path.exists(data_file_path):
            os.makedirs(data_file_path)
        simulated_data.to_csv(data_file_path + '/data.csv')
        with open(data_file_path + '/construction.json', 'w') as f:
            json.dump(self.get_construction(), f, cls=NumpyEncoder,
                      separators=(', ', ': '), indent=4)
        print('Data generated and saved to ' + data_file_path)

    def process_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Simulate the data based on the given model and domain.
        If data has already been simulated, loads the data.
        Saves the simulated data as a csv file.

        Returns:
            - tuple: A tuple containing the training data and test data.
        """

        if self.domain.points is None:
            raise ValueError('SimDataProcessor - domain has not been built, run domain.build_domain outside of the processor')

        points = self.domain.points
        if self.domain.time_array is not None:
            points = self.domain._add_time_to_points()

        model_func = self.model.get_model()
        if not all(self.independent_variables == points.columns):
            raise ValueError('SimDataProcessor - The domain points do not match the model independent variables')

        if not self._check_data_exists():
            mu = model_func(pd.Series({}), points)
            if self.noise_percentage is not None:
                vec_noise = self.noise_percentage*mu
            else:
                if self.noise_level is not None:
                    vec_noise = self.noise_level*np.ones(mu.size)
            if self.noise_dist == 'gaussian':
                C = np.array([mu[i] + vec_noise[i]**2*np.random.normal() for i in range(mu.size)])
            elif self.noise_dist == 'truncate_gaussian':
                C = np.array([mu[i] + vec_noise[i]*stats.truncnorm.rvs(0, np.inf) for i in range(mu.size)])
            elif self.noise_dist == 'no_noise':
                C = mu
            else:
                raise Exception('SimDataProcess - Noise distribution invalid!')

            data = points.copy()
            data[self.model.dependent_variable] = C
            data[self.model.dependent_variable + '_true'] = mu
            data.replace([np.inf, -np.inf], np.nan, inplace=True)
            data.dropna(inplace=True)
            self.processed_data = data
            self._save_data(self.processed_data)
        else:
            data_path = self.data_path + '/processed_sim_data/' + \
                self.processed_data_name
            self.processed_data = pd.read_csv(data_path + '/data.csv')
            print('Data loaded from ' + data_path)

        if self.plot_data:
            self.plot_sim_data()
        
        if self.train_test_split == 1:
            return self.processed_data, self.processed_data

        else:
            return train_test_split(
            self.processed_data,
            test_size=1 - self.train_test_split,
            random_state=42)

    def plot_sim_data(self):
        """
        This function plots the simulated data.
        It saves static plots for non-time-varying data and animated GIFs for time-varying data.
        Supported data: 1D, 2D, and 3D.
        """
        file_path = self.data_path + '/processed_sim_data/' + self.processed_data_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        full_static_path = file_path + '/data_plot.png'
        full_gif_path = file_path + '/data_plot.gif'

        # **Handle Static Plots (No Time Dependency)**
        title = f"Simulated {self.model.dependent_variable} Data"
        if self.domain.time_array is None:
            if not os.path.exists(full_static_path):

                if self.domain.n_dims == 1:
                    fig, ax = plt.subplots()
                    ax.scatter(self.processed_data[self.model.independent_variables[0]],
                            self.processed_data[self.model.dependent_variable], label='Simulated Data', s=10)
                    ax.plot(self.processed_data[self.model.independent_variables[0]],
                            self.processed_data[self.model.dependent_variable + '_true'],
                            label='Simulated Data No Noise', color='red')
                    ax.set_xlabel(self.model.independent_variables[0])
                    ax.set_ylabel(self.model.dependent_variable)
                    ax.set_title(title)
                    ax.legend()
                    fig.savefig(full_static_path)
                    plt.close()

                elif self.domain.n_dims == 2:
                    fig = plt.figure(figsize=(7, 8))
                    gs = gridspec.GridSpec(2, 1, height_ratios=[5, 0.2])
                    ax = fig.add_subplot(gs[0])

                    sc = ax.scatter(self.processed_data[self.model.independent_variables[0]],
                                    self.processed_data[self.model.independent_variables[1]],
                                    c=self.processed_data[self.model.dependent_variable],
                                    cmap='viridis', s=10, vmin=np.percentile(self.processed_data[self.model.dependent_variable], 5),
                                    vmax=np.percentile(self.processed_data[self.model.dependent_variable], 95))
                    ax.set_xlabel(self.model.independent_variables[0])
                    ax.set_ylabel(self.model.independent_variables[1])
                    ax.set_title(title)

                    cbar_ax = fig.add_subplot(gs[1])
                    fig.colorbar(sc, cax=cbar_ax, orientation='horizontal')
                    cbar_ax.set_xlabel(self.model.dependent_variable)
                    fig.tight_layout()
                    fig.savefig(full_static_path)
                    plt.close()

                elif self.domain.n_dims == 3:
                    fig = plt.figure(figsize=(7, 8))
                    gs = gridspec.GridSpec(2, 1, height_ratios=[5, 0.2])
                    ax = fig.add_subplot(gs[0], projection='3d')

                    sc = ax.scatter(self.processed_data[self.model.independent_variables[0]],
                                    self.processed_data[self.model.independent_variables[1]],
                                    self.processed_data[self.model.independent_variables[2]],
                                    c=self.processed_data[self.model.dependent_variable],
                                    cmap='viridis', s=10, vmin=np.percentile(self.processed_data[self.model.dependent_variable], 5),
                                    vmax=np.percentile(self.processed_data[self.model.dependent_variable], 95))
                    ax.set_xlabel(self.model.independent_variables[0])
                    ax.set_ylabel(self.model.independent_variables[1])
                    ax.set_zlabel(self.model.independent_variables[2])
                    ax.set_title(title)

                    cbar_ax = fig.add_subplot(gs[1])
                    fig.colorbar(sc, cax=cbar_ax, orientation='horizontal')
                    fig.tight_layout()
                    fig.savefig(full_static_path)
                    plt.close()

        # **Handle Animated GIFs for Time-Varying Data**
        elif self.domain.time_array is not None:
            if not os.path.exists(full_gif_path):
                if 't' not in self.processed_data.columns:
                    raise ValueError('SimDataProcessor - Time range not found in the data')

                images = []
                time_values = np.sort(self.processed_data['t'].unique())  # Ensure frames are ordered
                frame_files = []  # Track frame files for cleanup

                vmin = np.percentile(self.processed_data[self.model.dependent_variable], 5)
                vmax = np.percentile(self.processed_data[self.model.dependent_variable], 95)

                for t in time_values:
                    frame_data = self.processed_data[self.processed_data['t'] == t]

                    fig = plt.figure(figsize=(6, 5))

                    if self.domain.n_dims == 1:
                        ax = fig.add_subplot(111)
                        ax.scatter(frame_data[self.model.independent_variables[0]],
                                frame_data[self.model.dependent_variable], label='Simulated Data', s=10)
                        ax.plot(frame_data[self.model.independent_variables[0]],
                                frame_data[self.model.dependent_variable + '_true'], label='True Data', color='red')
                        ax.set_xlabel(self.model.independent_variables[0])
                        ax.set_ylabel(self.model.dependent_variable)
                        ax.set_title(f"{title} (t = {t})")
                        ax.legend(loc = 'upper right')
                        ax.grid(True)

                    elif self.domain.n_dims == 2:
                        ax = fig.add_subplot(111)
                        sc = ax.scatter(frame_data[self.model.independent_variables[0]],
                                        frame_data[self.model.independent_variables[1]],
                                        c=frame_data[self.model.dependent_variable], cmap='viridis', s=10,
                                        vmin=vmin, vmax=vmax)
                        ax.set_xlabel(self.model.independent_variables[0])
                        ax.set_ylabel(self.model.independent_variables[1])
                        ax.set_title(f"{title} (t = {t})")
                        plt.colorbar(sc, ax=ax, orientation='vertical')

                    elif self.domain.n_dims == 3:
                        ax = fig.add_subplot(111, projection='3d')
                        sc = ax.scatter(frame_data[self.model.independent_variables[0]],
                                        frame_data[self.model.independent_variables[1]],
                                        frame_data[self.model.independent_variables[2]],
                                        c=frame_data[self.model.dependent_variable], cmap='viridis', s=10,
                                        vmin=vmin, vmax=vmax)
                        ax.set_xlabel(self.model.independent_variables[0])
                        ax.set_ylabel(self.model.independent_variables[1])
                        ax.set_zlabel(self.model.independent_variables[2])
                        ax.set_title(f"{title} (t = {t})")
                        plt.colorbar(sc, ax=ax, orientation='vertical')

                    frame_filename = file_path + f'/frame_{t}.png'
                    fig.savefig(frame_filename)
                    frame_files.append(frame_filename)
                    images.append(imageio.imread(frame_filename))
                    plt.close(fig)

                # Save as looping GIF
                imageio.mimsave(full_gif_path, images, fps=1, loop=0)

                # Cleanup temporary frame images
                for frame_filename in frame_files:
                    os.remove(frame_filename)

        else:
            raise ValueError('SimDataProcessor - Data dimensionality not supported')

        print(f"Plot saved at: {file_path}")

