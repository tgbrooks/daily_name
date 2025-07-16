import zipfile
import polars as pl
import pathlib
import json


SOURCE_URL = "https://www.ssa.gov/oact/babynames/names.zip"
SOURCE_PATH = "data/names.zip"
DB_FILE_PATH = "data/counts.sqlite"

# NOTE: we cannot automate the downloading of this file from ssa.gov
# because it appears to deny all requests from python/curl/wget
# but allows it over the browser
## Download the source data from the social security administration
# source_path, msg = urllib.request.urlretrieve(SOURCE_URL, filename=SOURCE_PATH)

# Read in all the source data
# which is in a zipfile containing one cvs file per year of birth (yob)
temp = []
with zipfile.ZipFile(SOURCE_PATH) as source_data:
    for name in source_data.namelist():
        if not name.startswith("yob"):
            # Note a data file (e.g., a ReadMe)
            continue
        yob = int(name.removeprefix("yob").removesuffix(".txt"))
        yob_data = (
            pl.read_csv(
                source_data.open(name),
                has_header=False,
                new_columns=["name", "sex", "count"],
            )
            .with_columns(
                year_of_birth=pl.lit(yob),
                freq=pl.col("count") / pl.col("count").over("sex").sum(),
            )
            .with_columns(rank=1 + pl.int_range(pl.len()).over("sex"))
        )
        temp.append(yob_data)
data = pl.concat(temp)

## Save top names to a sqlite database file
# (
#    data.filter(pl.col("rank") <= 1000).write_database(
#        "counts",
#        connection=f"sqlite:///{DB_FILE_PATH}",
#        if_table_exists="replace",
#    )
# )

# Create separate files for easy use in front-end
start_year = data["year_of_birth"].min()
end_year = data["year_of_birth"].max()
all_years = pl.DataFrame({"year_of_birth": list(range(start_year, end_year + 1))})
name_db = pathlib.Path("data/name_db")
name_db.mkdir(exist_ok=True)
# Take names that were in the top 1000 of any year
top_1000_names = data.filter(pl.col("rank").min().over(["name", "sex"]) <= 1000)
for (name, sex), name_data in top_1000_names.group_by(["name", "sex"]):
    with open(name_db / f"{sex}.{name}.json", "wt") as out:
        json_data = {
            "name": name,
            "sex": sex,
            "freq_by_year": (
                # Expand out to include all years
                name_data.select("year_of_birth", "freq")
                .join(
                    all_years,
                    on="year_of_birth",
                    how="full",
                )
                .fill_null(0)  # make 0 if too rare to be in the database for that year
                .sort("year_of_birth")
            )["freq"].to_list(),
        }
        json.dump(json_data, out)

male_name_list = top_1000_names.filter(sex="M")["name"].unique()
female_name_list = top_1000_names.filter(sex="F")["name"].unique()
pl.DataFrame({"name": male_name_list}).write_csv(
    "data/male_name_list.txt", include_header=False
)
pl.DataFrame({"name": female_name_list}).write_csv(
    "data/female_name_list.txt", include_header=False
)
