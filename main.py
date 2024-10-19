import requests
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Function to fetch the JSON data
def get_json_data():
    url = 'https://cvs-data-public.s3.us-east-1.amazonaws.com/last-availability.json'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'cvs-data-public.s3.us-east-1.amazonaws.com',
        'Origin': 'https://checkvisaslots.com',
        'Referer': 'https://checkvisaslots.com/',
        'Sec-CH-UA': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        return None
    return response.json()

def format_table(data):
    formatted_data = ""
    
    # Loop through each visa type in the result dictionary
    for visa_type, records in data.items():
        if records['H-1B (Dropbox)']:
            for record in records['H-1B (Dropbox)']:
                # Convert the GMT time to Eastern Time
                gmt_time = datetime.strptime(record['createdon'], '%Y-%m-%d %H:%M:%S')
                gmt_time = gmt_time.replace(tzinfo=ZoneInfo('GMT'))
                eastern_time = gmt_time.astimezone(ZoneInfo("America/New_York"))
                
                # Format the Eastern time as a string
                eastern_time_str = eastern_time.strftime('%Y-%m-%d %H:%M:%S %Z')
                
                formatted_data += (
                    f"Location: {record['visa_location']}, "
                    f"Earliest Date: {record['earliest_date']}, "
                    f"Total Dates: {record['no_of_dates']}, "
                    f"Last Seen: {eastern_time_str}, "
                    f"Appointments: {record['no_of_apnts']}\n"
                )
            print(formatted_data)
        return formatted_data


def send_push_notification(message):
    user_key = os.getenv('PUSHOVER_USER_KEY')
    api_token = os.getenv('PUSHOVER_API_TOKEN')

    payload = {
        'user': user_key,
        'token': api_token,
        'message': message,
    }

    response = requests.post("https://api.pushover.net/1/messages.json", data=payload)

    if response.status_code != 200:
        print(f"Error sending Pushover notification: {response.text}")
    else:
        print("Pushover notification sent successfully!")

def check_for_updates():
    new_data = get_json_data()
    if new_data is None:
        print("Failed to fetch data.")
        return

    new_table = format_table(new_data)

    # Load the old data from a file if it exists
    if os.path.exists('last_table.txt'):
        with open('last_table.txt', 'r') as file:
            old_table = file.read()
    else:
        old_table = None

    # Compare the new data with the old data and check if appointments > 0
    if old_table != new_table and any(int(line.split("Appointments: ")[1]) > 0 for line in new_table.split('\n') if line):
        send_push_notification(new_table)

        # Save the new data to the file
        with open('last_table.txt', 'w') as file:
            file.write(new_table)
        print("Data changed. Notification sent and file updated.")
    else:
        print("No significant changes or no available appointments. No notification sent.")

if __name__ == "__main__":
    check_for_updates()
