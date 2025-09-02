import re
from typing import List, Tuple, Optional, Dict, Union

VALID_MENU_ITEMS = {
    # Appetizers
    'samosa', 'pakora', 'fruit_chaat', 'shami_kebab', 
    
    # Main Course - Original Items
    'biryani', 'chicken_biryani', 'beef_biryani', 'mutton_biryani',
    'karahi', 'chicken_karahi', 'beef_karahi', 'mutton_karahi',
    'burger', 'burgers', 'beef_burger', 'chicken_burger', 'zinger_burger',
    'kebab', 'seekh_kebab', 'beef_kebab', 'chicken_kebab', 'chapli_kebab',
    'naan', 'garlic_naan', 'tandoori_naan',
    
    # Main Course - New Items
    'nihari', 'haleem', 'paya', 'fish_fry', 'malai_boti',
    
    # Pizza Items - ADD THESE!
    'pizza', 'chicken_pizza', 'beef_pizza', 'cheese_pizza', 'margherita_pizza', 'veggie_pizza',
    
    # Desserts
    'kheer', 'jalebi', 'rasmalai', 'chocolate_lava_cake',
    
    # Beverages
    'pepsi', 'cola', 'cold_drink', 'lassi', 'rooh_afza',
    
    # Special Deals
    'biryani_combo', 'bbq_platter', 'nihari_combo', 'zinger_combo', 'dessert_combo'
}
def normalize_item_name(item_name: str) -> str:
    """Normalize item names to standard database format"""
    item_name = item_name.lower().strip()
    item_name = re.sub(r'\s+and$', '', item_name)
    item_name = re.sub(r'\s+', '_', item_name)
    
    item_mapping = {
        # Basics
        'biriyani': 'biryani', 'biryan': 'biryani', 'bryani': 'biryani',
        'chickenbiryani': 'chicken_biryani',
        'beefburger': 'beef_burger',
        
        # Burger variations
        'burgers': 'burger',
        'hamburger': 'burger',
        'hamburgers': 'burger',
        'cheeseburger': 'burger',
        'cheeseburgers': 'burger',
        'beef_burgers': 'beef_burger',
        'chicken_burgers': 'chicken_burger',
        'zinger_burgers': 'zinger_burger',
        
        # Beverages
        'cola': 'pepsi', 'cold_drink': 'pepsi', 'pepis': 'pepsi',
        'coke': 'pepsi', 'soft_drink': 'pepsi', 'soda': 'pepsi',
        
        # Kebabs
        'seekh': 'seekh_kebab', 'seekh_kabab': 'seekh_kebab',
        'chapli': 'chapli_kebab', 'chapli_kabab': 'chapli_kebab',
        'shami': 'shami_kebab', 'shami_kabab': 'shami_kebab',
        
        # Naan
        'naan_bread': 'naan', 'tandoori': 'tandoori_naan',
        
        # Special deals
        'biryani_deal': 'biryani_combo', 'biryani_special': 'biryani_combo',
        'bbq_combo': 'bbq_platter', 'bbq_deal': 'bbq_platter', 'bbq_special': 'bbq_platter',
        'nihari_deal': 'nihari_combo', 'nihari_special': 'nihari_combo',
        'burger_combo': 'zinger_combo', 'burger_deal': 'zinger_combo', 'zinger_deal': 'zinger_combo',
        'dessert_deal': 'dessert_combo', 'sweet_combo': 'dessert_combo',
        
        # Common variations
        'zigar': 'zinger_burger', 'zinger': 'zinger_burger',
        'chicken_karahi': 'karahi', 'mutton_karahi': 'karahi',
        'ruhafza': 'rooh_afza', 'roohafza': 'rooh_afza'
    }
    
    if item_name in VALID_MENU_ITEMS:
        return item_name
    
    if item_name in item_mapping:
        return item_mapping[item_name]
    
    for valid_item in VALID_MENU_ITEMS:
        if item_name in valid_item or valid_item in item_name:
            return valid_item
    
    return item_name

