# Install & Run — SG Jobs Analytics (conda only)

> This guide uses **conda** exclusively. No pip-only, venv, or alternative options.
> Follow the section for your OS: **Linux** or **Windows**.

---

## 0. Prerequisites

- **Miniconda** (or Anaconda) installed.
  - Linux: https://docs.conda.io/en/latest/miniconda.html
  - Windows: https://docs.conda.io/en/latest/miniconda.html
- The dataset file `SGJobData.csv` **or** `SGJobData.csv.zip`.
- The project folder `sg-jobs-analytics/` (the repo you cloned/downloaded).

Verify conda works:

**Linux**
```bash
conda --version
```

**Windows (Anaconda Prompt)**
```bat
conda --version
```

---

## 1. Open a terminal in the project folder

**Linux**
```bash
cd ~/path/to/sg-jobs-analytics
```

**Windows** — open **Anaconda Prompt** (Start Menu → Anaconda Prompt), then:
```bat
cd C:\path\to\sg-jobs-analytics
```

> On Windows, always use **Anaconda Prompt**, not `cmd.exe` or PowerShell, so `conda` is on PATH.

---

## 2. Create and activate the conda environment

**Linux**
```bash
conda create -n sg-jobs python=3.11 -y
conda activate sg-jobs
```

**Windows**
```bat
conda create -n sg-jobs python=3.11 -y
conda activate sg-jobs
```

Confirm the env is active:

**Linux**
```bash
which python
```
Expected: `.../miniconda3/envs/sg-jobs/bin/python`

**Windows**
```bat
where python
```
Expected: `...\miniconda3\envs\sg-jobs\python.exe`

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

Both OSes use the same command — pip runs *inside* the conda env, so packages land in `sg-jobs`.

Verify the key packages:

```bash
python -c "import duckdb, pandas, numpy, plotly, streamlit, matplotlib, seaborn; print('OK')"
```
Expected: `OK`

---

## 4. Put the dataset in place

Place the file inside `data/`:

```
sg-jobs-analytics/
└── data/
    └── SGJobData.csv        (or SGJobData.csv.zip — auto-unzipped by the script)
```

**Linux**
```bash
mkdir -p data
cp /path/to/SGJobData.csv data/
# or: cp /path/to/SGJobData.csv.zip data/
```

**Windows** — either drag-and-drop into `data\`, or:
```bat
mkdir data
copy C:\path\to\SGJobData.csv data\
```

---

## 5. Build the data pipeline (run in order)

All commands below run **inside the activated `sg-jobs` env**, from the project root.

```bash
python scripts/00_extract_data.py          # sample 50k. Add --full for ~1M
python scripts/03_eda_report.py            # prints first-look EDA
python scripts/01_clean_data.py            # applies 16 cleaning rules
python scripts/02_build_duckdb.py          # verifies tables + schema
```

If your CSV is somewhere else:
```bash
python scripts/00_extract_data.py --input /full/path/to/SGJobData.csv
```

Expected: the last line of each script prints a row count, and `data/sg_jobs.duckdb` exists.

---

## 6. (Optional) Run the notebooks

Register the env as a Jupyter kernel **once**, then launch:

```bash
python -m ipykernel install --user --name sg-jobs --display-name "Python (sg-jobs)"
jupyter notebook
```

In the browser, open `notebooks/01_data_cleaning.ipynb` and `notebooks/02_eda.ipynb`. Select kernel **Python (sg-jobs)** from the Kernel menu, then **Run All**.

---

## 7. Launch the Streamlit dashboard

```bash
streamlit run app.py
```

Open the URL Streamlit prints (default **http://localhost:8501**).

If the port is busy:
```bash
streamlit run app.py --server.port 8502
```

Stop the server with **Ctrl+C**.

---

## 8. Deactivate / reset

Deactivate when done:
```bash
conda deactivate
```

Remove the env completely and start over:
```bash
conda env remove -n sg-jobs -y
```
Then repeat from **Step 2**.

---

## 9. Quick reference

| Task | Command |
|---|---|
| Create env | `conda create -n sg-jobs python=3.11 -y` |
| Activate env | `conda activate sg-jobs` |
| Install deps | `pip install -r requirements.txt` |
| Extract + sample | `python scripts/00_extract_data.py` |
| Extract full | `python scripts/00_extract_data.py --full` |
| First-look EDA | `python scripts/03_eda_report.py` |
| Clean data | `python scripts/01_clean_data.py` |
| Verify DB | `python scripts/02_build_duckdb.py` |
| Notebooks | `jupyter notebook` |
| Dashboard | `streamlit run app.py` |
| Deactivate | `conda deactivate` |
| Remove env | `conda env remove -n sg-jobs -y` |

---

## 10. Troubleshooting

**`conda: command not found` (Linux)**
Run `source ~/miniconda3/etc/profile.d/conda.sh` first, or add conda to `~/.bashrc`.

**`'conda' is not recognized` (Windows)**
You are in `cmd`/PowerShell. Use **Anaconda Prompt** instead.

**`python` points to the wrong interpreter**
- Linux: `which python` should be `.../envs/sg-jobs/bin/python`
- Windows: `where python` should be `...\envs\sg-jobs\python.exe`
If not, you forgot `conda activate sg-jobs`.

**`ModuleNotFoundError: duckdb` (or any package)**
The env wasn't active when you ran `pip install`. Activate then reinstall:
```bash
conda activate sg-jobs
pip install -r requirements.txt
```

**Jupyter shows wrong kernel**
Rerun the kernel install line from Step 6, then pick **Python (sg-jobs)** from the Kernel menu.

**Streamlit port 8501 already in use**
`streamlit run app.py --server.port 8502`

**`00_extract_data.py` says "Input not found"**
Either place the file at `data/SGJobData.csv` (or `.zip`) or pass `--input /full/path/to/file`.

**`json_valid(categories)` returns 0 rows**
Your CSV's `categories` column isn't valid JSON. Open `data/raw_jobs_sample.csv`, inspect the column, and adjust `parse_categories` / the SQL snippet in `00_extract_data.py`.