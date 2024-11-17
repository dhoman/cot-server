import openai
import requests
from urllib.parse import urljoin
import sys
import socket
from requests.exceptions import RequestException
import time

def test_single_host(host, timeout=2):
    """Test a single host with timeout"""
    try:
        print(f"Testing connection to {host}...")
        response = requests.get(host, timeout=timeout)
        if response.status_code == 200:
            print(f"✓ Successfully connected to {host}")
            return True
    except RequestException as e:
        print(f"✗ Could not connect to {host}: {e.__class__.__name__}")
    return False

def find_wsl_host():
    """Try different possible hosts for WSL2 with timeout"""
    possible_hosts = [
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ]
    
    # Try to get WSL2 IP - with timeout
    try:
        hostname = socket.gethostname()
        wsl_ip = socket.gethostbyname(hostname)
        possible_hosts.append(f"http://{wsl_ip}:5000")
        print(f"Found WSL IP: {wsl_ip}")
    except socket.gaierror as e:
        print(f"Could not resolve WSL hostname: {e}")

    # Try each host
    for host in possible_hosts:
        if test_single_host(host):
            return f"{host}/v1"
    
    return None

print("Starting server connection test...")
print("-----------------------------------")

# Try to find the correct host
base_url = find_wsl_host()
if not base_url:
    print("\nCould not find a working host. Troubleshooting steps:")
    print("1. Verify the Flask server is running with:")
    print("   python app.py")
    print("\n2. Check the Flask server output for its IP address")
    print("\n3. In WSL terminal, run:")
    print("   ip addr show eth0")
    print("   This will show your WSL IP address")
    print("\n4. Try manually accessing the server with curl:")
    print("   curl http://localhost:5000")
    print("   curl http://127.0.0.1:5000")
    sys.exit(1)

print(f"\nUsing base URL: {base_url}")

# Configure the client
client = openai.Client(
    api_key="test-key",
    base_url=base_url
)

try:
    print("\nTesting OpenAI API call...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Explain how a car engine works"}
        ]
    )
    
    print("\nResponse received:")
    print(response.choices[0].message.content)
    print("\nReasoning:")
    print(response.choices[0].message.reasoning)

except openai.APIConnectionError as e:
    print(f"\nConnection Error: {e}")
    print("\nAPI call failed. Please verify:")
    print("1. The Flask server is running and shows no errors")
    print("2. The server output shows it's listening on 0.0.0.0:5000")
    print("3. Your firewall is not blocking the connection")
    
except Exception as e:
    print(f"Other error occurred: {e}")
