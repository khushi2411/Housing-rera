import json

def load_json(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        return json.load(f)

def ensure_dict(data):
    """
    Convert data to a dictionary if it is a list.
    Assumes that each item in the list is a dict with an "ActionID" key.
    If data is already a dict, return it unchanged.
    """
    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        new_dict = {}
        for item in data:
            if isinstance(item, dict) and "ActionID" in item:
                new_dict[item["ActionID"]] = item
        return new_dict
    else:
        return {}

# Load each JSON file
project_details = load_json("projectdetails.json")
project_schedule = load_json("projectschedule.json")
inventory = load_json("inventory.json")
tower_data = load_json("tower_data.json")
floorplan = load_json("floorplan.json")

# Ensure all files are dictionaries keyed by project ID.
project_details = ensure_dict(project_details)
project_schedule = ensure_dict(project_schedule)
inventory = ensure_dict(inventory)
tower_data = ensure_dict(tower_data)
floorplan = ensure_dict(floorplan)

# Get a set of all unique keys (project IDs) from all files.
all_keys = set()
for d in [project_details, project_schedule, inventory, tower_data, floorplan]:
    all_keys.update(d.keys())

# Prepare the final consolidated dictionary.
all_projects = {}

for key in all_keys:
    combined_project = {}
    
    # Merge project details if available
    if key in project_details:
        combined_project.update(project_details[key])
    
    # Merge project schedule if available
    if key in project_schedule:
        combined_project.update(project_schedule[key])
    
    # Add inventory list under the key "inventory"
    if key in inventory:
        combined_project["inventory"] = inventory[key]
    
    # Process tower data and floorplan if both exist for this key.
    if key in tower_data and key in floorplan:
        # Extract tower details list from tower_data file
        tower_details = tower_data[key].get("TowerDetails", [])
        floorplans = floorplan[key]
        
        # Check if both lists have the same length
        if len(tower_details) != len(floorplans):
            print(f"Warning: For key {key}, TowerDetails has {len(tower_details)} items "
                  f"but floorplan has {len(floorplans)} items. Proceeding with minimum length.")
        
        merged_towers = []
        # Zip will stop at the shorter of the two lists.
        for td, fp in zip(tower_details, floorplans):
            merged = dict(td)  # copy tower detail data
            merged["floorplan"] = fp  # add corresponding floorplan data
            merged_towers.append(merged)
        
        # Add the merged tower-floorplan objects to the project under the key "towers"
        combined_project["towers"] = merged_towers
    
    # Add the combined data for this project ID into the final dict.
    all_projects[key] = combined_project

# Write the consolidated data to allProjects.json.
with open("allProjects.json", "w", encoding="utf-8") as outfile:
    json.dump(all_projects, outfile, indent=4)

print("Data consolidation complete! Output written to allProjects.json.")
