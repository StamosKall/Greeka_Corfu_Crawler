#!/usr/bin/env python3

import json

def check_websites():
    # Load the updated data
    with open('hotels_updated.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Count hotels with websites
    hotels_with_websites = [h for h in data if h['official_website']]
    
    print(f"Hotels with websites: {len(hotels_with_websites)}/{len(data)} ({len(hotels_with_websites)/len(data)*100:.1f}%)")
    print("\nHotels with websites:")
    for hotel in hotels_with_websites:
        print(f"- {hotel['name']}")
        print(f"  Website: {hotel['official_website']}")
        print()

if __name__ == "__main__":
    check_websites()