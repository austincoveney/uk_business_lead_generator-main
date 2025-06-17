"""UK Business Types and Categories for Auto-complete

Comprehensive list of UK business types organized by categories
for enhanced search functionality and auto-complete features.
"""

# Primary business categories with subcategories
BUSINESS_CATEGORIES = {
    "Food & Beverage": [
        "Restaurant", "Pub", "Bar", "Cafe", "Coffee Shop", "Takeaway",
        "Fast Food", "Fine Dining", "Bakery", "Delicatessen", "Catering",
        "Food Truck", "Brewery", "Distillery", "Wine Bar", "Cocktail Bar",
        "Pizza Restaurant", "Indian Restaurant", "Chinese Restaurant",
        "Italian Restaurant", "Thai Restaurant", "Fish & Chips", "Sandwich Shop"
    ],
    
    "Retail & Shopping": [
        "Clothing Store", "Shoe Shop", "Electronics Store", "Bookstore",
        "Gift Shop", "Toy Store", "Jewellery Store", "Furniture Store",
        "Home Decor", "Garden Centre", "Pet Shop", "Sports Store",
        "Music Store", "Art Gallery", "Antique Shop", "Charity Shop",
        "Department Store", "Supermarket", "Convenience Store", "Pharmacy",
        "Opticians", "Mobile Phone Shop", "Computer Store", "Bike Shop"
    ],
    
    "Health & Beauty": [
        "Hair Salon", "Barber Shop", "Beauty Salon", "Nail Salon", "Spa",
        "Massage Therapy", "Physiotherapy", "Dental Practice", "GP Surgery",
        "Veterinary Clinic", "Optometrist", "Chiropractor", "Osteopath",
        "Acupuncture", "Cosmetic Surgery", "Tattoo Parlour", "Gym",
        "Fitness Studio", "Yoga Studio", "Personal Training", "Pilates Studio"
    ],
    
    "Professional Services": [
        "Solicitor", "Accountant", "Estate Agent", "Insurance Broker",
        "Financial Advisor", "Mortgage Broker", "Tax Advisor", "Consultant",
        "Marketing Agency", "Advertising Agency", "PR Agency", "Web Design",
        "Graphic Design", "Architect", "Surveyor", "Engineer", "IT Support",
        "Software Development", "Digital Marketing", "SEO Agency",
        "Translation Services", "Recruitment Agency", "Training Provider"
    ],
    
    "Construction & Trade": [
        "Builder", "Plumber", "Electrician", "Carpenter", "Painter", "Decorator",
        "Roofer", "Glazier", "Flooring", "Kitchen Fitter", "Bathroom Fitter",
        "Landscaper", "Gardener", "Tree Surgeon", "Pest Control", "Locksmith",
        "Security Systems", "CCTV Installation", "Alarm Systems", "Scaffolding",
        "Demolition", "Groundworks", "Drainage", "Heating Engineer",
        "Air Conditioning", "Solar Panel Installation"
    ],
    
    "Automotive": [
        "Car Dealer", "Used Car Sales", "Car Rental", "Garage", "MOT Centre",
        "Car Wash", "Petrol Station", "Tyre Fitting", "Car Parts", "Mechanic",
        "Body Shop", "Car Valeting", "Driving School", "Motorcycle Dealer",
        "Bike Repair", "Car Insurance", "Breakdown Recovery", "Parking",
        "Car Leasing", "Vehicle Finance", "HGV Training", "Taxi Service"
    ],
    
    "Education & Training": [
        "Primary School", "Secondary School", "College", "University",
        "Nursery", "Childcare", "Tutoring", "Music Lessons", "Dance School",
        "Martial Arts", "Language School", "Driving Instructor", "Training Centre",
        "Vocational Training", "Adult Education", "Online Learning",
        "Educational Consultant", "Special Needs Education", "After School Club"
    ],
    
    "Entertainment & Leisure": [
        "Cinema", "Theatre", "Museum", "Art Gallery", "Bowling Alley",
        "Arcade", "Escape Room", "Laser Tag", "Paintball", "Go Karting",
        "Mini Golf", "Sports Club", "Golf Course", "Tennis Club", "Swimming Pool",
        "Leisure Centre", "Nightclub", "Live Music Venue", "Comedy Club",
        "Event Venue", "Wedding Venue", "Conference Centre", "Hotel", "B&B",
        "Holiday Park", "Camping", "Travel Agent", "Tour Operator"
    ],
    
    "Technology & IT": [
        "Software Company", "Web Development", "App Development", "IT Consultancy",
        "Computer Repair", "Data Recovery", "Cloud Services", "Cybersecurity",
        "Network Solutions", "Telecommunications", "Internet Provider",
        "Tech Support", "Digital Agency", "E-commerce", "Online Marketing",
        "Social Media Management", "Content Creation", "Video Production",
        "Photography", "Printing Services", "3D Printing", "Electronics Repair"
    ],
    
    "Manufacturing & Industrial": [
        "Factory", "Warehouse", "Distribution", "Logistics", "Packaging",
        "Food Processing", "Textile Manufacturing", "Metal Working",
        "Plastic Manufacturing", "Chemical Processing", "Pharmaceutical",
        "Engineering", "Machinery", "Tools", "Industrial Equipment",
        "Quality Control", "Research & Development", "Laboratory",
        "Testing Services", "Certification", "Import/Export", "Freight"
    ],
    
    "Financial Services": [
        "Bank", "Building Society", "Credit Union", "Investment Firm",
        "Pension Provider", "Insurance Company", "Loan Company",
        "Currency Exchange", "Financial Planning", "Wealth Management",
        "Debt Management", "Payroll Services", "Bookkeeping", "Audit Firm",
        "Tax Services", "Business Finance", "Venture Capital", "Private Equity"
    ],
    
    "Property & Real Estate": [
        "Estate Agent", "Property Management", "Letting Agent", "Property Developer",
        "Property Investment", "Commercial Property", "Residential Sales",
        "Property Valuation", "Property Maintenance", "Facilities Management",
        "Cleaning Services", "Security Services", "Property Insurance",
        "Mortgage Broker", "Conveyancing", "Property Law", "Surveying"
    ]
}