def extract_dish_item(user_input: str) -> Optional[str]:
    """Extract dish item from user input with improved price query handling"""
    if is_price_query(user_input):
        price_pattern = r'(?:price of|cost of|how much is|tell me the price of)\s+([a-zA-Z\s]+)'
        match = re.search(price_pattern, user_input.lower())
        if match:
            item = match.group(1).strip()
            return normalize_item_name(item)
    
    patterns = [
        r'(?:is|are)\s+([a-zA-Z\s]+)\s+(?:available|in stock|left)',
        r'(?:tell me about|what is|what\'s)\s+([a-zA-Z\s]+)',
        r'([a-zA-Z\s]+)\s+(?:price|cost|availability)',
        r'(?:i\'d like|i want)\s+([a-zA-Z\s]+)',
        r'(?:order|get me)\s+([a-zA-Z\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            item = match.group(1).strip()
            return normalize_item_name(item)
    return None

def is_price_query(text: str) -> bool:
    """Check if user is asking about price"""
    price_phrases = [
        'price of', 'cost of', 'how much is', 
        'what is the price', "what's the price",
        'how much for', 'price for', 'how much does',
        'what does cost', 'tell me the price of',
        'what are the rates', 'pricing', 'what would be the cost'
    ]
    text_lower = text.lower()
    return (any(phrase in text_lower for phrase in price_phrases) and 
           not any(word in text_lower for word in ['order', 'want', 'get']))

def is_stock_query(text: str) -> bool:
    """Check if user is asking about stock"""
    stock_phrases = [
        'in stock', 'available', 'do you have',
        'is there any', 'left', 'have any',
        'is available', 'are available', 'can i get',
        'do you serve', 'is it on the menu', 'menu item'
    ]
    return any(phrase in text.lower() for phrase in stock_phrases)

def is_technical_support_request(text: str) -> bool:
    """Check if user is asking for technical support"""
    support_phrases = [
        'technical help', 'technical problem', 'contact support',
        'something is wrong', 'technical issue', 'need support',
        'not working', 'need help', 'have a problem',
        'need technical help', 'facing a technical problem',
        'want to contact support', 'wrong with my device',
        'technical problem', 'need support',
        'technical issue', 'help with my account',
        'device is not working', 'website is not working',
        'app crash', 'login issue', 'payment problem',
        'error message', 'stuck', 'glitch', 'bug',
        'my device', 'my phone', 'my app', 'my website'
    ]
    return any(phrase in text.lower() for phrase in support_phrases)

def is_feedback_request(text: str) -> bool:
    """Check if user is providing feedback"""
    feedback_phrases = [
        'feedback', 'review', 'suggestion',
        'complaint', 'experience',
        'like the', 'not happy', 'satisfied',
        'rude', 'perfect', 'great experience',
        'give feedback', 'share feedback',
        'tell you about my experience',
        'didn\'t like the service',
        'liked the food', 'not happy with my order',
        'satisfied with the service',
        'great experience', 'staff was rude',
        'everything was perfect', 'amazing service',
        'terrible service', 'delicious food'
    ]
    return any(phrase in text.lower() for phrase in feedback_phrases)

def extract_item_and_intent(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract both item and intent type from query"""
    item = extract_dish_item(text)
    if is_price_query(text):
        return item, 'price'
    elif is_stock_query(text):
        return item, 'stock'
    elif is_technical_support_request(text):
        return None, 'technical_support'
    elif is_feedback_request(text):
        return None, 'feedback'
    return item, None

def extract_order_details(user_input: str) -> List[Tuple[str, int]]:
    """Extract order details from user input - SIMPLIFIED DEBUG VERSION"""
    import logging
    logger = logging.getLogger(__name__)
    
    print(f"DEBUG: Original input: '{user_input}'")
    
    user_input = user_input.lower().strip()
    
    # Remove common prefixes
    user_input = re.sub(r'^(i want to order|i want|order|get me|give me)\s+', '', user_input)
    print(f"DEBUG: After cleaning: '{user_input}'")
    
    # SIMPLE APPROACH: Split by spaces and look for number-word patterns
    words = user_input.split()
    print(f"DEBUG: Words: {words}")
    
    items = []
    i = 0
    
    while i < len(words):
        print(f"DEBUG: Checking word {i}: '{words[i]}'")
        
        if words[i].isdigit():
            quantity = int(words[i])
            print(f"DEBUG: Found quantity: {quantity}")
            i += 1
            
            # Collect the next word(s) as item name
            item_words = []
            while i < len(words) and not words[i].isdigit():
                if words[i] not in ['and', 'please', 'thanks', 'thank', 'you']:
                    item_words.append(words[i])
                    print(f"DEBUG: Adding word to item: '{words[i]}'")
                else:
                    print(f"DEBUG: Skipping connector word: '{words[i]}'")
                i += 1
            
            if item_words:
                item_name = ' '.join(item_words)
                print(f"DEBUG: Constructed item name: '{item_name}'")
                
                normalized_item = normalize_item_name(item_name)
                print(f"DEBUG: Normalized item: '{normalized_item}'")
                
                print(f"DEBUG: Is '{normalized_item}' in VALID_MENU_ITEMS? {normalized_item in VALID_MENU_ITEMS}")
                
                if normalized_item in VALID_MENU_ITEMS:
                    items.append((normalized_item, quantity))
                    print(f"DEBUG: Added to items: {quantity} {normalized_item}")
                else:
                    print(f"DEBUG: REJECTED - '{normalized_item}' not in valid items")
                    print(f"DEBUG: Valid items are: {list(VALID_MENU_ITEMS)[:10]}...")  # Show first 10
        else:
            print(f"DEBUG: '{words[i]}' is not a digit, moving to next word")
            i += 1
    
    print(f"DEBUG: Final items before combining: {items}")
    
    # Combine duplicate items
    combined_items = {}
    for item_name, quantity in items:
        if item_name in combined_items:
            combined_items[item_name] += quantity
        else:
            combined_items[item_name] = quantity
    
    final_items = list(combined_items.items())
    print(f"DEBUG: Final combined items: {final_items}")
    
    return final_items


# IMPORTANT: Make sure pizza is in your VALID_MENU_ITEMS
# Add this to test if pizza is the issue:
def check_pizza_in_menu():
    """Check if pizza variants are in VALID_MENU_ITEMS"""
    pizza_variants = ['pizza', 'chicken_pizza', 'beef_pizza', 'cheese_pizza']
    print("Checking pizza in VALID_MENU_ITEMS:")
    for variant in pizza_variants:
        print(f"  {variant}: {'YES' if variant in VALID_MENU_ITEMS else 'NO'}")
    
    print(f"\nAll VALID_MENU_ITEMS: {sorted(VALID_MENU_ITEMS)}")


# Test function with detailed output
def test_specific_case():
    """Test the specific failing case"""
    print("="*60)
    print("TESTING: 'order 2 biryani 2 pepsi 2 pizza'")
    print("="*60)
    
    # First check if all items are in the valid menu
    check_pizza_in_menu()
    print("\n")
    
    # Test the parsing
    test_input = "order 2 biryani 2 pepsi 2 pizza"
    result = extract_order_details(test_input)
    
    print(f"\nFINAL RESULT: {result}")
    print(f"Number of items parsed: {len(result)}")
    
    if len(result) < 3:
        print("❌ PROBLEM: Only got", len(result), "items instead of 3")
        print("This means either:")
        print("1. The parsing logic is wrong, OR")
        print("2. Some items are not in VALID_MENU_ITEMS")
    else:
        print("✅ SUCCESS: Got all 3 items!")


# Run the test
if __name__ == "__main__":
    test_specific_case()

# Update your VALID_MENU_ITEMS by adding these items

def format_order_items(items: List[Tuple[str, int]]) -> str:
    """Format order items for display"""
    if not items:
        return ""
    
    item_units = {
        # Main dishes
        "biryani": "plate", 
        "chicken_biryani": "plate", 
        "beef_biryani": "plate", 
        "mutton_biryani": "plate",
        "karahi": "bowl", 
        "chicken_karahi": "bowl", 
        "mutton_karahi": "bowl",
        "burger": "burger", 
        "beef_burger": "burger", 
        "zinger_burger": "burger",
        "seekh_kebab": "skewer", 
        "chapli_kebab": "piece", 
        "shami_kebab": "piece",
        "naan": "naan", 
        "garlic_naan": "naan", 
        "tandoori_naan": "naan",
        "nihari": "bowl", 
        "haleem": "bowl", 
        "paya": "bowl",
        "fish_fry": "piece", 
        "malai_boti": "piece",
        
        # Appetizers
        "samosa": "piece", 
        "pakora": "plate", 
        "fruit_chaat": "bowl",
        
        # Desserts
        "kheer": "bowl", 
        "jalebi": "piece", 
        "rasmalai": "piece", 
        "chocolate_lava_cake": "slice",
        
        # Beverages
        "pepsi": "bottle", 
        "lassi": "glass", 
        "rooh_afza": "glass",
        
        # Special deals
        "biryani_combo": "combo", 
        "bbq_platter": "platter", 
        "nihari_combo": "combo", 
        "zinger_combo": "combo", 
        "dessert_combo": "combo"
    }
    
    formatted = []
    for name, qty in items:
        display_name = name.replace('_', ' ')
        unit = item_units.get(name, display_name)
        formatted.append(f"{qty} {unit}{'s' if qty > 1 and not unit.endswith('s') else ''}")
    
    if len(formatted) == 1:
        return formatted[0]
    return ", ".join(formatted[:-1]) + f" and {formatted[-1]}"

def extract_order_id(user_input: str) -> Optional[str]:
    """Extract order ID from user input"""
    match = re.search(r'(?:order\s*[#]?\s*|status\s*of\s*|#|id\s*)?(\d{3,})', user_input.lower())
    return match.group(1) if match else None

def extract_support_request_details(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract issue type and description from support request"""
    issue_types = {
        'technical': ['technical', 'tech', 'problem', 'issue', 'not working', 'error', 'bug', 'glitch'],
        'account': ['account', 'login', 'password', 'sign in', 'profile', 'registration', 'signup'],
        'device': ['device', 'phone', 'computer', 'tablet', 'mobile', 'app', 'application'],
        'website': ['website', 'web', 'page', 'site', 'online', 'browser'],
        'payment': ['payment', 'transaction', 'money', 'card', 'credit', 'debit', 'pay'],
        'general': ['question', 'help', 'support', 'assistance', 'information', 'how to']
    }
    
    text_lower = text.lower()
    issue_type = 'general'
    
    for category, keywords in issue_types.items():
        if any(keyword in text_lower for keyword in keywords):
            issue_type = category
            break
    
    return issue_type, text_lower