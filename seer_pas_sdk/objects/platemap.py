import pandas as pd


class PlateMap:
    """
    Plate map object containing information about samples and corresponding MS data files.
    """

    def __init__(
        self,
        ms_file_name=None,
        sample_name=None,
        sample_id=None,
        well_location=None,
        nanoparticle=None,
        nanoparticle_id=None,
        control=None,
        control_id=None,
        instrument_name=None,
        date_sample_preparation=None,
        sample_volume=None,
        peptide_concentration=None,
        peptide_mass_sample=None,
        recon_volume=None,
        dilution_factor=None,
        kit_id=None,
        plate_id=None,
        plate_name=None,
        assay_version=None,
        sample_tube_id=None,
        method_set_id=None,
        assay_method_id=None,
        product="XT",
    ):

        if not ms_file_name:
            raise ValueError("MS file name(s) must be provided.")

        self.ms_file_name = ms_file_name
        self.length = len(ms_file_name)

        self.sample_name = sample_name
        self.sample_id = sample_id
        self.well_location = well_location
        self.nanoparticle = nanoparticle
        self.nanoparticle_id = nanoparticle_id
        self.control = control
        self.control_id = control_id
        self.instrument_name = instrument_name
        self.date_sample_preparation = date_sample_preparation
        self.sample_volume = sample_volume
        self.peptide_concentration = peptide_concentration
        self.peptide_mass_sample = peptide_mass_sample
        self.recon_volume = recon_volume
        self.dilution_factor = dilution_factor
        self.kit_id = kit_id
        self.plate_id = plate_id
        self.plate_name = plate_name
        self.assay_version = assay_version
        self.sample_tube_id = sample_tube_id
        self.method_set_id = method_set_id
        self.assay_method_id = assay_method_id
        self.product = product

        if self.product == "XT":
            self.__map = {
                "ms_file_name": "MS file name",
                "sample_name": "Sample name",
                "sample_id": "Sample ID",
                "well_location": "Well location",
                "nanoparticle": "Nanoparticle",
                "nanoparticle_id": "Nanoparticle ID",
                "control": "Control",
                "control_id": "Control ID",
                "instrument_name": "Instrument name",
                "date_sample_preparation": "Date sample preparation",
                "sample_volume": "Sample volume",
                "peptide_concentration": "Peptide concentration",
                "peptide_mass_sample": "Peptide mass sample",
                "recon_volume": "Recon volume",
                "dilution_factor": "Dilution factor",
                "kit_id": "Kit ID",
                "plate_id": "Plate ID",
                "plate_name": "Plate Name",
                "assay_version": "Assay",
            }
        else:
            self.__map = {
                "ms_file_name": "MS file name",
                "sample_name": "Sample name",
                "sample_id": "Sample ID",
                "well_location": "Well location",
                "nanoparticle": "Nanoparticle set",
                "nanoparticle_id": "Nanoparticle set ID",
                "control_id": "Control ID",
                "instrument_name": "Instrument ID",
                "date_sample_preparation": "Date assay initiated",
                "sample_volume": "Sample volume",
                "peptide_concentration": "Reconstituted peptide concentration",
                "peptide_mass_sample": "Recovered peptide mass",
                "recon_volume": "Reconstitution volume",
                "plate_id": "Plate ID",
                "plate_name": "Plate Name",
                "assay_version": "Assay product",
                "sample_tube_id": "Sample tube ID",
                "method_set_id": "Method set ID",
                "assay_method_id": "Assay method ID",
            }

        self.__attrs = [
            "ms_file_name",
            "sample_name",
            "sample_id",
            "well_location",
            "nanoparticle",
            "nanoparticle_id",
            "control",
            "control_id",
            "instrument_name",
            "date_sample_preparation",
            "sample_volume",
            "peptide_concentration",
            "peptide_mass_sample",
            "recon_volume",
            "dilution_factor",
            "kit_id",
            "plate_id",
            "plate_name",
            "assay_version",
            "sample_tube_id",
            "method_set_id",
            "assay_method_id",
        ]

        for attr in self.__attrs:
            if not getattr(self, attr):
                # Replace falsey values with empty lists
                setattr(self, attr, [])

            attr_len = len(getattr(self, attr))

            if attr_len > self.length:
                raise ValueError(
                    "Parameter lengths must not exceed the number of MS files."
                )

            elif attr_len < self.length:
                for i in range(self.length - attr_len):
                    getattr(self, attr).append(None)

    def to_dict(self):
        res = {}

        supported_cols = self.__map.keys()

        for attr in self.__attrs:
            if attr in supported_cols:
                res[self.__map[attr]] = getattr(self, attr)

        for entry in res:
            res[entry] = {i: res[entry][i] for i in range(len(res[entry]))}

        return res

    def to_df(self):
        return pd.DataFrame(self.to_dict())

    def to_csv(self, path=None):
        if not path:
            return self.to_df().to_csv(index=False)
        return self.to_df().to_csv(path_or_buf=path, index=False)

    def __repr__(self):
        return str(self.to_dict())
