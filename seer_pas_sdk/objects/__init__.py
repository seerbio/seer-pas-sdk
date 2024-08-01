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
        dilution_factor=None,
        kit_id=None,
        plate_id=None,
        plate_name=None,
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
        self.dilution_factor = dilution_factor
        self.kit_id = kit_id
        self.plate_id = plate_id
        self.plate_name = plate_name

        self.__cols = [
            "MS file name",
            "Sample name",
            "Sample ID",
            "Well location",
            "Nanoparticle",
            "Nanoparticle ID",
            "Control",
            "Control ID",
            "Instrument name",
            "Date sample preparation",
            "Sample volume",
            "Peptide concentration",
            "Peptide mass sample",
            "Dilution factor",
            "Kit ID",
            "Plate ID",
            "Plate Name",
        ]

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
            "dilution_factor",
            "kit_id",
            "plate_id",
            "plate_name",
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

        for i in range(len(self.__attrs)):
            res[self.__cols[i]] = getattr(self, self.__attrs[i])

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
