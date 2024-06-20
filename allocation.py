import random

# Lists of countries
consuming_countries = [
    "India", "United Kingdom", "Japan", "Germany", "Indonesia", "Spain",
    "Australia", "Netherlands", "Canada", "Thailand", "Taiwan", "Singapore"
]

producing_countries = [
    "Saudi Arabia", "UAE", "United States", "Iran", "Iraq", "Kuwait",
    "Venezuela", "Qatar", "Malaysia", "Mexico", "Brazil", "Russia"
]

def generate_country_data(countries):
    country_data = {}
    for country in countries:
        initial_capital = random.randint(1, 20000)
        initial_barrels = random.randint(1, 1000)
        target_barrels = initial_barrels + random.randint(0, 1000)  # Target can be up to 1000 more than initial
        country_data[country] = {
            'initial_capital': initial_capital,
            'initial_barrels': initial_barrels,
            'target_barrels': target_barrels
        }
    return country_data

consuming_countries_data = generate_country_data(consuming_countries)
producing_countries_data = generate_country_data(producing_countries)

# Example of how to print the data
print("Consuming Countries Data:")
for country, data in consuming_countries_data.items():
    print(f"{country}: Initial Capital: ${data['initial_capital']}, Initial Barrels: {data['initial_barrels']}, Target Barrels: {data['target_barrels']}")

print("\nProducing Countries Data:")
for country, data in producing_countries_data.items():
    print(f"{country}: Initial Capital: ${data['initial_capital']}, Initial Barrels: {data['initial_barrels']}, Target Barrels: {data['target_barrels']}")
