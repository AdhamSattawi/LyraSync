from enum import Enum


class Profession(str, Enum):
    # --- Construction & Building Trades ---
    PLUMBER = "plumber"
    ELECTRICIAN = "electrician"
    CARPENTER = "carpenter"
    ROOFER = "roofer"
    PAVER = "paver"
    CONCRETE = "concrete"
    TILER = "tiler"
    BRICKLAYER = "bricklayer"
    PLASTERER = "plasterer"
    GLAZIER = "glazier"
    INSULATION = "insulation"
    SCAFFOLDER = "scaffolder"
    DEMOLITION = "demolition"
    GENERAL_CONTRACTOR = "general_contractor"

    # --- Mechanical & HVAC ---
    HVAC = "hvac"
    BOILER_ENGINEER = "boiler_engineer"
    REFRIGERATION = "refrigeration"
    FIRE_PROTECTION = "fire_protection"

    # --- Home & Property Services ---
    PAINTER = "painter"
    LANDSCAPER = "landscaper"
    CLEANER = "cleaner"
    HANDYMAN = "handyman"
    LOCKSMITH = "locksmith"
    POOL_SERVICE = "pool_service"
    PEST_CONTROL = "pest_control"
    WINDOW_CLEANING = "window_cleaning"
    GUTTER_CLEANING = "gutter_cleaning"
    PRESSURE_WASHING = "pressure_washing"
    TREE_SERVICE = "tree_service"
    FENCING = "fencing"
    GARAGE_DOOR = "garage_door"
    FLOORING = "flooring"
    APPLIANCE_REPAIR = "appliance_repair"
    FURNITURE_REPAIR = "furniture_repair"
    INTERIOR_DESIGNER = "interior_designer"

    # --- Automotive ---
    VEHICLE_REPAIR = "vehicle_repair"
    VEHICLE_PAINTING = "vehicle_painting"
    VEHICLE_WASHING = "vehicle_washing"
    VEHICLE_TOWING = "vehicle_towing"
    AUTO_ELECTRICIAN = "auto_electrician"
    MOT_TESTER = "mot_tester"

    # --- Welding & Metalwork ---
    WELDER = "welder"
    BLACKSMITH = "blacksmith"
    SHEET_METAL = "sheet_metal"

    # --- Health & Wellness ---
    DOCTOR = "doctor"
    DENTIST = "dentist"
    PHYSIOTHERAPIST = "physiotherapist"
    CHIROPRACTOR = "chiropractor"
    OPTICIAN = "optician"
    PERSONAL_TRAINER = "personal_trainer"
    MASSAGE_THERAPIST = "massage_therapist"
    NUTRITIONIST = "nutritionist"

    # --- Legal & Finance ---
    LAWYER = "lawyer"
    ACCOUNTANT = "accountant"
    FINANCIAL_ADVISOR = "financial_advisor"
    TAX_CONSULTANT = "tax_consultant"
    BOOKKEEPER = "bookkeeper"
    REAL_ESTATE_AGENT = "real_estate_agent"

    # --- Pets ---
    PET_SITTER = "pet_sitter"
    PET_GROOMER = "pet_groomer"
    VETERINARIAN = "veterinarian"
    DOG_TRAINER = "dog_trainer"

    # --- Technology ---
    SOFTWARE_DEVELOPER = "software_developer"
    WEB_DEVELOPER = "web_developer"
    MOBILE_DEVELOPER = "mobile_developer"
    IT_SUPPORT = "it_support"
    NETWORK_ENGINEER = "network_engineer"
    DATA_ANALYST = "data_analyst"
    DATA_SCIENTIST = "data_scientist"
    MACHINE_LEARNING_ENGINEER = "machine_learning_engineer"
    CYBERSECURITY = "cybersecurity"

    # --- Creative & Design ---
    WEB_DESIGNER = "web_designer"
    GRAPHIC_DESIGNER = "graphic_designer"
    UI_UX_DESIGNER = "ui_ux_designer"
    PHOTOGRAPHER = "photographer"
    VIDEOGRAPHER = "videographer"

    # --- Marketing & Consulting ---
    SEO_SPECIALIST = "seo_specialist"
    MARKETING_CONSULTANT = "marketing_consultant"
    BUSINESS_CONSULTANT = "business_consultant"
    COPYWRITER = "copywriter"
    SOCIAL_MEDIA_MANAGER = "social_media_manager"

    # --- Events & Catering ---
    CATERER = "caterer"
    EVENT_PLANNER = "event_planner"
    DJ = "dj"
    FLORIST = "florist"

    # --- Education & Tutoring ---
    TUTOR = "tutor"
    DRIVING_INSTRUCTOR = "driving_instructor"
    MUSIC_TEACHER = "music_teacher"

    # --- Catch-all ---
    OTHER = "other"
