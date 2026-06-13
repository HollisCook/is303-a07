'''
Country Data Analysis Pipeline

Inputs: https://api.restcountries.com/countries/v5
Processes: scrape country data, store in SQLite via Peewee,
           query and analyze with Pandas, create population chart
Outputs: printed analysis, population_by_region.png, countries.db
'''


import requests
from peewee import SqliteDatabase, Model, CharField, FloatField, IntegerField
import pandas as pd
import matplotlib.pyplot as plt
import time
import json

# ─── DATABASE SETUP ──────────────────────────────────────────────

db = SqliteDatabase("countries.db")

class Country(Model):
    name = CharField(unique=True)
    population = IntegerField()
    area = FloatField()
    region = CharField()

    class Meta():
        database = db 

    def __str__(self):
        return f'{self.name} | {self.area} | {self.region} | {self.population}'

# ─── SCRAPING FUNCTIONS ──────────────────────────────────────────

def fetch_countries():
    API_KEY = "rc_live_126246323bd54068892aa9cc5a062fc8"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    url_base = "https://api.restcountries.com/countries/v5"
    all_countries = []
    offset = 0

    while True:
        params = {"limit": 100, "offset": offset}
        response = requests.get(url_base, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            countries = data["data"]["objects"]
            all_countries = all_countries + countries
            if data["data"]["meta"]["more"] == False:
                break
            offset = offset + 100
        else:
            print("Something went wrong fetching countries")
            break

        time.sleep(5)

    return all_countries

def store_countries(all_countries):
    for country in all_countries:
        try:
            Country.create(
                name=country["names"]["common"],
                population=country["population"],
                area=country["area"]["kilometers"],
                region=country["region"]
            )
        except Exception as e:
            print(f"Skipping {country['names']['common']}: {e}")

def analyze():
    countries = Country.select()
    data = []
    for country in countries:
        data.append({"name": country.name, "population": country.population, 
                    "area": country.area, 'region': country.region})
        
    df = pd.DataFrame(data)
    df["density"] = df["population"] / df["area"]
    print(df.groupby("region")["population"].sum())

    print(f"Total countries: {len(df)}")
    print(f"\nPopulation by region:\n{df.groupby('region')['population'].sum()}")
    print(f"\nAverage population density by region:\n{df.groupby('region')['density'].mean().round(2)}")
    print(f"\nMost populous country: {df.loc[df['population'].idxmax(), 'name']}")
    print(f"Largest country by area: {df.loc[df['area'].idxmax(), 'name']}")
    return df

def visualize(df):
    region_pop = df.groupby("region")["population"].sum()
    
    plt.figure(figsize=(10, 6))
    plt.bar(region_pop.index, region_pop.values, color="steelblue")
    plt.title("Total Population by Region")
    plt.xlabel("Region")
    plt.ylabel("Population")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("population_by_region.png")
    plt.show()
    print("Chart saved as population_by_region.png")

def main():
    db.connect()
    db.create_tables([Country])
    countries = fetch_countries()
    if Country.select().count() == 0:
        store_countries(countries)
    else:
        print("Database already populated, skipping store.")
    df = analyze()
    visualize(df)
    db.close()

main()


