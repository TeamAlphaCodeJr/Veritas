from pathlib import Path
import sys
import pandas as pd

# compiler_service.py
# Reads data/Fake.csv and data/True.csv, adds a 'fake' column (1 for fake, 0 for true),
# concatenates them and writes data/dataset.csv
# Maintains class balance when downsampling and caps the dataset at 10,000 rows.


def build_dataset(max_size: int = 10000, random_state: int = 42):
    base = Path(__file__).resolve().parent
    data_dir = base / "data"
    fake_file = data_dir / "Fake.csv"
    true_file = data_dir / "True.csv"
    out_file = data_dir / "dataset.csv"

    if not fake_file.exists():
        print(f"Missing file: {fake_file}", file=sys.stderr)
        return 1
    if not true_file.exists():
        print(f"Missing file: {true_file}", file=sys.stderr)
        return 1

    df_fake = pd.read_csv(fake_file)
    df_true = pd.read_csv(true_file)

    # add label column
    df_fake["FAKE"] = 1
    df_true["FAKE"] = 0

    total_rows = df_fake.shape[0] + df_true.shape[0]

    if total_rows > max_size:
        # keep classes balanced when downsampling.
        # n_per is the per-class sample size; capped by the smaller class and by half the max_size
        n_per = min(df_fake.shape[0], df_true.shape[0], max_size // 2)
        df_fake = df_fake.sample(n=n_per, random_state=random_state)
        df_true = df_true.sample(n=n_per, random_state=random_state)
        print(f"Downsampled to {2 * n_per} rows (per class: {n_per})")
    else:
        print(f"Keeping all rows (total {total_rows})")

    combined = pd.concat([df_fake, df_true], ignore_index=True, sort=False)
    # shuffle the combined dataset
    combined = combined.sample(frac=1, random_state=random_state).reset_index(drop=True)

    combined.to_csv(out_file, index=False)
    print(f"Wrote {len(combined)} rows to {out_file} (fake={df_fake.shape[0]}, true={df_true.shape[0]})")
    return 0

if __name__ == "__main__":
    raise SystemExit(build_dataset())