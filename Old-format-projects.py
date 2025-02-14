import scrapy
import csv
import json
import re
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "Old-format-projects"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]

    def __init__(self):
        # Replace with valid cookies/headers if needed
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
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
            ),
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.input_file = "C:\\Users\\khush\\old-format-rera-projects\\myproject\\myproject\\spiders\\extracted_action_ids_stream.csv"
        self.output_file = "old.json" 

    def load_action_ids(self):
        """Reads the first column of the CSV (skipping header) and returns a list of action IDs."""
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # skip header
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"Input file '{self.input_file}' not found.")
        return action_ids

    def start_requests(self):
        """For each action_id from the CSV, sends a POST request with body='action={id}'."""
        action_ids = self.load_action_ids()
        for action_id in action_ids:
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_details,
                meta={'action_id': action_id}
            )

    def parse_details(self, response):
        """Extracts details and saves them to a JSON file keyed by action_id."""
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.text, encoding="utf-8")
        data = {}
        # Get full text of the page (for regex fallback)
        body_text = scrapy_response.xpath("string(//body)").get(default="")

        # --- Helper Functions ---

        def extract_field(label, text):
            """
            Uses regex to extract the value following 'label :' in the text.
            """
            pattern = re.compile(rf'{re.escape(label)}\s*:\s*(.+)', re.IGNORECASE)
            match = pattern.search(text)
            if match:
                return match.group(1).splitlines()[0].strip()
            return ""

        def extract_from_label_element(label):
            """
            Finds a <p> element containing the label and returns the text after the colon.
            """
            element_text = scrapy_response.xpath(f'//p[contains(text(), "{label}")]//text()').getall()
            if element_text:
                full_text = " ".join(element_text).strip()
                parts = full_text.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
            return ""

        def extract_with_default(label):
            """
            Tries to extract the value using XPath; if nothing is found, falls back
            to regex extraction. Returns 'not mentioned' if still empty.
            """
            value = extract_from_label_element(label) or extract_field(label, body_text)
            return value.strip() if value.strip() else "not mentioned"

        def extract_coordinate(label):
            """
            Extracts a coordinate field and returns "not mentioned" if the extracted value
            appears to be just a leftover label (e.g., "North Longitude:").
            """
            val = extract_with_default(label)
            if re.match(r'^(north|south|east|west)\s+(longitude|latitude):$', val.lower()):
                return "not mentioned"
            return val

        # --- Field Extraction ---
        # Registration Number (using XPath to target the <b> element)
        registration_number = scrapy_response.xpath(
            '//span[contains(@class, "user_name") and contains(., "Registration Number")]/b/text()'
        ).get()
        if registration_number:
            data["RegistrationNumber"] = registration_number.strip()
        else:
            data["RegistrationNumber"] = extract_field("Registration Number", body_text)

        project_type = extract_from_label_element("Project Type") or extract_field("Project Type", body_text)
        data["ProjectType"] = project_type if project_type else "not mentioned"

        project_status = extract_from_label_element("Project Status") or extract_field("Project Status", body_text)
        data["ProjectStatus"] = project_status if project_status else "not mentioned"

        project_start_date = extract_from_label_element("Project Start Date") or extract_field("Project Start Date", body_text)
        data["ProjectStartDate"] = project_start_date if project_start_date else "not mentioned"

        proposed_completion = (extract_from_label_element("Proposed Project Completion") or 
                               extract_field("Proposed Project Completion Date", body_text))
        data["ProposedProjectCompletion"] = proposed_completion.strip() if proposed_completion.strip() else "not mentioned"

        # Latitude/Longitude fields (we extract only latitudes as per format)
        data["NorthLatitude"] = extract_coordinate("North Latitude")
        data["SouthLatitude"] = extract_coordinate("South Latitude")
        data["EastLatitude"]  = extract_coordinate("East Latitude")
        data["WestLatitude"]  = extract_coordinate("West Latitude")

        def get_text_after_label(label):
            """Returns the text of the <p> immediately following a <p> that contains the label."""
            val = scrapy_response.xpath(f'//p[contains(text(),"{label}")]/following::p[1]//text()').get()
            return val.strip() if val else ""

        project_name = scrapy_response.xpath(
            '//span[@class="pull-right user_name"][contains(text(),"Project Name")]/b/text()'
        ).get()
        if project_name:
            data["ProjectName"] = project_name.strip()

        proj_desc = scrapy_response.xpath(
            '//div[@class="row"]//p[.="Project Description:"]/following::pre[1]//text()'
        ).get()
        if proj_desc:
            data["ProjectDescription"] = proj_desc.strip()
        
        data["TotalAreaOfLand"] = get_text_after_label("Total Area Of Land")
        data["TotalCoveredArea"] = get_text_after_label("Total Coverd Area")
        data["TotalOpenArea"] = get_text_after_label("Total Open Area")
        data["EstimatedCostOfConstruction"] = get_text_after_label("Estimated Cost of Construction")
        data["CostOfLand"] = get_text_after_label("Cost of Land")
        data["TotalProjectCost"] = get_text_after_label("Total Project Cost")
        data["ProjectAddress"] = get_text_after_label("Project Address")
        data["District"] = get_text_after_label("District")
        data["Taluk"] = get_text_after_label("Taluk")
        data["ApprovingAuthority"] = get_text_after_label("Approving Authority")
        data["NoOfGarageForSale"] = get_text_after_label("No of Garage for Sale")
        data["AreaOfGarageForSaleSqMtr"] = get_text_after_label("Area of Garage for Sale (Sq Mtr)")
        data["NoOfParkingForSale"] = get_text_after_label("No of Parking for Sale")
        data["AreaOfParkingForSaleSqMtr"] = get_text_after_label("Area of Parking for Sale (Sq Mtr)")

        # --- Development Details ---
        dev_details = {}
        dev_map = {
            "Type of Inventory": "typeOfInventory",
            "No of Inventory": "noOfInventory",
            "Carpet Area (Sq Mtr)": "carpetAreaSqMtr",
            "Area of exclusive balcony/verandah (Sq Mtr)": "balconyVerandahSqMtr",
            "Area of exclusive open terrace if any (Sq Mtr)": "openTerraceSqMtr"
        }
        for label_text, field_key in dev_map.items():
            value = get_text_after_label(label_text)
            dev_details[field_key] = value if value else "not mentioned"
        data["DevelopmentDetails"] = dev_details

        # --- External Development ---
        ext_labels = {
            'Road System': 'roadSystem',
            'Water Supply': 'waterSupply',
            'Sewege and Drainage System': 'sewegeDrainage',
            'Electricity Supply Transformer And Sub Station': 'electricitySubstation',
            'Solid Waste Management And Disposal': 'wasteManagement',
            'Fire Fighting facility': 'fireFighting',
            'Drinking Water Facility': 'drinkingWater',
            'Emergency Evacuation Services': 'emergencyEvac',
            'Use of Renewable Energy': 'renewableEnergy'
        }
        external_dev = {}
        for label_text, key in ext_labels.items():
            value = get_text_after_label(label_text)
            external_dev[key] = value if value else "not mentioned"
        data["ExternalDevelopment"] = external_dev

        # --- Project Bank details ---
        bank_data = {}
        bank_data["BankName"] = get_text_after_label("Bank Name")
        bank_data["Branch"] = get_text_after_label("Branch")
        bank_data["ifscCode"] = get_text_after_label("ifscCode")
        bank_data["AccountNo_70Percent"] = get_text_after_label("Account No.(70% Account)")
        bank_data["BankState"] = get_text_after_label("State")
        bank_data["BankDistrict"] = get_text_after_label("District")
        data["ProjectBank"] = bank_data

        # --- Assemble final ordered dictionary ---
        # This matches the format: RegistrationNumber at top, then the other keys in order.
        ordered_data = {
            "RegistrationNumber": data.get("RegistrationNumber", "not mentioned"),
            "ProjectName": data.get("ProjectName", "not mentioned"),
            "ProjectDescription": data.get("ProjectDescription", "not mentioned"),
            "ProjectType": data.get("ProjectType", "not mentioned"),
            "ProjectStatus": data.get("ProjectStatus", "not mentioned"),
            "ProjectStartDate": data.get("ProjectStartDate", "not mentioned"),
            "ProposedProjectCompletion": data.get("ProposedProjectCompletion", "not mentioned"),
            "TotalAreaOfLand": data.get("TotalAreaOfLand", "not mentioned"),
            "TotalCoveredArea": data.get("TotalCoveredArea", "not mentioned"),
            "TotalOpenArea": data.get("TotalOpenArea", "not mentioned"),
            "EstimatedCostOfConstruction": data.get("EstimatedCostOfConstruction", "not mentioned"),
            "CostOfLand": data.get("CostOfLand", "not mentioned"),
            "TotalProjectCost": data.get("TotalProjectCost", "not mentioned"),
            "ProjectAddress": data.get("ProjectAddress", "not mentioned"),
            "District": data.get("District", "not mentioned"),
            "Taluk": data.get("Taluk", "not mentioned"),
            "NorthLatitude": data.get("NorthLatitude", "not mentioned"),
            "SouthLatitude": data.get("SouthLatitude", "not mentioned"),
            "EastLatitude": data.get("EastLatitude", "not mentioned"),
            "WestLatitude": data.get("WestLatitude", "not mentioned"),
            "ApprovingAuthority": data.get("ApprovingAuthority", "not mentioned"),
            "NoOfGarageForSale": data.get("NoOfGarageForSale", "not mentioned"),
            "AreaOfGarageForSaleSqMtr": data.get("AreaOfGarageForSaleSqMtr", "not mentioned"),
            "NoOfParkingForSale": data.get("NoOfParkingForSale", "not mentioned"),
            "AreaOfParkingForSaleSqMtr": data.get("AreaOfParkingForSaleSqMtr", "not mentioned"),
            "DevelopmentDetails": data.get("DevelopmentDetails", "not mentioned"),
            "ExternalDevelopment": data.get("ExternalDevelopment", "not mentioned"),
            "ProjectBank": data.get("ProjectBank", "not mentioned")
        }

        self.save_to_json(action_id, ordered_data)

    def save_to_json(self, action_id, data):
        """Merge/overwrite data for a given action_id into the JSON output."""
        try:
            try:
                with open(self.output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}
            existing_data[action_id] = data
            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved basic details for Action ID {action_id} to '{self.output_file}'")
        except Exception as e:
            self.logger.error(f"Error saving data for Action ID {action_id}: {e}")