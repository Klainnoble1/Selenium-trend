import json
import os
from dotenv import load_dotenv
from n8n_sender import send_to_n8n

def main():
    load_dotenv()
    
    output_path = "trends_output.json"
    if not os.path.exists(output_path):
        print(f"Error: {output_path} not found.")
        return
        
    with open(output_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    print(f"Sending trends data to n8n...")
    result = send_to_n8n(payload)
    
    if result.get("success"):
        print("✅ Sent to n8n successfully.")
        print(f"Response: {result.get('response')}")
    else:
        print(f"❌ Failed to send to n8n: {result.get('error') or result.get('response')}")

if __name__ == "__main__":
    main()
