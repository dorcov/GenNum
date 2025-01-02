import random 
import pandas as pd

OPERATOR_PREFIXES = {
    'Orange': ['60','61','62','63','68','69'],
    'Moldcell': ['76','78','79'],
    'Unite': ['67'],
    'Moldtelecom': ['2']
}

def clean_phone_number(number):
    """Convert number to 8-digit string, handling NaN and invalid values"""
    if pd.isna(number):
        return None
    try:
        # Remove any non-digit characters and convert to int
        cleaned = ''.join(filter(str.isdigit, str(number)))
        if not cleaned:
            return None
        return str(int(cleaned)).zfill(8)
    except ValueError:
        return None

def clean_source_number(number):
    """Clean source number format - remove leading zeros while preserving valid prefixes"""
    if pd.isna(number):
        return None
    try:
        # Convert to string and remove any non-digit characters
        cleaned = ''.join(filter(str.isdigit, str(number)))
        
        # Remove leading zeros while keeping valid prefixes
        if len(cleaned) >= 8:
            # Check if starts with valid prefix
            for operator, prefixes in OPERATOR_PREFIXES.items():
                if any(cleaned.startswith(prefix) for prefix in prefixes):
                    # Keep prefix and ensure 8 digits
                    return cleaned[:8]
            
            # If no valid prefix found, try to fix it
            if cleaned.startswith('0'):
                cleaned = cleaned[1:]  # Remove single leading zero
            return cleaned[:8].zfill(8)
            
        return cleaned.zfill(8)
    except ValueError:
        return None

def format_tip_date(tip):
    """Convert date string to MMM/YYYY format"""
    if isinstance(tip, str) and tip == "Număr nou":
        return tip
    try:
        date = pd.to_datetime(tip)
        return date.strftime('%b/%Y')
    except:
        return tip

def generate_number_variation(base_number, digits_to_vary, operator):
    """Generate variation of base number by changing X random digits"""
    # Ensure valid prefix
    prefix = base_number[:2]
    if not any(prefix.startswith(p) for p in OPERATOR_PREFIXES[operator]):
        return None
        
    remaining_digits = base_number[2:]
    
    # Choose random positions to modify
    positions = random.sample(range(len(remaining_digits)), digits_to_vary)
    
    # Create new number ensuring no invalid leading zeros
    new_digits = list(remaining_digits)
    for pos in positions:
        new_digits[pos] = str(random.randint(0,9))
    
    new_number = prefix + ''.join(new_digits)
    
    # Validate final number format
    if len(new_number) != 8 or not any(new_number.startswith(p) for p in OPERATOR_PREFIXES[operator]):
        return None
        
    return new_number

def load_blacklist():
    """Load blacklisted numbers from Excel"""
    try:
        df_blacklist = pd.read_excel('blacklist.xlsx')
        return set(df_blacklist['Phone'].astype(str).apply(clean_source_number))
    except FileNotFoundError:
        return set()

def create_seed_numbers(missing_operator):
    """Create seed numbers for missing operator type"""
    seeds = []
    prefixes = OPERATOR_PREFIXES[missing_operator]
    
    for prefix in prefixes:
        # Create 2 seed numbers for each prefix
        for _ in range(2):
            number = prefix + ''.join(str(random.randint(0,9)) for _ in range(8-len(prefix)))
            seeds.append({
                'Phone': number,
                'Tip': 'Seed',
                'Operator': missing_operator
            })
    return seeds

def generate_variations(df_source, variations_per_number=5, digits_to_vary=3):
    """Generate variations including missing operators"""
    
    # Find missing operators
    source_operators = set(df_source['Operator'].unique())
    all_operators = set(OPERATOR_PREFIXES.keys())
    missing_operators = all_operators - source_operators
    
    # Add seed numbers for missing operators
    seed_numbers = []
    for operator in missing_operators:
        seed_numbers.extend(create_seed_numbers(operator))
    
    if seed_numbers:
        df_seeds = pd.DataFrame(seed_numbers)
        df_source = pd.concat([df_source, df_seeds], ignore_index=True)
    
    # Load blacklist
    blacklist = load_blacklist()
    
    # Clean source numbers with fixed function
    df_source['Phone'] = df_source['Phone'].apply(clean_source_number)
    df_source['Tip'] = df_source['Tip'].apply(format_tip_date)
    df_source = df_source.dropna(subset=['Phone'])
    
    # Additional validation - remove any numbers still having invalid format
    df_source = df_source[df_source['Phone'].apply(lambda x: 
        any(x.startswith(p) for op in OPERATOR_PREFIXES.values() for p in op))]
    
    # Remove blacklisted numbers from source
    df_source = df_source[~df_source['Phone'].isin(blacklist)]
    
    new_numbers = []
    used_numbers = set(df_source['Phone'].values)
    
    for _, row in df_source.iterrows():
        base_number = row['Phone']
        operator = row['Operator']
        
        if not any(base_number.startswith(prefix) for prefix in OPERATOR_PREFIXES[operator]):
            continue
            
        counter = 0
        attempts = 0
        max_attempts = variations_per_number * 10
        
        while counter < variations_per_number and attempts < max_attempts:
            new_number = generate_number_variation(base_number, digits_to_vary, operator)
            
            if new_number and new_number not in used_numbers and new_number not in blacklist:
                used_numbers.add(new_number)
                new_numbers.append({
                    'Phone': new_number,
                    'Tip': 'Număr nou',
                    'Operator': operator
                })
                counter += 1
            attempts += 1
    
    df_new = pd.DataFrame(new_numbers)
    df_combined = pd.concat([df_source, df_new], ignore_index=True)
    return df_combined.sample(frac=1).reset_index(drop=True)

def main():
    try:
        df_source = pd.read_excel('source_numbers.xlsx')
        variations = int(input("Variations per number: "))
        digits_to_vary = int(input("Number of digits to vary (1-6): "))
        
        if not 1 <= digits_to_vary <= 6:
            raise ValueError("Must vary between 1 and 6 digits")
            
        df_result = generate_variations(df_source, variations, digits_to_vary)
        df_result.to_excel('generated_numbers.xlsx', index=False)
        print(f"Generated {len(df_result)} total numbers")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()