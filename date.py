import scrapy
import csv
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
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
            ),
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.input_file = "rera_ids.csv"
        # Two different output files: one for new website pages (with inventory) and one for old website pages.
        self.new_output_file = "new_format.json"
        self.old_output_file = "old_format.json"

    def load_action_ids(self):
        """
        Loads a list of action_ids from self.input_file (CSV).
        """
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header if present
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"Input file {self.input_file} not found.")
        return action_ids

    def start_requests(self):
        """
        Yields POST requests to the start URL for each action_id.
        """
        action_ids = self.load_action_ids()
        for action_id in action_ids:
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_page,
                meta={'action_id': action_id}
            )

    def parse_page(self, response):
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.body, encoding="utf-8")

        # -----------------------------------------------------------
        # 1. Check if an inventory table exists.
        # -----------------------------------------------------------
        # Presence of an inventory table indicates a "new website" page.
        inventory_table = scrapy_response.xpath(
            '//table[contains(@class,"table-bordered")][.//th[contains(normalize-space(.), "Type of Inventory")]]'
        )
        is_new_website = bool(inventory_table)

        # -----------------------------------------------------------
        # 2. Extract Registration Number from the span element.
        #    This looks for a <span> with class "pull-right user_name" that contains the text
        #    "Registration Number :" and then extracts the text from the nested <b> element.
        # -----------------------------------------------------------
        registration_number = scrapy_response.xpath(
            '//span[contains(@class, "user_name") and contains(., "Registration Number")]/b/text()'
        ).get()
        if registration_number:
            registration_number = registration_number.strip()

        # -----------------------------------------------------------
        # 3. Extract Approved Dates from the Registration/Extensions table.
        #    Expected columns might be: Registration/Extensions | Start Date | Proposed Completion Date | Certificate/Order
        # -----------------------------------------------------------
        approved_dates = {}
        registration_extensions = []
        regext_table = scrapy_response.xpath(
            '//table[contains(@class,"table-bordered") and contains(., "Registration/Extensions")]/tbody'
        )
        if regext_table:
            rows = regext_table.xpath('./tr')
            for tr in rows:
                cols = tr.xpath('.//td//text()').getall()
                cols = [x.strip() for x in cols if x.strip()]
                if len(cols) >= 3:
                    registration_extensions.append({
                        "Status": cols[0],
                        "StartDate": cols[1],
                        "ProposedCompletionDate": cols[2],
                        "CertificateOrder": cols[3] if len(cols) >= 4 else ""
                    })
        else:
            self.logger.warning(f"[{action_id}] No Registration/Extensions table found.")

        if registration_extensions:
            # We use the first row's dates as the approved dates.
            reg = registration_extensions[0]
            approved_dates = {
                "StartDate": reg.get("StartDate", ""),
                "ProposedCompletionDate": reg.get("ProposedCompletionDate", "")
            }
            # In case the registration number wasn't found in the span,
            # fallback to using the CertificateOrder or Status from the table.
            if not registration_number:
                registration_number = reg.get("CertificateOrder") or reg.get("Status", "")
        else:
            # If no registration extension data is available, leave approved_dates empty.
            approved_dates = {}

        # -----------------------------------------------------------
        # 4. Prepare minimal output data.
        # Only include action_id, RegistrationNumber, and ApprovedDates.
        # -----------------------------------------------------------
        output_data = {
            "action_id": action_id,
            "RegistrationNumber": registration_number,
            "ApprovedDates": approved_dates
        }

        # -----------------------------------------------------------
        # 5. Save to the appropriate JSON file.
        # Pages with an inventory table are considered "new website" pages.
        # -----------------------------------------------------------
        output_file = self.new_output_file if is_new_website else self.old_output_file
        self.save_to_json(output_file, action_id, output_data)

    def save_to_json(self, output_file, action_id, data):
        """
        Appends/updates the data in the given JSON file, keyed by action_id.
        """
        try:
            # Load existing data if the file exists.
            try:
                with open(output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}

            existing_data[action_id] = data

            # Write updated data back to the file.
            with open(output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)

            self.logger.info(f"[{action_id}] Data saved to {output_file}.")
        except Exception as e:
            self.logger.error(f"[{action_id}] Error saving data: {e}")
