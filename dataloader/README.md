
# Standardized Data Transformation


## Data Transfer Tools

This module converts raw trajectory datasets into the NBDT standard format.

### Supported Datasets

- `highD`
- `inD`
- `NGSIM`
- `CitySim`

Set up your Python environment first.

Install the dependencies required by this project before running any transfer scripts.
```
pip intsall -r requirements.txt
```

### Start transfer current dataset into standard

Follow these steps:

1. Go to the `dataloader` directory.

```bash
cd dataloader
```

2. Run the transfer script with CLI arguments.

```bash
python factory.py --dataset highD --data_folder ./original_data --save_folder ./processed_data
```

- `--dataset` (`str`, default: `highD`)
  - Dataset key (case-insensitive): `highD`, `inD`, `ngsim`, `citysim`
- `--data_folder` (`str`, default: `./original_data`)
  - Folder containing raw input files
- `--save_folder` (`str`, default: `./processed_data`)
  - Folder where converted CSV files are written
- `--use_yml` (`str`, default: `./config/config.yaml`)
  - YAML file loaded after CLI parsing; values in YAML override CLI/default values

3. If you prefer configuration files, use YAML from `config`.

```bash
python factory.py --use_yml ./config/config.yaml
```

- Example Config (`config/config.yaml`)

```yaml
dataset: highD
data_folder: ./original_data
save_folder: ./processed_data
```

## Surrogate Safety Measures Calculation



