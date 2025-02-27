import os
import csv

def save_to_csv(match_data, scraper_name, filename):
    """
    Saves match data to a CSV file inside the scraper's respective data folder.

    :param match_data: List of dictionaries containing match data.
    :param scraper_name: Name of the scraper (e.g., 'oddsportal', 'bet365').
    :param filename: Name of the CSV file to save.
    """
    # Get the absolute path to the scraper-specific data directory
    base_dir = os.path.dirname(os.path.dirname(__file__))  # Go to project root
    data_dir = os.path.join(base_dir, scraper_name, "data")

    # Ensure the data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Define the full path to the CSV file
    csv_path = os.path.join(data_dir, filename)

    # Write data to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        fieldnames = ['Date', 'Time', 'Home Team', 'Away Team', 'Home Odds', 'Draw Odds', 'Away Odds']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for data in match_data:
            writer.writerow(data)

    print(f"✅ Data saved successfully to {csv_path}")




def save_league_table_to_csv(table_data, scraper_name, filename):
    """
    Saves league table data to a CSV file inside the scraper's respective data folder.

    :param table_data: List of dictionaries containing league table data.
    :param scraper_name: Name of the scraper (e.g., 'oddsportal', 'bet365').
    :param filename: Name of the CSV file to save.
    """
    # Get the absolute path to the scraper-specific data directory
    base_dir = os.path.dirname(os.path.dirname(__file__))  # Go to project root
    data_dir = os.path.join(base_dir, scraper_name, "data")

    # Ensure the data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Define the full path to the CSV file
    csv_path = os.path.join(data_dir, filename)

    # Write data to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            'Position', 'Team', 'Played', 'Wins', 'Draws', 'Losses', 
            'Goals For', 'Goals Against', 'Goal Difference', 'Points'
        ] 
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for data in table_data:
            writer.writerow(data)

    print(f"✅ League table saved successfully to {csv_path}")


