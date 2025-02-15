# pip install requests matplotlib
# 0 7 * * * /usr/bin/python3 /path/to/your/script.py


import subprocess
import requests
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from collections import Counter

# Define Fail2Ban log file path
fail2ban_log_path = '/var/log/fail2ban.log'

# Define your ipinfo.io token
ipinfo_token = 'token here'

# Define your Discord webhook URL
discord_webhook_url = 'https://discord.com/api/webhooks/'  # Replace with your webhook URL

# Get banned IPs from Fail2Ban log
def get_banned_ips(log_path):
    banned_ips = set()
    cutoff_time = datetime.now() - timedelta(days=1)
    with open(log_path, 'r') as file:
        lines = file.readlines()
    for line in lines:
        if 'Ban' in line:
            timestamp_str = ' '.join(line.split()[:2])
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            if timestamp > cutoff_time:
                banned_ips.add(line.split()[-1])
    return list(banned_ips)

# Get IP information from ipinfo.io
def get_ip_info(ip, token):
    response = requests.get(f'https://ipinfo.io/{ip}/json?token={token}')
    return response.json()

# Create bar chart for Country, State, City distribution
def plot_country_state_city(banned_ips_info):
    countries = [info.get('country', 'Unknown') for info in banned_ips_info]
    cities = [info.get('city', 'Unknown') for info in banned_ips_info]
    states = [info.get('region', 'Unknown') for info in banned_ips_info]

    fig, ax = plt.subplots(3, 1, figsize=(10, 10))
    
    country_counts = Counter(countries)
    state_counts = Counter(states)
    city_counts = Counter(cities)
    
    ax[0].bar(country_counts.keys(), country_counts.values())
    ax[0].set_title('Banned IPs by Country')
    
    ax[1].bar(state_counts.keys(), state_counts.values())
    ax[1].set_title('Banned IPs by State')

    ax[2].bar(city_counts.keys(), city_counts.values())
    ax[2].set_title('Banned IPs by City')

    plt.tight_layout()
    return fig

# Create bar chart for IP details
def plot_ip_details(banned_ips_info):
    ips = [info.get('ip', 'Unknown') for info in banned_ips_info]
    asns = [info.get('org', 'Unknown') for info in banned_ips_info]
    isps = [info.get('hostname', 'Unknown') for info in banned_ips_info]

    fig, ax = plt.subplots(3, 1, figsize=(10, 10))

    ax[0].bar(ips, range(len(ips)))
    ax[0].set_title('Banned IPs')
    
    ax[1].bar(asns, range(len(asns)))
    ax[1].set_title('Banned IPs by ASN')

    ax[2].bar(isps, range(len(isps)))
    ax[2].set_title('Banned IPs by ISP')

    plt.tight_layout()
    return fig

# Function to send images to Discord using webhook
def send_image_to_discord(fig, webhook_url, filename):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    response = requests.post(webhook_url, files={filename: buf})
    return response.status_code

# Main function
def main():
    banned_ips = get_banned_ips(fail2ban_log_path)
    banned_ips_info = [get_ip_info(ip, ipinfo_token) for ip in banned_ips]
    
    # Plot and send Country, State, City distribution chart
    fig1 = plot_country_state_city(banned_ips_info)
    send_image_to_discord(fig1, discord_webhook_url, 'country_state_city.png')

    # Plot and send IP details chart
    fig2 = plot_ip_details(banned_ips_info)
    send_image_to_discord(fig2, discord_webhook_url, 'ip_details.png')

if __name__ == '__main__':
    main()