# Flatten all business types for quick search
ALL_BUSINESS_TYPES = []
for category, types in BUSINESS_CATEGORIES.items():
    ALL_BUSINESS_TYPES.extend(types)

# Sort alphabetically for better user experience
ALL_BUSINESS_TYPES.sort()

# Popular/trending business types (for suggestions)
POPULAR_TYPES = [
    "Restaurant", "Cafe", "Hair Salon", "Gym", "Dentist", "Solicitor",
    "Accountant", "Estate Agent", "Plumber", "Electrician", "Builder",
    "Car Garage", "Takeaway", "Pub", "Shop", "Office", "Clinic", "School"
]

# UK-specific business types
UK_SPECIFIC_TYPES = [
    "Fish & Chips", "Pub", "Betting Shop", "Post Office", "Charity Shop",
    "Building Society", "GP Surgery", "Council Services", "NHS Trust",
    "Parish Council", "Village Hall", "Cricket Club", "Football Club",
    "Working Men's Club", "Conservative Club", "British Legion",
    "Jobcentre Plus", "Citizens Advice", "Housing Association"
]

def get_business_suggestions(query: str, limit: int = 10) -> list:
    """Get business type suggestions based on user input
    
    Args:
        query: User's search query
        limit: Maximum number of suggestions to return
        
    Returns:
        List of matching business types
    """
    if not query:
        return POPULAR_TYPES[:limit]
    
    query_lower = query.lower()
    suggestions = []
    
    # Exact matches first
    for business_type in ALL_BUSINESS_TYPES:
        if business_type.lower().startswith(query_lower):
            suggestions.append(business_type)
    
    # Partial matches
    for business_type in ALL_BUSINESS_TYPES:
        if query_lower in business_type.lower() and business_type not in suggestions:
            suggestions.append(business_type)
    
    return suggestions[:limit]

def get_category_for_type(business_type: str) -> str:
    """Get the category for a specific business type
    
    Args:
        business_type: The business type to categorize
        
    Returns:
        Category name or 'Other' if not found
    """
    for category, types in BUSINESS_CATEGORIES.items():
        if business_type in types:
            return category
    return "Other"