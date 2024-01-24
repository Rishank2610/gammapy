import pytest
from numpy.testing import assert_allclose
from astropy.coordinates import SkyCoord
from pydantic import ValidationError
from gammapy.datasets import MapDatasetMetaData
from gammapy.utils.metadata import PointingInfoMetaData


def test_meta_default():
    meta = MapDatasetMetaData()
    assert meta.creation.creator.split()[0] == "Gammapy"
    assert meta.instrument is None
    assert meta.event_type is None


def test_mapdataset_metadata():
    position = SkyCoord(83.6287, 22.0147, unit="deg", frame="icrs")
    input = {
        "telescope": "cta-north",
        "instrument": "lst",
        "observation_mode": "wobble",
        "pointing": PointingInfoMetaData(radec_mean=position),
        "obs_ids": 112,
        "optional": dict(test=0.5, other=True),
    }
    meta = MapDatasetMetaData(**input)

    assert meta.telescope == "cta-north"
    assert meta.instrument == "lst"
    assert meta.observation_mode == "wobble"
    assert_allclose(meta.pointing.radec_mean.dec.value, 22.0147)
    assert_allclose(meta.pointing.radec_mean.ra.deg, 83.6287)
    assert meta.obs_ids == "112"
    assert meta.optional["other"] is True
    assert meta.creation.creator.split()[0] == "Gammapy"
    assert meta.event_type is None

    with pytest.raises(ValidationError):
        meta.pointing = 2.0

    input_bad = input.copy()
    input_bad["bad"] = position

    with pytest.raises(ValueError):
        MapDatasetMetaData(**input_bad)


def test_mapdataset_metadata_lists():
    input = {
        "telescope": "cta-north",
        "instrument": "lst",
        "observation_mode": "wobble",
        "pointing": [
            PointingInfoMetaData(
                radec_mean=SkyCoord(83.6287, 22.0147, unit="deg", frame="icrs")
            ),
            PointingInfoMetaData(
                radec_mean=SkyCoord(83.1287, 22.5147, unit="deg", frame="icrs")
            ),
        ],
        "obs_ids": [111, 222],
    }
    meta = MapDatasetMetaData(**input)
    assert meta.telescope == "cta-north"
    assert meta.instrument == "lst"
    assert meta.observation_mode == "wobble"
    assert_allclose(meta.pointing[0].radec_mean.dec.value, 22.0147)
    assert_allclose(meta.pointing[1].radec_mean.ra.deg, 83.1287)
    assert meta.obs_ids == ["111", "222"]
    assert meta.optional is None
    assert meta.event_type is None


def test_mapdataset_metadata_stack():
    input1 = {
        "telescope": "a",
        "instrument": "H.E.S.S.",
        "observation_mode": "wobble",
        "pointing": PointingInfoMetaData(
            radec_mean=SkyCoord(83.6287, 22.5147, unit="deg", frame="icrs")
        ),
        "obs_ids": 111,
        "optional": dict(test=0.5, other=True),
    }

    input2 = {
        "telescope": "b",
        "instrument": "H.E.S.S.",
        "observation_mode": "wobble",
        "pointing": PointingInfoMetaData(
            radec_mean=SkyCoord(83.6287, 22.0147, unit="deg", frame="icrs")
        ),
        "obs_ids": 112,
        "optional": dict(test=0.1, other=False),
    }

    meta1 = MapDatasetMetaData(**input1)
    meta2 = MapDatasetMetaData(**input2)

    meta = meta1.stack(meta2)
    assert meta.telescope == ["a", "b"]
    assert meta.instrument == ["H.E.S.S."]
    assert meta.observation_mode == ["wobble"]
    assert_allclose(meta.pointing[1].radec_mean.dec.deg, 22.0147)
    assert meta.obs_ids == ["111", "112"]
    assert meta.optional["test"] == [0.5, 0.1]
    assert meta.optional["other"] == [True, False]
    assert meta.event_type is None
    assert meta.creation.creator.split()[0] == "Gammapy"


def test_to_header():
    input1 = {
        "telescope": "a",
        "instrument": "H.E.S.S.",
        "observation_mode": "wobble",
        "pointing": PointingInfoMetaData(
            radec_mean=SkyCoord(83.6287, 22.5147, unit="deg", frame="icrs")
        ),
        "obs_ids": 111,
        "optional": dict(test=0.5, other=True),
    }
    meta1 = MapDatasetMetaData(**input1)
    hdr = meta1.to_header()
    assert hdr["INSTRUM"] == "H.E.S.S."
    assert hdr["OBS_IDS"] == "111"
