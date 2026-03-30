from tools.crop_tool import add_crop, get_all_crops, delete_field
from tools.inventory_tool import add_fertilizer, check_fertilizer_stock, delete_fertilizer
from tools.irrigation_tool import activate_sprinkler

def verify_db_ops():
    print("--- Verifying Crop Operations ---")
    # Add a mock crop
    print(add_crop("TestCrop", "Sandy", 5.0))
    print(get_all_crops())
    
    # Try to find the field ID for TestCrop to delete it (this is a bit manual here)
    # In reality, the agent would use get_all_crops to find the ID.
    
    print("\n--- Verifying Inventory Operations ---")
    print(add_fertilizer("TestFertilizer", 50))
    print(check_fertilizer_stock())
    print(delete_fertilizer("TestFertilizer"))
    
    print("\n--- Verifying Irrigation History ---")
    # Assuming there's a field with ID 1
    print(activate_sprinkler(1, 45))

if __name__ == "__main__":
    import traceback
    try:
        verify_db_ops()
    except Exception as e:
        print("Error during verification:")
        traceback.print_exc()
