import numpy as np
import json
import pandas as pd
from typing import List as _List, Dict as _Dict
from .groupanalysis import GroupAnalysisPostData


class VolcanoPlotSettings:
    """Class to hold the settings information for the Volcano Plot"""

    def __init__(
        self,
        significance_threshold: float = 0.05,
        fold_change_threshold: float = 1,
        label_by: str = "fold_change",
    ):
        """Initialize the VolcanoPlotSettings object

        Args:
            significance_threshold (float, optional): Cutoff value for the p-value to determine significance. Defaults to 0.05.
            fold_change_threshold (float, optional): Cutoff value for the fold change to determine significance. Defaults to 1.
            label_by (str, optional): Metric to sort result data. Defaults to "fold_change".

        Raises:
            ValueError: "Invalid label_by value, must be one of ['euclidean', 'fold_change', 'significance']"
        """
        if label_by not in ["euclidean", "fold_change", "significance"]:
            raise ValueError(
                "Invalid label_by value, must be one of ['euclidean', 'fold_change', 'significance']"
            )
        self.significance_threshold = significance_threshold
        self.fold_change_threshold = fold_change_threshold
        self.label_by = label_by

    @property
    def values(self):
        return {
            "significance_threshold": self.significance_threshold,
            "fold_change_threshold": self.fold_change_threshold,
            "label_by": self.label_by,
        }

    @classmethod
    def get_settings(cls):
        return [
            "significance_threshold",
            "fold_change_threshold",
            "label_by",
        ]

    @classmethod
    def get_label_by_map(cls):
        return dict(
            euclidean="euclideanDistance",
            fold_change="logFD",
            significance="negativeLog10P",
        )


