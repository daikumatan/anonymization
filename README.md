# anonymization for Japanese CSV file

## if you want to use Docker:

### How to install

First of all, please execute `git clone`. then:

```bash
cd anonymization
docker build --no-cache -t csv-anonymizer .
```

### How to use this program with sample data (test_data.csv)

in this case:

- input csv-file name including person's name: `test_data.csv`
- output csv-file name: `result.csv`

```bash
 docker run \                                                        
    -v $(pwd):/app \
    csv-anonymizer \
    --input test_data.csv --output result.csv
```

please change `test_csv.data` and `result.csv` according to your situation.

## if you want to work on your host

### How to install

First of all, please execute `git clone`. then:

```bash
cd anonymization
pyenv install 3.10.13
pyenv global 3.10.13
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### How to use this program with sample data (test_data.csv)

in this case:

- input csv-file name including person's name: `test_data.csv`
- output csv-file name: `result.csv`

```bash
python anonymization_basic.py --input test_data.csv --output result.csv
```

please change `test_csv.data` and `result.csv` according to your situation.
