import requests
import certifi
import re
from bs4 import BeautifulSoup
import csv

def main():
    # -------------------------------------
    # 1) Create a Session, set headers
    # -------------------------------------
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/131.0.0.0 Safari/537.36'
    })
    # If the site needs a cookie:
    # session.cookies.set('JSESSIONID', '02E62E6483634774FB712EBE28E64DEC')

    # -------------------------------------
    # 2) Prepare your search form data
    #    (Adjust fields to match the site)
    # -------------------------------------
    payload = {
        "district": "BENGALURU URBAN",
        "taluk": "",
        "projectName": "",
        "promoterName": "",
        "registrationNo": ""
        # possibly more hidden fields if needed
    }

    search_url = "https://rera.karnataka.gov.in/projectViewDetails"

    try:
        # -------------------------------------
        # 3) Make a POST request with stream=True
        # -------------------------------------
        response = session.post(
            search_url,
            data=payload,
            stream=True,        # enables chunked reading
            verify=certifi.where(),
            timeout=60          # increase timeout if needed
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Search request failed: {e}")
        return

    # -------------------------------------
    # 4) Read the response in chunks
    # -------------------------------------
    content = b""
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            content += chunk

    # Decode to HTML (assuming UTF-8)
    html_text = content.decode("utf-8", errors="replace")

    # -------------------------------------
    # 5) Parse with BeautifulSoup
    # -------------------------------------
    soup = BeautifulSoup(html_text, "html.parser")

    # Find all <a> with onclick containing "showFileApplicationPreview"
    links = soup.find_all("a", onclick=re.compile(r"showFileApplicationPreview"))

    # Collect their 'id' attributes
    action_ids = []
    for link in links:
        link_id = link.get("id")
        if link_id:
            action_ids.append(link_id)

    print(f"[INFO] Found {len(action_ids)} IDs.")
    print(action_ids)

    # -------------------------------------
    # 6) Write IDs to CSV
    # -------------------------------------
    csv_filename = "extracted_action_ids_stream.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ActionID"])
        for aid in action_ids:
            writer.writerow([aid])

    print(f"[INFO] Wrote IDs to {csv_filename}")

if __name__ == "__main__":
    main()
