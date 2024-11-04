# Filter group analysis data for only the POST
class GroupAnalysisPostData:
    """DTO for Group Analysis Saved Results"""

    def __init__(self, data):
        if "post" not in data:
            raise ValueError('Invalid data format. Missing "post" key')

        # Safe check if there are proteins vs peptides
        num_proteins = (
            data["post"]
            .get("protein", {"totalFeature": 0})
            .get("totalFeature", 0)
        )
        num_peptides = (
            data["post"]
            .get("peptide", {"totalFeature": 0})
            .get("totalFeature", 0)
        )

        if num_proteins > 0:
            self.type = "protein"
        elif num_peptides > 0:
            self.type = "peptide"
        else:
            raise ValueError(
                "Invalid data format. No features found in post data"
            )
        self.data = data["post"][self.type]["mergedStats"]
        self.stat_test = data["post"][self.type]["parameters"]["statTest"]
