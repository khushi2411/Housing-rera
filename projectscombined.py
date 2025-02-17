import json

# Helper function to load JSON from a file
def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

# Load each JSON file
project_details = load_json("projectdetails.json")
project_schedule = load_json("projectschedule.json")
inventory = load_json("inventory.json")
tower_data = load_json("tower_data.json")
floorplan = load_json("floorplan.json")

# Get a set of all unique keys (project IDs) from all files
all_keys = set()
for d in [project_details, inventory, tower_data, floorplan,project_schedule]:
    all_keys.update(d.keys())

# Prepare the final consolidated dictionary
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
    
    # Process tower data and floorplan if both exist for this key
    if key in tower_data and key in floorplan:
        # Extract tower details list from tower_data file
        tower_details = tower_data[key].get("TowerDetails", [])
        floorplans = floorplan[key]
        
        # Check if both lists have the same length
        if len(tower_details) != len(floorplans):
            print(f"Warning: For key {key}, TowerDetails has {len(tower_details)} items "
                  f"but floorplan has {len(floorplans)} items. Proceeding with minimum length.")
        
        merged_towers = []
        # Zip will stop at the shorter of the two lists
        for td, fp in zip(tower_details, floorplans):
            merged = dict(td)  # copy tower detail data
            merged["floorplan"] = fp  # add corresponding floorplan data
            merged_towers.append(merged)
        
        # Add the merged tower-floorplan objects to the project under the key "towers"
        combined_project["towers"] = merged_towers
    
    # Add the combined data for this project ID into the final dict
    all_projects[key] = combined_project

# Write the consolidated data to allProjects.json
with open("allProjects.json", "w") as outfile:
    json.dump(all_projects, outfile, indent=4)

print("Data consolidation complete! Output written to allProjects.json.")
