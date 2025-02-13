
        
        

#second code where its taking tables as well--------------------------------------------------------------------------------------------------------------------------
from bs4 import BeautifulSoup
import requests

url = "https://rera.karnataka.gov.in/projectDetails"

# Payload and headers
payload = {"action": "12778"}
headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "JSESSIONID=1D72777E41C907EAF3F66A95B398C63C",
    "Origin": "https://rera.karnataka.gov.in",
    "Referer": "https://rera.karnataka.gov.in/projectViewDetails",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
}

# Send the request
response = requests.post(url, data=payload, headers=headers)

# Parse the HTML response
soup = BeautifulSoup(response.text, 'html.parser')

# Locate the table
tables = soup.find_all('table', class_='table')  # Adjust the class if needed

for table in tables:
    rows = table.find_all('tr')  # Find all rows in the table
    for row in rows:
        cells = row.find_all('td')  # Find all cells in the row
        if cells:
            # Extract the title from the first column (if applicable)
            title = cells[0].text.strip()
            # Extract the document link (if available in <a> tags)
            link_tag = cells[-1].find('a', href=True)  # Assuming link is in the last column
            if link_tag:
                link = link_tag['href']
                print(f"{title}: https://rera.karnataka.gov.in{link}")


#this is the third script where it is loading everything for uploaded document--------------------------------------------------------------------------------------------
from bs4 import BeautifulSoup
import requests

url = "https://rera.karnataka.gov.in/projectDetails"

# Payload and headers
payload = {"action": "12778"}  # Adjust the action parameter as needed
headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "JSESSIONID=1D72777E41C907EAF3F66A95B398C63C",  # Ensure this is valid
    "Origin": "https://rera.karnataka.gov.in",
    "Referer": "https://rera.karnataka.gov.in/projectViewDetails",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
}

# Send the request
response = requests.post(url, data=payload, headers=headers)

# Parse the HTML response
soup = BeautifulSoup(response.text, 'html.parser')

# Extract document links and their associated text from all tables
tables = soup.find_all('table')  # Get all tables
for table in tables:
    rows = table.find_all('tr')  # Find all rows in the table
    for row in rows:
        cells = row.find_all('td')  # Find all cells in the row
        if cells:
            # Extract the text description
            document_description = cells[1].text.strip() if len(cells) > 1 else "No description"

            # Extract the document link (if available in <a> tags)
            link_tag = row.find('a', href=True)
            if link_tag:
                link = link_tag['href']
                # Ensure the link is absolute
                if not link.startswith('http'):
                    link = f"https://rera.karnataka.gov.in{link}"
                print(f"{document_description}: {link}")

# Extract additional document links and text across the page
# Locate all anchor tags (`<a>`) and print their text and link
all_links = soup.find_all('a', href=True)
for link_tag in all_links:
    link = link_tag['href']
    text = link_tag.text.strip()  # Extract the text for the link
    if 'reraDocument' in link:  # Filter for document-related links
        # Ensure the link is absolute
        if not link.startswith('http'):
            link = f"https://rera.karnataka.gov.in{link}"
        print(f"{text}: {link}")





# inventory details correct--------------------------------------------------------------------------------------------------------------------------
import scrapy
import json
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "rera_scraper"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]

    def __init__(self):
        self.cookies = {
            'JSESSIONID': 'F474E2915CE022928A5A77CCA69C5CC8',
        }
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://rera.karnataka.gov.in',
            'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.output_file = "tower_data.json"

    def start_requests(self):
        # You can add multiple action IDs here
        action_ids = ["12892"]
        for action_id in action_ids:
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_tower_data,
                meta={'action_id': action_id}
            )

    def parse_tower_data(self, response):
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.text, encoding="utf-8")

        tower_data = []
        
        # Locate the area that contains the table in question
        final_selector = scrapy_response.xpath(
            './/h1[contains(text(), "Development") and span[contains(text(), "Bifurcation")]]/..'
        )
        
        if final_selector:
            # Locate the specific table containing tower details (assumed to be the first table here)
            table_selector = final_selector.xpath('.//table[1]')
            if table_selector:
                rows = table_selector.xpath('.//tr')
                # Extract column headers from the first row
                headers = rows[0].xpath('.//th/text()').getall()
                headers = [h.strip() for h in headers]

                # Iterate over data rows, starting from the second row
                for row in rows[1:]:
                    # Check "Sl No" in the first <td>
                    sl_no = row.xpath('.//td[1]/text()').get(default="").strip()

                    # If sl_no is not an integer, we break out of the loop
                    if not sl_no.isdigit():
                        self.logger.info(f"Encountered non-integer Sl No ({sl_no}); stopping row parsing.")
                        break

                    # If sl_no is integer, continue extracting columns
                    row_data = {}
                    for i, header in enumerate(headers):
                        # Use i+1 for the correct column index in XPath
                        value = row.xpath(f'.//td[{i + 1}]/text()').get(default="").strip()
                        row_data[header] = value

                    tower_data.append(row_data)
        else:
            self.logger.warning("No matching section found for the table.")

        self.save_to_json(action_id, tower_data)

    def save_to_json(self, action_id, data):
        try:
            try:
                with open(self.output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}

            existing_data[action_id] = data
            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)

            self.logger.info(f"Saved Tower Data for Action ID {action_id} to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")



