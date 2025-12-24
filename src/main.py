from argparse import ArgumentParser, ArgumentTypeError
from models.site import Site
import os
import pandas as pd


def csv_file(path: str) -> str:
    if not os.path.exists(path):
        raise ArgumentTypeError(f"File not found: {path}")

    if not path.lower().endswith(".csv"):
        raise ArgumentTypeError(f"Not a csv file: {path}")

    return path


def main(**kwargs):
    if not (sites := kwargs.get("sites")):
        print("No sites source provided.")
        exit(1)

    df_sites = pd.read_csv(sites)
    sites_data = [Site(**record) for record in df_sites.to_dict(orient='records')]
    print(sites_data)


if __name__ == "__main__":
    arg_parser = ArgumentParser(description="Script to match students to sites")
    arg_parser.add_argument(
        "--sites", help="Csv storing the sites", type=csv_file, required=True
    )

    args = arg_parser.parse_args()

    main(sites=args.sites)
