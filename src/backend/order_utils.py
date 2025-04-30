import re
from typing import List, Tuple, Optional, Dict, Union

VALID_MENU_ITEMS = {
    'biryani', 'chicken_biryani', 'beef_biryani', 'mutton_biryani',
    'karahi', 'chicken_karahi', 'beef_karahi', 'mutton_karahi',
    'samosa', 'vegetable_samosa', 'aloo_samosa',
    'pepsi', 'cola', 'cold_drink',
    'burger', 'beef_burger', 'chicken_burger',
    'kebab', 'seekh_kebab', 'beef_kebab', 'chicken_kebab',
    'naan', 'garlic_naan', 'tandoori_naan'
}

def normalize_item_name(item_name: str) -> str:
    """Normalize item names to standard database format"""
    item_name = item_name.lower().strip()
    item_name = re.sub(r'\s+and$', '', item_name)
    item_name = re.sub(r'\s+', '_', item_name)  # Replace spaces with underscores
    
    item_mapping = {
        'biriyani': 'biryani', 'biryan': 'biryani',
        'cola': 'pepsi', 'cold_drink': 'pepsi',
        'seekh_kebab': 'kebab', 'seekh': 'kebab',
        'pepis': 'pepsi', 'pepsi': 'pepsi',
        'chickenbiryani': 'chicken_biryani',
        'beefburger': 'beef_burger'
    }
    
    if item_name in VALID_MENU_ITEMS:
        return item_name
    
    for valid_item in VALID_MENU_ITEMS:
        if item_name in valid_item or valid_item in item_name:
            return valid_item
    
    return item_mapping.get(item_name, item_name)

def extract_dish_item(user_input: str) -> Optional[str]:
    """Extract dish item from user input with improved price query handling"""
    # Handle price queries first
    if is_price_query(user_input):
        price_pattern = r'(?:price of|cost of|how much is|tell me the price of)\s+([a-zA-Z\s]+)'
        match = re.search(price_pattern, user_input.lower())
        if match:
            item = match.group(1).strip()
            return normalize_item_name(item)
    
    # Handle other patterns
    patterns = [
        r'(?:is|are)\s+([a-zA-Z\s]+)\s+(?:available|in stock|left)',
        r'(?:tell me about|what is|what\'s)\s+([a-zA-Z\s]+)',
        r'([a-zA-Z\s]+)\s+(?:price|cost|availability)',
        r'(?:i\'d like|i want)\s+([a-zA-Z\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            item = match.group(1).strip()
            return normalize_item_name(item)
    return None

def is_price_query(text: str) -> bool:
    """Check if user is asking about price (more precise)"""
    price_phrases = [
        'price of', 'cost of', 'how much is', 
        'what is the price', "what's the price",
        'how much for', 'price for', 'how much does',
        'what does cost', 'tell me the price of'
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
        'do you serve'
    ]
    return any(phrase in text.lower() for phrase in stock_phrases)

def is_technical_support_request(text: str) -> bool:
    """Check if user is asking for technical support"""
    support_phrases = [
        'technical help', 'technical problem', 'contact support',
        'something is wrong', 'technical issue', 'need support',
        'not working', 'need help', 'have a problem'
    ]
    return any(phrase in text.lower() for phrase in support_phrases)

def extract_item_and_intent(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract both item and intent type from query"""
    item = extract_dish_item(text)
    if is_price_query(text):
        return item, 'price'
    elif is_stock_query(text):
        return item, 'stock'
    elif is_technical_support_request(text):
        return None, 'technical_support'
    return item, None

def extract_order_details(user_input: str) -> List[Tuple[str, int]]:
    """Extract order details from user input"""
    pattern = r'(\d+)\s+([a-zA-Z_\s]+?)(?=\s*\d+|and\s*\d+|$)'
    matches = re.finditer(pattern, user_input.lower())
    
    items = []
    for match in matches:
        try:
            quantity = int(match.group(1))
            item = match.group(2).strip()
            item = re.sub(r'\s+and$', '', item).strip()
            if quantity > 0 and item:
                items.append((item, quantity))
        except (ValueError, IndexError):
            continue
    
    combined_items: Dict[str, int] = {}
    for item_name, quantity in items:
        normalized_name = normalize_item_name(item_name)
        if normalized_name:
            combined_items[normalized_name] = combined_items.get(normalized_name, 0) + quantity
    
    return list(combined_items.items())

def format_order_items(items: List[Tuple[str, int]]) -> str:
    """Format order items for display"""
    if not items:
        return ""
    
    item_units = {
        "biryani": "🍛 plate", "chicken_biryani": "🍛 plate",
        "karahi": "🍲 bowl", "samosa": "🥟 piece",
        "pepsi": "🥤 bottle", "burger": "🍔 burger",
        "kebab": "🍢 skewer", "naan": "🫓 naan"
    }
    
    formatted = []
    for name, qty in items:
        display_name = name.replace('_', ' ')
        unit = item_units.get(name, display_name)
        formatted.append(f"{qty} {unit}{'s' if qty > 1 and not name.endswith('s') else ''}")
    
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
        'technical': ['technical', 'tech', 'problem', 'issue'],
        'account': ['account', 'login', 'password'],
        'device': ['device', 'phone', 'computer', 'tablet']
    }
    
    text_lower = text.lower()
    issue_type = None
    for key, keywords in issue_types.items():
        if any(keyword in text_lower for keyword in keywords):
            issue_type = key
            break
    
    return issue_type, text_lower