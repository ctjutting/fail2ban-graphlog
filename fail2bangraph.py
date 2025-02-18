# pip install requests matplotlib
# 0 7 * * * /usr/bin/python3 /path/to/your/script.py
import subprocess
import requests
from datetime import datetime, timedelta
from collections import Counter
import io
import matplotlib.pyplot as plt

# Define Fail2Ban log file path
fail2ban_log_path = '/var/log/fail2ban.log'

# Define your ipinfo.io token
ipinfo_token = 'token'

# Define your Discord webhook URL
discord_webhook_url = 'webhooks'  # Replace with your webhook URL

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

# Get unbanned IPs from Fail2Ban log
def get_unbanned_ips(log_path):
    unbanned_ips = set()
    cutoff_time = datetime.now() - timedelta(days=1)
    with open(log_path, 'r') as file:
        lines = file.readlines()
    for line in lines:
        if 'Unban' in line:
            timestamp_str = ' '.join(line.split()[:2])
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            if timestamp > cutoff_time:
                unbanned_ips.add(line.split()[-1])
    return list(unbanned_ips)

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

# Send text message to Discord using webhook
def send_text_to_discord(text, webhook_url):
    payload = {"content": text}
    response = requests.post(webhook_url, json=payload)
    return response.status_code

# Send images to Discord using webhook
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
    unbanned_ips = get_unbanned_ips(fail2ban_log_path)
    
    # Plot and send Country, State, City distribution chart
    fig1 = plot_country_state_city(banned_ips_info)
    send_image_to_discord(fig1, discord_webhook_url, 'country_state_city.png')
    
    # Send list of banned IPs with ASN and ISP
    banned_list_text = "Banned IPs in the Last 24 Hours:\n"
    for info in banned_ips_info:
        banned_list_text += f"IP: {info.get('ip', 'Unknown')}, ASN: {info.get('org', 'Unknown')}, ISP: {info.get('hostname', 'Unknown')}\n"
    send_text_to_discord(banned_list_text, discord_webhook_url)
    
    # Send list of unbanned IPs
    if unbanned_ips:
        unbanned_list_text = "Unbanned IPs in the Last 24 Hours:\n" + "\n".join(unbanned_ips)
        send_text_to_discord(unbanned_list_text, discord_webhook_url)
    
if __name__ == '__main__':
    main()
