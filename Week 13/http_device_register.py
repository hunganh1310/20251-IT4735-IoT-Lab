import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ThingsBoard server URL
THINGSBOARD_URL = "http://demo.thingsboard.io/api/v1/provision"

# Device provisioning credentials from environment variables
DEVICE_NAME = os.getenv("DEVICE_NAME")
PROVISION_KEY = os.getenv("PROVISION_KEY")
PROVISION_SECRET = os.getenv("PROVISION_SECRET")

def provision_device():
    payload = {
        "deviceName": DEVICE_NAME,
        "provisionDeviceKey": PROVISION_KEY,
        "provisionDeviceSecret": PROVISION_SECRET
    }
    
    print("ThingsBoard Device Provisioning")
    print(f"\nSending POST request to: {THINGSBOARD_URL}")
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            THINGSBOARD_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Device Provisioning Successful!")
            print(f"\nServer Response:")
            print(json.dumps(result, indent=2))
            
            if result.get("status") == "SUCCESS":
                access_token = result.get("credentialsValue")
                print(f"ACCESS TOKEN: {access_token}")
                
                with open("access_token.txt", "w") as f:
                    f.write(access_token)
                print("Token saved to 'access_token.txt'")
                
                return access_token
            else:
                print(f"\nProvisioning failed with status: {result.get('status')}")
                return None
        else:
            print(f"\nError: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {e}")
        return None

if __name__ == "__main__":
    
    # Run the provisioning
    access_token = provision_device()
    
    if access_token:
        print("\nDevice provisioning completed successfully!")
    else:
        print("\nDevice provisioning failed. Please check your credentials and try again.")
