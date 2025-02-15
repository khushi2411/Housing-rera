import scrapy
import json
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "inventory"
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
        self.output_file = "inventory.json"

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