class VolcanoPlotBuilder:
    """
    Builder class for the Volcano Plot
    Can be used to reuse the same GroupAnalysisResults data to build multiple Volcano Plots with different settings.

    """

    PROTEIN_GROUP_INDEX = "pg"
    PEPTIDE_INDEX = "peptide"

    def __init__(
        self,
        data: _List[_Dict],
        significance_threshold: float = 0.05,
        fold_change_threshold: float = 1,
        label_by: str = "fold_change",
    ):
        """Initialize the VolcanoPlotBuilder object

        Args:
            data (list[dict]): The complete set of group analysis result data
            significance_threshold (float, optional): Cutoff value for the p-value to determine significance. Defaults to 0.05.
            fold_change_threshold (float, optional): Cutoff value for the fold change to determine significance. Defaults to 1.
            label_by (str, optional): Metric to sort result data. Defaults to "fold_change".

        Raises:
            ValueError: "Invalid label_by value, must be one of ['euclidean', 'fold_change', 'significance']"

        Returns:
            None
        """

        self.settings = VolcanoPlotSettings(
            significance_threshold=significance_threshold,
            fold_change_threshold=fold_change_threshold,
            label_by=label_by,
        )

        parsed_data = GroupAnalysisPostData(data)

        self.type = parsed_data.type
        self.stat_test = parsed_data.stat_test
        self.data = parsed_data.data
        self.minusLog10PSigValue = -np.log10(
            self.settings.significance_threshold
        )
        self.sort_param = VolcanoPlotSettings.get_label_by_map()[
            self.settings.label_by
        ]
        self.max_logFD, self.max_negative_log10_p = self._get_max_values(
            self.data
        )
        self.protein_gene_map = dict()
        self.feature_type_index = (
            self.PROTEIN_GROUP_INDEX
            if self.type == "protein"
            else self.PEPTIDE_INDEX
        )
        self.volcano_plot = self.build()

    def build(self):
        """Build the volcano plot

        Returns:
            list[dict]: sorted volcano plot data
        """
        result = []
        for i, row in enumerate(self.data):
            result.append(self.build_row(i, row))
        sorted_result = sorted(
            result,
            key=lambda x: (
                x[self.sort_param]
                if self.sort_param != "logFD"
                else np.abs(x[self.sort_param])
            ),
            reverse=True,
        )
        return sorted_result

    def build_row(self, i, data):
        """Build a row for the volcano plot

        Args:
            i (int): The index of the row
            data (dict): a group analysis result entry

        Returns:
            dict: The row data
        """
        self.protein_gene_map[data[self.feature_type_index]] = data["gene"]

        row = dict(
            logFD=data["logFD"],
            negativeLog10P=data["negativeLog10P"],
            dataIndex=i,
            rowID=json.dumps(data),
            gene=data["gene"],
            group=self.get_contrast_group_string(data),
            significant=self.get_significance_class(data),
            euclideanDistance=self.calculate_euclidean_distance(
                data["logFD"] / self.max_logFD,
                data["negativeLog10P"] / self.max_negative_log10_p,
            ),
        )
        row[self.type] = data[self.feature_type_index]
        return row

    def is_significant_point(self, data):
        return (
            data["negativeLog10P"] >= self.minusLog10PSigValue
            and np.abs(data["logFD"]) >= self.settings.fold_change_threshold
        )

    def get_significance_class(self, data):
        """Get the significance class

        Args:
            data (dict): the row data

        Returns:
            int: 0 if not significant, 1 if (logFD >= 1), -1 if (logFD <= -1)
        """
        if not self.is_significant_point(data):
            return 0
        elif data["logFD"] >= 1:
            return 1
        elif data["logFD"] <= -1:
            return -1

    def get_contrast_group_string(self, obj):
        """Get the contrast group string

        Args:
            obj (dict): The row data

        Returns:
            str: The contrast group string
        """
        if (
            obj
            and obj.get("contrastGroup", None)
            and obj["contrastGroup"].get("G1", None)
            and obj["contrastGroup"].get("G2", None)
        ):
            return "/".join(
                [obj["contrastGroup"]["G1"], obj["contrastGroup"]["G2"]]
            )

    def calculate_euclidean_distance(self, x, y):
        """Calculate the euclidean distance

        Args:
            x (float): The x value
            y (float): The y value

        Returns:
            float: The euclidean distance
        """
        return np.sqrt(x**2 + y**2)

    def _get_max_values(self, data):
        """For euclidean distance, get the max logFD and negativeLog10P values to normalize the data

        Args:
            data (list[dict]): The complete set of group analysis result data

        Returns:
            tuple: The max logFD and negativeLog10P values.
        """
        max_logFD = -np.inf
        max_negative_log10_p = -np.inf
        for row in data:
            max_logFD = max(max_logFD, row["logFD"])
            max_negative_log10_p = max(
                max_negative_log10_p, row["negativeLog10P"]
            )
        return max_logFD, max_negative_log10_p

    def update(
        self,
        significance_threshold=None,
        fold_change_threshold=None,
        label_by=None,
    ):
        """Updates the settings and recalculates the volcano plot

        Args:
            significance_threshold (float, optional): Cutoff value for the p-value to determine significance
            fold_change_threshold (float, optional): Cutoff value for the fold change to determine significance
            label_by (str, optional): Metric to sort result data

        Raises:
            ValueError: "Invalid label_by value, must be one of ['euclidean', 'fold_change', 'significance']"

        Returns:
            None
        """
        if not significance_threshold:
            significance_threshold = self.settings.significance_threshold
        if not fold_change_threshold:
            fold_change_threshold = self.settings.fold_change_threshold
        if not label_by:
            label_by = self.settings.label_by

        self.settings = VolcanoPlotSettings(
            significance_threshold=significance_threshold,
            fold_change_threshold=fold_change_threshold,
            label_by=label_by,
        )
        self.minusLog10PSigValue = -np.log10(
            self.settings.significance_threshold
        )
        self.sort_param = VolcanoPlotSettings.get_label_by_map()[
            self.settings.label_by
        ]
        self.volcano_plot = self.build()

    def to_df(self):
        """Convert the volcano plot data to a DataFrame"""
        return pd.DataFrame(self.volcano_plot)

    def get_significant_rows(self):
        """Get the significant proteins

        Returns:
            List: The list of significant proteins
        """
        return [
            row[self.type] for row in self.volcano_plot if row["significant"]
        ]
