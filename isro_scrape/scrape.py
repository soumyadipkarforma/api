import requests
from bs4 import BeautifulSoup
import json
import os
import re

def normalize_key(key):
    # Remove extra underscores and whitespace, convert to lowercase
    key = key.lower().strip()
    key = re.sub(r'[^a-z0-9\s]', '', key)
    key = re.sub(r'\s+', '_', key)
    return re.sub(r'_+', '_', key)

def scrape():
    base_url = "https://www.isro.gov.in"
    list_url = f"{base_url}/SpacecraftMissions.html"
    
    try:
        response = requests.get(list_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching list page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # Find links to specific spacecraft
    craft_links = soup.find_all("a", {"class": "out"})
    
    new_data = []
    seen_names = set()

    for craft in craft_links:
        title = " ".join(craft.text.split()).strip()
        if not title or title in seen_names:
            continue
            
        link = craft["href"]
        if not link.startswith("http"):
            url = f"{base_url}/{link.lstrip('/')}"
        else:
            url = link

        try:
            print(f"Scraping: {title}")
            res = requests.get(url, timeout=20)
            res.raise_for_status()
            c_soup = BeautifulSoup(res.text, 'html.parser')
            
            # The specific table class used in ISRO site
            tables = c_soup.find_all("table", {"class": "pContent table table-striped table-bordered"})
            
            dt = {"name": title}
            found_info = False
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) == 2:
                        key = normalize_key(cols[0].text)
                        val = " ".join(cols[1].text.split()).strip()
                        if key and val:
                            dt[key] = val
                            found_info = True
            
            if found_info:
                new_data.append(dt)
                seen_names.add(title)
                
        except Exception as e:
            print(f"Skipping {title} due to error: {e}")

    # Reverse to keep chronological order if needed (ISRO usually lists newest first)
    new_data.reverse()
    
    # Assign IDs
    for i, item in enumerate(new_data):
        item["id"] = i + 1

    # Save to file (overwrites to keep repo lean)
    output_path = "data/spacecraft_missions.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully updated {output_path} with {len(new_data)} missions.")

if __name__ == "__main__":
    scrape()
