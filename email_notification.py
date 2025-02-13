import time
import os
import json
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import Mailjet client
from mailjet_rest import Client

# ---------- Helper Functions for Persistence using JSON ----------

def load_stored_identifier(filename="stored_identifier.json"):
    """Load the stored RERA ID from a JSON file (if it exists)."""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("stored_identifier")
            except json.JSONDecodeError:
                print("JSON decode error. Returning None.")
                return None
    return None

def save_stored_identifier(identifier, filename="stored_identifier.json"):
    """Save the given RERA ID to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"stored_identifier": identifier}, f, indent=4)

def save_new_projects(projects, filename="new_projects.json"):
    """
    Save the list of new project details to a JSON file.
    Each project is a dictionary with keys: reg_no, promoter_name, project_name.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=4)

# ---------- Mailjet Email Sending Function ----------

def send_email_with_mailjet(file_path, sender_email, receiver_email, subject, body,
                            mailjet_api_key, mailjet_api_secret):
    """
    Send an email with the JSON file attached using Mailjet.
    
    Parameters:
        file_path (str): Path to the attachment (JSON file).
        sender_email (str): Sender's email address (should be a verified sender in Mailjet).
        receiver_email (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body (plain text).
        mailjet_api_key (str): Your Mailjet API key.
        mailjet_api_secret (str): Your Mailjet API secret.
    """
    # Read file content and encode it in base64
    with open(file_path, "rb") as f:
        file_data = f.read()
    encoded_file = base64.b64encode(file_data).decode('utf-8')
    
    # Initialize Mailjet client
    mailjet = Client(auth=(mailjet_api_key, mailjet_api_secret), version='v3.1')
    
    # Prepare the email data with attachment using the correct keys
    data = {
        'Messages': [
            {
                "From": {
                    "Email": sender_email,
                    "Name": "No Reply"  # You can change the sender name as desired
                },
                "To": [
                    {
                        "Email": receiver_email,
                        "Name": "Recipient"
                    }
                ],
                "Subject": subject,
                "TextPart": body,
                "HTMLPart": f"<p>{body}</p>",
                "Attachments": [
                    {
                        "ContentType": "application/json",
                        "Filename": os.path.basename(file_path),
                        "Base64Content": encoded_file
                    }
                ]
            }
        ]
    }
    
    # Send the email
    result = mailjet.send.create(data=data)
    print("Mailjet response status code:", result.status_code)
    print("Mailjet response:", result.json())

# ------------------- Main Script -------------------

