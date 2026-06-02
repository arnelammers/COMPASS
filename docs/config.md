# Workflow configuration

The workflow is configured via a YAML file located at `config/config.yaml`.

---

## Example

```yaml
datasets:
  easvolee_pos:
    mzmine:
      template: "dda_orbitrap_pos"
      retention_time_range: [0.5, 31]
      approximate_feature_fwhm: 0.1
      minimum_feature_height: 5e4
      blank_subtraction:
        min_blank_presence: 3
        fold_change_threshold: 3
      spectral_library_files:
        - "msnlib/20250828_targetmol_hts_np_pos_ms2.json"
        - "msnlib/20241003_mcebio_pos_ms2.json"
        - "msnlib/20241003_otavapep_pos_ms2.json"
        - "msnlib/20241003_enamdisc_pos_ms2.json"
        - "msnlib/20241003_nihnp_pos_ms2.json"
        - "msnlib/20241003_mcescaf_pos_ms2.json"
        - "msnlib/20241003_mcedrug_pos_ms2.json"
        - "msnlib/20241003_enammol_pos_ms2.json"
        - "msnlib/20250828_mcediv_50k_sub_pos_ms2.json"
spectral_libraries:
  msnlib:
    zenodo_id: 16984129
```

---

## `datasets`

A map of datasets to process. Each key must match a subfolder name under `data/`.

### `mzmine`

MZmine processing settings for a dataset.

| Field | Type | Description |
|---|---|---|
| `template` | string | Name of the MZmine batch template to use as a base, currently only `dda_orbitrap_pos` is supported |
| `retention_time_range` | [number, number] | Start and end of the retention time window to process, in minutes. |
| `approximate_feature_fwhm` | number | Estimated peak width at half maximum, used to tune peak detection. |
| `minimum_feature_height` | number | Minimum intensity for a feature to be detected. |
| `blank_subtraction` | object | Settings for filtering out background signals (see below). |
| `spectral_library_files` | string[] | Library files to use for annotation. Must be formatted as `{collection}/{filename}.json`, where `collection` matches a key in `spectral_libraries`. |

### `blank_subtraction`

| Field | Type | Description |
|---|---|---|
| `min_blank_presence` | integer | Minimum number of blanks in which a feature must appear to be considered background. |
| `fold_change_threshold` | number | Minimum fold-change between sample and blank intensity for a feature to be retained. |

---

## `spectral_libraries`

A map of named spectral library sources. Each key becomes a collection name that can be referenced in `spectral_library_files`.

| Field | Type | Description |
|---|---|---|
| `zenodo_id` | integer | Zenodo record ID for this library. Used to download the library files. |