# tower data-----------------------------------------------------------------------------------------------------------------------------------------
import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "projectDetails"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]

    def __init__(self):
        self.cookies = {
            'JSESSIONID': 'F474E2915CE022928A5A77CCA69C5CC8',
        }
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://rera.karnataka.gov.in',
            'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.output_file = "tower_data.json"
        self.input_file = "extracted_action_ids_stream.csv"

    def load_action_ids(self):
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip the header row
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"Input file {self.input_file} not found.")
        return action_ids

    def start_requests(self):
        action_ids = self.load_action_ids()
        for action_id in action_ids:
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_tower_data,
                meta={'action_id': action_id}
            )

    def parse_tower_data(self, response):
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.body, encoding="utf-8")
        
        # Only the keys you want
        desired_keys = [
            "Tower Name", "Type", "No. of Floors", "Total No. of Units",
            "No. of Stilts", "No. of slab of super structure",
            "No. of Basement", "Total No. of Parking",
            "Height of the Tower (In Meters)"
        ]
        
        # Prepare our data dictionary
        data = {
            "TowerDetails": []
        }
        
        # Select all tables that match these headers
        tower_tables = scrapy_response.xpath('//table[contains(., "Tower Name") and contains(., "No. of Floors")]')
        
        if not tower_tables:
            self.logger.warning(f"No tower details table found for Action ID {action_id}")
        else:
            for t_index, tower_table in enumerate(tower_tables, start=1):
                # We create a dictionary for the current tower
                tower_dict = {}
                rows = tower_table.xpath('.//tr')

                for row in rows:
                    texts = row.xpath('.//text()').getall()
                    texts = [t.strip() for t in texts if t.strip()]
                    # Pair the texts: first = key, second = value
                    for i in range(0, len(texts), 2):
                        if i + 1 < len(texts):
                            key = texts[i]
                            value = texts[i + 1]
                            if key in desired_keys:
                                tower_dict[key] = value
                
                # If this table provided any data, add it to the list of towers
                if tower_dict:
                    data["TowerDetails"].append(tower_dict)

        # Save combined tower data for this action_id
        self.save_to_json(action_id, data)

    def save_to_json(self, action_id, data):
        try:
            try:
                with open(self.output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}

            existing_data[action_id] = data
            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)

            self.logger.info(f"Saved data for Action ID {action_id} to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            
 
 
#this code is extracting floor plans--------------------------------------------------------------------------------------------------------------------------------------------------------------    
import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class FloorPlanSpider(scrapy.Spider):
    name = "floorPlanSpider"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]  # Adjust if needed

    def __init__(self):
        # Replace these with valid session cookies and request headers for your environment
        self.cookies = {
            'JSESSIONID': 'F474E2915CE022928A5A77CCA69C5CC8',
        }
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://rera.karnataka.gov.in',
            'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }

        # CSV file with action IDs and JSON output
        self.input_file = "extracted_action_ids_stream.csv"
        self.output_file = "floorplan.json"

    def load_action_ids(self):
        """Reads the first column from 'extracted_action_ids_stream.csv' as action IDs."""
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header row if present
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"Input file '{self.input_file}' not found.")
        return action_ids

    def start_requests(self):
        """
        Sends a POST request for each action_id, 
        with 'body=f\"action={action_id}\"' to projectDetails.
        """
        action_ids = self.load_action_ids()
        for action_id in action_ids:
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_floor_plan,
                meta={'action_id': action_id}
            )

    def parse_floor_plan(self, response):
        """
        Looks for all matching floor-plan tables, loops over each,
        extracts floor number & no. of units from each row, 
        and saves them in a list of lists into floorplan.json
        """
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.body, encoding="utf-8")

        # Locate *all* tables with the 'Floor No' / 'No of Units' heading
        floor_tables = scrapy_response.xpath(
            '//table[@class="table table-bordered table-striped table-condensed"]'
            '[.//th[@colspan="5" and contains(text(),"Floor No")] '
            ' and .//th[@colspan="4" and contains(text(),"No of Units")]]'
        )

        if not floor_tables:
            self.logger.warning(f"No matching floor plan table found for Action ID {action_id}")
            self.save_to_json(action_id, [])
            return

        all_tables_data = []  # This will hold a list of lists

        for table in floor_tables:
            # Identify the row that has the <th colspan="5">Floor No</th>, etc.
            floor_heading = table.xpath(
                './/tr[th[@colspan="5" and contains(text(),"Floor No")] and '
                '     th[@colspan="4" and contains(text(),"No of Units")]]'
            )
            if not floor_heading:
                self.logger.info(f"No floor header row in this table. Skipping. (Action ID {action_id})")
                continue

            # Next, get the subsequent <tr> from either a <tbody> or direct siblings
            floor_rows = floor_heading.xpath('./following-sibling::tbody[1]/tr')
            if not floor_rows:
                floor_rows = floor_heading.xpath('./following-sibling::tr')

            table_data = []
            for row in floor_rows:
                # If we see a <th> row, we assume it's a heading or new table => stop reading more rows
                if row.xpath('./th'):
                    break

                floor_no = row.xpath('./td[1]/text()').get()
                no_of_units = row.xpath('./td[2]/text()').get()

                # Typically the row has <td colspan="5">someFloor</td><td colspan="4">someUnits</td>
                if floor_no and no_of_units:
                    table_data.append({
                        "FloorNo": floor_no.strip(),
                        "NoOfUnits": no_of_units.strip()
                    })
                else:
                    # Possibly a filler/heading row or incomplete data => break
                    break

            if table_data:
                all_tables_data.append(table_data)

        # Save the combined multi-table data
        self.save_to_json(action_id, all_tables_data)

    def save_to_json(self, action_id, all_floor_data):
        """
        Loads 'floorplan.json' from disk, merges/updates data for the current action_id,
        then writes back. all_floor_data is a list of lists, e.g. [ [ {FloorNo,NoOfUnits},.. ], ... ]
        """
        try:
            try:
                with open(self.output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}

            existing_data[action_id] = all_floor_data

            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)

            self.logger.info(f"Saved floor plan data for Action ID {action_id} to '{self.output_file}'")
        except Exception as e:
            self.logger.error(f"Error saving floor plan data for Action ID {action_id}: {e}")




