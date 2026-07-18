# Student Performance Predictor — End-to-End ML Project

An end-to-end machine learning project that predicts a student's **math score**
from demographic and academic features, served through a Flask web app. The focus
is production-style structure: modular components, a reusable preprocessing
pipeline, custom logging/exception handling, and a trained model exposed behind a
prediction API.

> **Problem:** regression — predict `math_score`.
> **Model:** Ridge regression (scikit-learn).
> **Serving:** Flask app with an HTML form for live predictions.

---

## Features

- **Modular pipeline** split into ingestion, transformation, and training components.
- **Reusable preprocessing** via a scikit-learn `ColumnTransformer`:
  - Numeric features → median imputation + standard scaling.
  - Categorical features → most-frequent imputation + one-hot encoding.
- **Persisted artifacts** — the fitted preprocessor and trained model are saved so
  the web app can serve predictions without retraining.
- **Custom logging & exceptions** — timestamped logs and a `CustomException` that
  reports the exact file and line where an error occurred.
- **Flask serving** — a form-based UI that collects inputs and returns a prediction.

---

## How it works

```
Raw data (student.csv)
        │
        ▼
 Data Ingestion         → reads the dataset, writes raw/train/test CSVs to artifacts/
        │
        ▼
 Data Transformation    → builds & fits a ColumnTransformer (impute + scale + one-hot),
        │                  saves preprocessor.pkl, returns transformed train/test arrays
        ▼
 Model Training         → trains Ridge regression, evaluates R², saves model.pkl
        │
        ▼
 Prediction Pipeline    → loads preprocessor.pkl + model.pkl, transforms a single
                          input row and returns the predicted math score
        │
        ▼
 Flask app (application.py) → serves the prediction pipeline via a web form
```

### Input features

| Feature | Type |
|---------|------|
| `gender` | categorical |
| `race_ethnicity` | categorical |
| `parental_level_of_education` | categorical |
| `lunch` | categorical |
| `test_preparation_course` | categorical |
| `reading_score` | numeric |
| `writing_score` | numeric |

**Target:** `math_score`

---

## Project structure

```
.
├── application.py                 # Flask app entry point
├── setup.py                       # package install config
├── requirements.txt
├── data/
│   └── student.csv                # raw dataset (see note in Setup)
├── src/
│   ├── logger.py                  # timestamped logging setup
│   ├── exception.py               # CustomException with file/line detail
│   ├── utils.py                   # save/load objects, model evaluation helpers
│   ├── components/
│   │   ├── data_ingestion.py      # read data, train/test split
│   │   ├── data_transformation.py # preprocessing ColumnTransformer
│   │   └── model_trainer.py       # train + evaluate Ridge, save model
│   └── pipeline/
│       ├── train_pipeline.py      # runs ingestion → transformation → training
│       └── prediction_pipeline.py # loads artifacts, predicts on new input
├── templates/
│   ├── index.html
│   └── home.html                  # prediction form
└── artifacts/                     # generated model.pkl + preprocessor.pkl
```

---

## Setup

### Prerequisites
- Python 3.10+

### Install

```bash
git clone https://github.com/penzen/mlproject.git
cd mlproject

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -e .                   # installs src as an editable package
```

> **Note:** the raw dataset must be present before running training. Place
> `student.csv` at `data/student.csv` and point `data_ingestion.py` there. The
> dataset is the standard *Students Performance in Exams* set.

---

## Usage

### Train the pipeline

```bash
python -m src.pipeline.train_pipeline
```

This runs ingestion → transformation → training and writes:

```
artifacts/preprocessor.pkl
artifacts/model.pkl
```

### Run the web app

```bash
python application.py
```

Then open `http://127.0.0.1:5000/predictdata`, fill in the form, and submit to get
a predicted math score.

---

## Tech stack

- **ML:** scikit-learn (Ridge, ColumnTransformer, Pipeline), pandas, numpy
- **Serialization:** dill
- **Serving:** Flask, gunicorn (production WSGI server)

---

## Possible extensions

- Compare multiple regressors and select the best by R² (an `evaluate_model`
  helper is already scaffolded in `utils.py`).
- Add hyperparameter tuning (e.g. `GridSearchCV`).
- Containerize with Docker and add a CI workflow for lint + a training smoke test.