def main():
    # Load the stored identifier from file; if not found, use a default value.
    stored_identifier = load_stored_identifier() or "PRM/KA/RERA/1251/446/PR/050225/007481"
    print("Loaded stored identifier:", stored_identifier)
    
    # Setup Chrome options (adjust as needed)
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Uncomment to run headless
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # ------------------------------------------------------------
        # 1. Navigate to the RERA projects page
        # ------------------------------------------------------------
        URL = 'https://rera.karnataka.gov.in/viewAllProjects'
        driver.get(URL)
        print("Navigated to the RERA projects URL.")
        
        # ------------------------------------------------------------
        # 2. Set up the initial search by entering "Bengaluru Urban"
        #    in the district input field (ID: projectDist)
        # ------------------------------------------------------------
        district_input = wait.until(EC.presence_of_element_located((By.ID, "projectDist")))
        district_value = "Bengaluru Urban"
        readonly_attr = district_input.get_attribute("readonly")
        if readonly_attr or not district_input.is_enabled():
            print("District input field is read-only or disabled; using JavaScript to set its value.")
            driver.execute_script("arguments[0].value = arguments[1];", district_input, district_value)
        else:
            try:
                district_input.clear()
                district_input.send_keys(district_value)
            except Exception as e:
                print("Standard method failed, falling back to JavaScript. Exception:", e)
                driver.execute_script("arguments[0].value = arguments[1];", district_input, district_value)
        print("Entered district:", district_value)
        
        # ------------------------------------------------------------
        # 3. Click the search button (assumed to have the class 'btn-style')
        # ------------------------------------------------------------
        search_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-style")))
        search_button.click()
        print("Clicked search button.")
        
        # ------------------------------------------------------------
        # 4. Wait for the approved projects table to load (ID: approvedTable)
        # ------------------------------------------------------------
        wait.until(EC.presence_of_element_located((By.XPATH, '//table[@id="approvedTable"]')))
        print("Approved projects table loaded.")
        
        # ------------------------------------------------------------
        # 5. Trigger table sorting:
        #    a) Click the "STATUS" header once.
        #    b) Click the "APPROVED ON" header twice.
        # ------------------------------------------------------------
        status_header = wait.until(EC.element_to_be_clickable((By.XPATH, "//th[contains(text(), 'STATUS')]")))
        status_header.click()
        print("Clicked 'STATUS' header once.")
        time.sleep(2)  # Allow time for sorting animation
        approved_header = wait.until(EC.element_to_be_clickable((By.XPATH, "//th[contains(text(), 'APPROVED ON')]")))
        approved_header.click()
        time.sleep(2)
        approved_header.click()
        print("Clicked 'APPROVED ON' header twice.")
        time.sleep(2)
        
        # ------------------------------------------------------------
        # 6. Process all rows in the table.
        #    For each row, if the RERA ID (column 3, index 2) is not the stored one,
        #    extract and save its details; stop processing when the stored identifier is encountered.
        # ------------------------------------------------------------
        rows = driver.find_elements(By.XPATH, '//table[@id="approvedTable"]/tbody/tr')
        print("Total rows found in table:", len(rows))
        new_projects = []
        
        # Iterate over rows from top (newest) downwards
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 6:
                continue  # Skip rows that do not have enough cells
            current_rera_id = cells[2].text.strip()
            if current_rera_id == stored_identifier:
                # Found the stored project; assume all subsequent rows are already processed.
                break
            # Otherwise, treat as a new project.
            reg_no = current_rera_id  # Column index 2
            promoter_name = cells[4].text.strip()  # Column index 4
            project_name = cells[5].text.strip()   # Column index 5
            new_projects.append({
                "reg_no": reg_no,
                "promoter_name": promoter_name,
                "project_name": project_name
            })
        
        # Print details for all new projects.
        if new_projects:
            print("New projects found:")
            for proj in new_projects:
                print("Scraped Details:")
                print("  Registration No:", proj["reg_no"])
                print("  Promoter Name:  ", proj["promoter_name"])
                print("  Project Name:   ", proj["project_name"])
                print("-" * 40)
        else:
            print("No new projects detected.")
        
        # ------------------------------------------------------------
        # 7. Update the stored identifier with the RERA ID of the first row.
        # ------------------------------------------------------------
        if rows:
            new_stored = rows[0].find_elements(By.TAG_NAME, "td")[2].text.strip()
            save_stored_identifier(new_stored)
            print("Stored identifier updated to:", new_stored)
        
        # ------------------------------------------------------------
        # 8. Save new projects details to a JSON file and send email if new projects exist.
        # ------------------------------------------------------------
        if new_projects:
            json_file = "new_projects.json"
            save_new_projects(new_projects, json_file)
            print("New projects saved to", json_file)
            
            # Email configuration for Mailjet:
            sender_email = "khushiatrey011@gmail.com"       
            receiver_email = "khushi@truestate.in",    
            subject = "New RERA Projects Update"
            body = "Please find attached the new RERA projects details."
            
            # Your Mailjet API credentials (replace with your own)
            mailjet_api_key = "ecad4f02175cc06bb5af8c45b1ed11b0"
            mailjet_api_secret = "05a81d3b2447bb0d73eb936fa680224e"
            
            # Send the email with the JSON file attached using Mailjet
            send_email_with_mailjet(json_file, sender_email, receiver_email, subject, body,
                                    mailjet_api_key, mailjet_api_secret)
    
    except Exception as e:
        print("An error occurred:", e)
    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()