#this script is for uploaded doc

import requests
import certifi
import ssl
from bs4 import BeautifulSoup
import os
import json
import csv

def sanitize_filename(filename):
    """Remove or replace invalid characters from a filename."""
    invalid_chars = r'\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename

def main():
    # ------------------------------------------------
    # 1) Configuration: headers and cookies
    # ------------------------------------------------
    cookies = {
        'JSESSIONID': '02E62E6483634774FB712EBE28E64DEC',  # Update if needed
    }
    
    headers = {
        'Accept': 'application/xml, text/xml, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://rera.karnataka.gov.in',
        'Pragma': 'no-cache',
        'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/131.0.0.0 Safari/537.36'),
        'X-Requested-With': 'XMLHttpRequest',
    }

    cert_path = certifi.where()
    ssl_context = ssl.create_default_context(cafile=cert_path)

    # ------------------------------------------------
    # 2) Read action IDs from CSV
    # ------------------------------------------------
    input_csv = "extracted_action_ids_stream.csv"
    action_ids = []
    with open(input_csv, "r", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        next(reader, None)  # Skip the header if present
        for row in reader:
            if row and row[0].strip():  # Ensure row is not empty and has a valid action ID
                action_id = row[0].strip()
                action_ids.append(action_id)

    print(f"Extracted Action IDs: {action_ids}")

    # ------------------------------------------------
    # 3) Prepare JSON output and PDF folder
    # ------------------------------------------------
    output_json = "uploadeddoc.json"
    pdf_folder = "uploadeddoc_pdfs"
    os.makedirs(pdf_folder, exist_ok=True)

    all_data = {}

    # ------------------------------------------------
    # 4) Loop over each action ID, fetch & parse
    # ------------------------------------------------
    for action_id in action_ids:
        print(f"\n[INFO] Fetching details for Action ID={action_id} ...")

        project_details_url = "https://rera.karnataka.gov.in/projectDetails"
        payload_details = {'action': action_id}

        try:
            response_details = requests.post(
                project_details_url,
                headers=headers,
                cookies=cookies,
                data=payload_details,
                verify=cert_path  # or verify=False if you prefer
            )
            response_details.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch details for ID={action_id}: {e}")
            continue

        # Step A: Parse the Land Details page
        soup = BeautifulSoup(response_details.text, "html.parser")
        data_dict = {"ActionID": action_id, "Details": {}, "PDFs": {}}

        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True).replace(":", "")
                value = cols[1].get_text(strip=True)
                data_dict["Details"][label] = value

                # Check for PDF link
                pdf_anchor = cols[1].find("a", href=True)
                if pdf_anchor:
                    pdf_url = pdf_anchor["href"]
                    if not pdf_url.startswith("http"):
                        pdf_url = f"https://rera.karnataka.gov.in{pdf_url}"
                    pdf_filename = f"{action_id}_{label.replace(' ', '_')}.pdf"
                    pdf_filename = sanitize_filename(pdf_filename)  # Sanitize filename
                    pdf_path = os.path.join(pdf_folder, pdf_filename)

                    # Download the PDF
                    try:
                        pdf_response = requests.get(pdf_url, headers=headers, verify=cert_path)
                        pdf_response.raise_for_status()
                        with open(pdf_path, "wb") as pdf_file:
                            pdf_file.write(pdf_response.content)
                        data_dict["PDFs"][label] = pdf_path
                        print(f"[INFO] Downloaded PDF for {label}: {pdf_path}")
                    except requests.exceptions.RequestException as e:
                        print(f"[ERROR] Failed to download PDF for {label}: {e}")

        all_data[action_id] = data_dict
        print(f"[INFO] Parsed data for ID={action_id}")

    # ------------------------------------------------
    # 5) Save to JSON file
    # ------------------------------------------------
    with open(output_json, "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, indent=4)

    print(f"\n[INFO] Finished! All data saved in '{output_json}'.")

if __name__ == "__main__":
    main()
    
    
    
# project details updated
import scrapy
import csv
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "rera_scraper"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]

    def __init__(self):
        self.cookies = {'JSESSIONID': '02E62E6483634774FB712EBE28E64DEC'}  # Update as needed
        self.headers = {
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://rera.karnataka.gov.in',
            'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/131.0.0.0 Safari/537.36'),
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.input_file = "extracted_action_ids_stream.csv"
        self.output_file = "projectdetails.csv"

        # Read action IDs from input CSV
        self.action_ids = self.load_action_ids()

    def load_action_ids(self):
        """Loads action IDs from CSV."""
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as infile:
                reader = csv.reader(infile)
                next(reader, None)  # Skip header
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"File {self.input_file} not found.")
        return action_ids

    def start_requests(self):
        for action_id in self.action_ids:
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                formdata={'action': action_id},
                cookies=self.cookies,
                headers=self.headers,
                callback=self.parse_project_details,
                meta={'action_id': action_id}
            )

    def parse_project_details(self, response):
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.text, encoding="utf-8")

        # Use a dictionary to avoid duplicates per label
        field_dict = {}

        # ---------------------------------------------------------
        # 1) ADDITIONAL FIELDS (Project Name, Ack No, Reg No, etc.)
        # ---------------------------------------------------------
        project_name = scrapy_response.xpath(
            '//span[contains(text(),"Project Name")]/b/text()'
        ).get(default="").strip()
        if project_name and "Project Name" not in field_dict:
            field_dict["Project Name"] = project_name

        acknowledgement_number = scrapy_response.xpath(
            '//span[contains(text(),"Acknowledgement Number")]/b/text()'
        ).get(default="").strip()
        if acknowledgement_number and "Acknowledgement Number" not in field_dict:
            field_dict["Acknowledgement Number"] = acknowledgement_number

        registration_number = scrapy_response.xpath(
            '//span[contains(text(),"Registration Number")]/b/text()'
        ).get(default="").strip()
        if registration_number and "Registration Number" not in field_dict:
            field_dict["Registration Number"] = registration_number

        latitude = scrapy_response.xpath(
            '//div[p[contains(normalize-space(.),"Latitude")]]'
            '/following-sibling::div[1]/p/text()'
        ).get(default="").strip()
        if latitude and "Latitude" not in field_dict:
            field_dict["Latitude"] = latitude

        longitude = scrapy_response.xpath(
            '//div[p[contains(normalize-space(.),"Longitude")]]'
            '/following-sibling::div[1]/p/text()'
        ).get(default="").strip()
        if longitude and "Longitude" not in field_dict:
            field_dict["Longitude"] = longitude

        local_authority = scrapy_response.xpath(
            '//div[p[contains(normalize-space(.),"Local Authority")]]'
            '/following-sibling::div[1]/p/text()'
        ).get(default="").strip()
        if local_authority and "Local Authority" not in field_dict:
            field_dict["Local Authority"] = local_authority

        # ---------------------------------------------------------
        # 2) EXISTING LOGIC (FIELD MAPPING)
        # ---------------------------------------------------------
        project_details = scrapy_response.xpath('//div[@class="col-md-3 col-sm-6 col-xs-6"]/p')
        taluk_details = scrapy_response.xpath('//div[@class="col-md-6 col-sm-6 col-xs-6"]/p')
        inventory_details = scrapy_response.xpath('//div[@class="col-md-3 col-sm-6 col-xs-6"]/p')

        field_mapping = {
            'Project Name': 'Project Name',
            'Project Description': 'Project Description',
            'Project Type': 'Project Type',
            'Project Status': 'Project Status',
            'Project Sub Type': 'Project Sub Type',
            'Total amount of money used for development of project': 'Total amount of money used for development of project',
            'Extent of development carried till date': 'Extent of development carried till date',
            'Extent of development pending': 'Extent of development pending',
            'Project Start Date': 'Project Start Date',
            'Proposed Completion Date': 'Proposed Completion Date',
            'Project Address': 'Project Address',
            'District': 'District',
            'Taluk': 'Taluk',
            'Pin Code': 'Pin Code',
            'North Schedule': 'North Schedule',
            'East Schedule': 'East Schedule',
            'South Schedule': 'South Schedule',
            'West Schedule': 'West Schedule',
            'Approving Authority': 'Approving Authority',
            'Approved Plan Number': 'Approved Plan Number',
            'Plan Approval Date': 'Plan Approval Date',
            'Have you applied for RERA Registration for the same Plan ?': 'Have you applied for RERA Registration for the same Plan ?',
            'Total Number of Inventories/Flats/Villas': 'Total Number of Inventories/Flats/Villas',
            'No. of Open Parking': 'No. of Open Parking',
            'No. of Garage': 'No. of Garage',
            'No. of Covered Parking': 'No. of Covered Parking',
            'Total Open Area (Sq Mtr) (A1)': 'Total Open Area (Sq Mtr) (A1)',
            'Total Area Of Land (Sq Mtr) (A1+A2)': 'Total Area Of Land (Sq Mtr) (A1+A2)',
            'Total Built-up Area of all the Floors (Sq Mtr)': 'Total Built-up Area of all the Floors (Sq Mtr)',
            'Total Plinth Area (Sq Mtr)': 'Total Plinth Area (Sq Mtr)',
            'Area Of Open Parking (Sq Mtr)': 'Area Of Open Parking (Sq Mtr)',
            'Area of Garage (Sq Mtr)': 'Area of Garage (Sq Mtr)',
            'Total Coverd Area (Sq Mtr) (A2)': 'Total Coverd Area (Sq Mtr) (A2)',
            'Total Carpet Area of all the Floors (Sq Mtr)': 'Total Carpet Area of all the Floors (Sq Mtr)',
            'Area Of Covered Parking (Sq Mtr)': 'Area Of Covered Parking (Sq Mtr)',
            'Source of Water': 'Source of Water',
            'Is TDR Applicable ?': 'Is TDR Applicable ?',
        }

        # Go through each detail list, skip duplicates if label is already in field_dict
        for details in [project_details, inventory_details, taluk_details]:
            for i in range(len(details)):
                label = details[i].xpath('normalize-space(text())').get(default="").strip()
                # Next line if within bounds
                value = (
                    details[i+1].xpath('normalize-space(text())').get(default="").strip()
                    if i + 1 < len(details) else ""
                )
                if label and label in field_mapping:
                    mapped_label = field_mapping[label]
                    # Only store if we haven't already stored that mapped_label
                    if mapped_label not in field_dict:
                        field_dict[mapped_label] = value

        # ---------------------------------------------------------
        # 3) Convert field_dict to a list of rows (ActionID, Field, Value)
        # ---------------------------------------------------------
        extracted_data = []
        for field_label, field_value in field_dict.items():
            extracted_data.append([action_id, field_label, field_value])

        # Finally, write everything to CSV
        self.save_to_csv(extracted_data)

    def save_to_csv(self, data):
        """Save extracted data to CSV."""
        try:
            file_exists = False
            try:
                with open(self.output_file, "r", encoding="utf-8") as checkfile:
                    file_exists = bool(checkfile.readline())
            except FileNotFoundError:
                pass

            with open(self.output_file, "a", newline="", encoding="utf-8") as outfile:
                writer = csv.writer(outfile)
                if not file_exists:
                    # Write header if file is new
                    writer.writerow(["ActionID", "Field", "Value"])
                writer.writerows(data)

            if data:
                self.logger.info(f"Saved Action ID {data[0][0]} to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
