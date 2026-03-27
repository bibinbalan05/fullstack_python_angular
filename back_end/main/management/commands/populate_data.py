import os
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from main.models import (
    Role, Company, Aspect, Subaspect, ProductCategory,
    QuestionnaireCategory,
    Questionnaire, ProductEntity, ProductBrand, ProductLine, ProductModel, EAN,
    Score, Question, Option, Answer, MyProducts,
    Query, Suggestion, AspectTotalScore, UserProfile, QuestionnaireEntity
)
from faker import Faker # Keep Faker for user data

User = get_user_model()
fake = Faker()

# --- Static Data Definitions (EXPANDED) ---

TECH_COMPANIES = [
    # Major Device Manufacturers
    'Samsung Electronics', 'Apple Inc.', 'Dell Technologies', 'HP Inc.',
    'Lenovo Group Limited', 'AsusTek Computer Inc.', 'Acer Inc.', 'Microsoft Corporation',
    'Google LLC', 'Xiaomi Corporation', 'Oppo', 'Vivo', 'Huawei Technologies Co., Ltd.',
    'Sony Group Corporation', 'Panasonic Corporation', 'LG Electronics Inc.', 'Motorola Mobility LLC',
    'Nokia Corporation', 'OnePlus', 'Realme', 'Fairphone B.V.', 'Framework Computer Inc.',

    # Component Manufacturers
    'Intel Corporation', 'Advanced Micro Devices, Inc. (AMD)', 'NVIDIA Corporation',
    'Qualcomm Incorporated', 'MediaTek Inc.', 'Taiwan Semiconductor Manufacturing Company (TSMC)',
    'SK Hynix Inc.', 'Micron Technology, Inc.', 'Western Digital Corporation', 'Seagate Technology PLC',
    'Corning Incorporated', 'BOE Technology Group Co., Ltd.',

    # Enterprise & Cloud
    'Amazon Web Services (AWS)', 'Microsoft Azure', 'Google Cloud Platform (GCP)',
    'Oracle Corporation', 'IBM Corporation', 'Cisco Systems, Inc.', 'Hewlett Packard Enterprise (HPE)',
    'VMware, Inc.', 'Salesforce, Inc.',

    # Peripherals & Accessories
    'Logitech International S.A.', 'Razer Inc.', 'Corsair Gaming, Inc.', 'Canon Inc.', 'Epson',
    'Brother Industries, Ltd.', 'Kingston Technology Corporation', 'Anker Innovations',

    # Others
    'Foxconn (Hon Hai Precision Industry Co., Ltd.)', # Major EMS provider
    'Tesla, Inc.' # Tech-focused, produces devices/interfaces
]

PRODUCT_CATEGORIES = [
    # Consumer Electronics
    'Smartphones', 'Laptops', 'Desktop Computers', 'All-in-One Computers', 'Tablets', 'E-readers',
    'Smartwatches', 'Fitness Trackers', 'Wireless Earbuds', 'Headphones (Over-ear/On-ear)',
    'Smart Speakers', 'Streaming Devices (Sticks/Boxes)', 'Digital Cameras (DSLR/Mirrorless/Point-and-Shoot)',
    'Action Cameras', 'Drones (Consumer)', 'Portable Gaming Consoles', 'Home Gaming Consoles',
    'VR Headsets', 'AR Glasses',

    # Computing Components
    'CPUs (Processors)', 'GPUs (Graphics Cards)', 'RAM (Memory Modules)', 'SSDs (Solid State Drives)',
    'HDDs (Hard Disk Drives)', 'Motherboards', 'Power Supply Units (PSUs)', 'Computer Cases',
    'CPU Coolers (Air/Liquid)', 'Case Fans',

    # Peripherals
    'Monitors', 'Keyboards', 'Mice', 'Webcams', 'Printers (Inkjet/Laser/All-in-One)', 'Scanners',
    'External Hard Drives', 'USB Flash Drives', 'Memory Cards', 'Docking Stations', 'Computer Speakers',
    'Microphones (USB/XLR)', 'Game Controllers', 'Drawing Tablets',

    # Networking
    'Wi-Fi Routers', 'Mesh Wi-Fi Systems', 'Modems', 'Network Switches', 'Network Attached Storage (NAS)',

    # Enterprise Hardware
    'Servers (Rack/Tower/Blade)', 'Workstations', 'Enterprise Storage Systems', 'Network Switches (Enterprise)',
    'Routers (Enterprise)', 'Firewalls (Hardware)', 'Thin Clients',

    # Software & Services (Representing the infrastructure impact)
    'Cloud Computing Services', 'Operating Systems', 'Software as a Service (SaaS)',
    'Platform as a Service (PaaS)', 'Infrastructure as a Service (IaaS)',

    # Other Tech
    'Smart Home Hubs', 'Smart Thermostats', 'Smart Lighting', 'Security Cameras (Smart)',
    'Video Doorbells', 'Electric Vehicle Chargers', 'Solar Panels (as tech product)', 'Power Banks'
]

# --- EXPANDED: Environmental Aspects ---
ENVIRONMENTAL_ASPECTS = {
    # Product Lifecycle Stages
    'Material Sourcing': ['Conflict-Free Minerals', 'Responsible Metals', 'Sustainable Forestry', 'Bio-based Content'],
    'Manufacturing & Production': ['Renewable Energy Use', 'Process Emissions', 'Waste Generation', 'Chemical Reduction'],
    'Logistics & Distribution': ['Transport Efficiency', 'Packaging Optimization', 'Distribution Network'],
    'Product Use Phase': ['Energy Consumption', 'Product Lifespan', 'Software Support', 'Water Usage'],
    'End-of-Life Management': ['Take-Back Programs', 'Recycling Rate', 'Refurbishment Rate', 'Safe Disposal'],

    # Cross-Cutting Impacts
    'Carbon Footprint (Total)': ['Direct Emissions', 'Energy Emissions', 'Supply Chain Emissions', 'Carbon Goals'],
    'Water Stewardship': ['Water Withdrawal', 'Discharge Quality', 'Supply Chain Risk', 'Water Recycling'],
    'Biodiversity Impact': ['Land Use Change', 'Ecosystem Impact', 'Pollution Prevention'],
    'Circular Economy Integration': ['Design for Repair', 'Recycled Materials', 'Service Models', 'Closed-Loop Systems'],
    'Hazardous Substances Management': ['Regulatory Compliance', 'Chemical Phase-out', 'Material Transparency'],

    # Corporate Responsibility & Transparency
    'Supply Chain Responsibility': ['Supplier Standards', 'Audit Program', 'Corrective Actions', 'Training Programs'],
    'Environmental Reporting & Disclosure': ['CDP Score', 'GRI Reporting', 'TCFD Alignment', 'Product Footprints'],
    'Climate Action & Advocacy': ['Science-Based Targets', 'Renewable Commitment', 'Policy Engagement'],
    'Investment in Green Tech': ['R&D Spending', 'Renewable Projects', 'Innovation Partnerships'],
    'Packaging Sustainability': ['Plastic Reduction', 'Recycled Content', 'Biodegradability', 'Sustainable Materials'],
    'Repairability & Access to Repair': ['Repairability Score', 'Parts Availability', 'Software Locks', 'Repair Network']
}
# --- (End of Expanded Aspects) ---


# --- EXPANDED: Brands, Lines, Products ---
BRANDS_LINES_PRODUCTS = {
    # --- Major Device Manufacturers ---
    'Samsung Electronics': {
        'Smartphones': {
            'Galaxy S': ['Galaxy S24 Ultra', 'Galaxy S24+', 'Galaxy S24', 'Galaxy S23 FE', 'Galaxy S23', 'Galaxy S22 Ultra'],
            'Galaxy Z': ['Galaxy Z Fold 5', 'Galaxy Z Flip 5', 'Galaxy Z Fold 4', 'Galaxy Z Flip 4'],
            'Galaxy A': ['Galaxy A55', 'Galaxy A35', 'Galaxy A25', 'Galaxy A15', 'Galaxy A05s'],
            'Galaxy M': ['Galaxy M55', 'Galaxy M34', 'Galaxy M14']
        },
        'Tablets': {
            'Galaxy Tab S': ['Galaxy Tab S9 Ultra', 'Galaxy Tab S9+', 'Galaxy Tab S9', 'Galaxy Tab S9 FE+', 'Galaxy Tab S8'],
            'Galaxy Tab A': ['Galaxy Tab A9+', 'Galaxy Tab A9', 'Galaxy Tab A8', 'Galaxy Tab Active 5']
        },
        'Laptops': {
            'Galaxy Book': ['Galaxy Book4 Ultra', 'Galaxy Book4 Pro 360', 'Galaxy Book4 Pro', 'Galaxy Book4 360', 'Galaxy Book3'],
            'Chromebook': ['Galaxy Chromebook 2 360', 'Galaxy Chromebook Go']
        },
        'Wearables': {
            'Galaxy Watch': ['Galaxy Watch 6 Classic', 'Galaxy Watch 6', 'Galaxy Watch 5 Pro', 'Galaxy Watch 5'],
            'Galaxy Buds': ['Galaxy Buds 2 Pro', 'Galaxy Buds FE', 'Galaxy Buds 2'],
            'Galaxy Fit': ['Galaxy Fit 3']
        },
         'Monitors': {
            'ViewFinity': ['ViewFinity S9 (S90PC)', 'ViewFinity S8 (S80PB)', 'ViewFinity S6 (S65TC)'],
            'Odyssey': ['Odyssey OLED G9', 'Odyssey Neo G9', 'Odyssey OLED G8', 'Odyssey Ark'],
            'Smart Monitor': ['Smart Monitor M8', 'Smart Monitor M7', 'Smart Monitor M5']
         },
         'SSDs (Solid State Drives)': {
             'Consumer SSD': ['990 PRO PCIe 4.0 NVMe', '980 PRO', '870 EVO SATA III', 'T7 Shield Portable SSD', 'T9 Portable SSD']
         },
         'Memory Cards': {
             'SD Cards': ['PRO Ultimate SD Card', 'EVO Plus SD Card'],
             'microSD Cards': ['PRO Ultimate microSD Card', 'EVO Select microSD Card']
         }
    },
    'Apple Inc.': {
        'Smartphones': {
            'iPhone': ['iPhone 15 Pro Max', 'iPhone 15 Pro', 'iPhone 15 Plus', 'iPhone 15', 'iPhone 14 Pro', 'iPhone 14', 'iPhone SE (3rd gen)']
        },
        'Tablets': {
            'iPad Pro': ['iPad Pro 13-inch (M4)', 'iPad Pro 11-inch (M4)', 'iPad Pro 12.9-inch (M2)'],
            'iPad Air': ['iPad Air 13-inch (M2)', 'iPad Air 11-inch (M2)', 'iPad Air (M1)'],
            'iPad': ['iPad (10th gen)', 'iPad (9th gen)'],
            'iPad mini': ['iPad mini (6th gen)']
        },
        'Laptops': {
            'MacBook Pro': ['MacBook Pro 16-inch (M3 Pro/Max)', 'MacBook Pro 14-inch (M3/Pro/Max)', 'MacBook Pro 13-inch (M2)'],
            'MacBook Air': ['MacBook Air 15-inch (M3)', 'MacBook Air 13-inch (M3)', 'MacBook Air 13-inch (M2)']
        },
        'Desktop Computers': {
            'iMac': ['iMac 24-inch (M3)'],
            'Mac mini': ['Mac mini (M2/M2 Pro)'],
            'Mac Studio': ['Mac Studio (M2 Max/Ultra)'],
            'Mac Pro': ['Mac Pro (M2 Ultra)']
        },
        'Wearables': {
            'Apple Watch': ['Apple Watch Ultra 2', 'Apple Watch Series 9', 'Apple Watch SE (2nd gen)'],
            'AirPods': ['AirPods Pro (2nd gen USB-C)', 'AirPods (3rd gen)', 'AirPods (2nd gen)', 'AirPods Max']
        },
         'Monitors': {
            'Pro Displays': ['Studio Display', 'Pro Display XDR']
         },
         'Streaming Devices (Sticks/Boxes)': {
             'Apple TV': ['Apple TV 4K (3rd gen)']
         },
         'Keyboards': {
             'Magic Keyboard': ['Magic Keyboard with Touch ID and Numeric Keypad', 'Magic Keyboard', 'Magic Keyboard Folio (iPad)']
         },
         'Mice': {
             'Magic Mouse': ['Magic Mouse'],
             'Magic Trackpad': ['Magic Trackpad']
         }
    },
    'Dell Technologies': {
        'Laptops': {
            'XPS': ['XPS 17 (9730)', 'XPS 15 (9530)', 'XPS 13 Plus (9320)', 'XPS 13 (9315)', 'XPS 13 2-in-1 (9315)'],
            'Alienware': ['Alienware m18 R2', 'Alienware m16 R2', 'Alienware x16 R2', 'Alienware x14 R2'],
            'Latitude': ['Latitude 9440 2-in-1', 'Latitude 7640', 'Latitude 7340 Ultralight', 'Latitude 5440', 'Latitude 3540'],
            'Inspiron': ['Inspiron 16 Plus (7630)', 'Inspiron 16 2-in-1 (7635)', 'Inspiron 14 (5430)', 'Inspiron 15 (3530)'],
            'Precision Mobile Workstations': ['Precision 7780', 'Precision 5680', 'Precision 3581'],
            'Vostro': ['Vostro 16', 'Vostro 15 3530']
        },
        'Desktop Computers': {
            'XPS Desktop': ['XPS Desktop (8960)'],
            'Alienware Aurora': ['Alienware Aurora R16', 'Alienware Aurora R15'],
            'OptiPlex': ['OptiPlex All-in-One (7410)', 'OptiPlex Micro (7010)', 'OptiPlex Tower (7010)'],
            'Inspiron Desktop': ['Inspiron Desktop', 'Inspiron Small Desktop'],
            'Vostro Desktop': ['Vostro Small Form Factor']
        },
        'Monitors': {
            'UltraSharp': ['Dell UltraSharp 32 6K (U3224KB)', 'Dell UltraSharp 40 Curved (U4025QW)', 'Dell UltraSharp 27 (U2724DE)', 'Dell UltraSharp 24 (U2424H)'],
            'Alienware Monitors': ['Alienware 34 Curved QD-OLED (AW3423DWF)', 'Alienware 27 Gaming (AW2724DM)', 'Alienware 38 Curved (AW3821DW)'],
            'Dell Gaming': ['G2724D', 'G3223Q'],
            'C Series (Video Conferencing)': ['C2722DE', 'C3422WE'],
            'P Series (Professional)': ['P2723DE', 'P2423D'],
            'S Series (Home)': ['S2721QS', 'S3221QS']
        },
        'Servers (Rack/Tower/Blade)': {
            'PowerEdge Rack': ['PowerEdge R760', 'PowerEdge R660', 'PowerEdge R750', 'PowerEdge R250'],
            'PowerEdge Tower': ['PowerEdge T560', 'PowerEdge T350', 'PowerEdge T150'],
            'PowerEdge Modular': ['PowerEdge MX760c', 'PowerEdge M640 VRTX']
        },
        'Workstations': {
            'Precision Fixed Workstations': ['Precision 7960 Tower', 'Precision 3660 Tower', 'Precision 3260 Compact']
        },
        'Keyboards': {
            'Dell Keyboards': ['Dell Premier Multi-Device Wireless Keyboard and Mouse (KM7321W)', 'Dell Pro Wireless Keyboard and Mouse (KM5221W)', 'Alienware Gaming Keyboard (AW510K)']
        },
        'Mice': {
            'Dell Mice': ['Dell Premier Rechargeable Mouse (MS7421W)', 'Dell Mobile Pro Wireless Mouse (MS5121W)', 'Alienware Gaming Mouse (AW610M)']
        },
        'Docking Stations': {
            'Dell Docks': ['Dell Universal Dock (UD22)', 'Dell Thunderbolt Dock (WD22TB4)', 'Dell Dual Charge Dock (HD22Q)']
        }
    },
    'HP Inc.': {
        'Laptops': {
            'Spectre': ['HP Spectre x360 14', 'HP Spectre x360 16', 'HP Spectre Foldable'],
            'Envy': ['HP Envy x360 15', 'HP Envy 16', 'HP Envy 17', 'HP Envy Move All-in-One'],
            'EliteBook': ['HP EliteBook 1040 G10', 'HP EliteBook 840 G10', 'HP EliteBook 655 G10', 'HP Elite Dragonfly G4'],
            'ProBook': ['HP ProBook 450 G10', 'HP ProBook 445 G10'],
            'ZBook Mobile Workstations': ['HP ZBook Fury G10', 'HP ZBook Studio G10', 'HP ZBook Firefly G10'],
            'OMEN Gaming': ['OMEN Transcend 16', 'OMEN 17', 'OMEN 16'],
            'Victus Gaming': ['Victus 16', 'Victus 15'],
            'Pavilion': ['HP Pavilion Plus 14', 'HP Pavilion x360 15', 'HP Pavilion 15'],
            'Chromebook': ['HP Chromebook x360 14c', 'HP Elite Dragonfly Chromebook']
        },
        'Desktop Computers': {
            'Spectre Desktops': ['HP Spectre All-in-One PC'],
            'Envy Desktops': ['HP ENVY All-in-One PC', 'HP ENVY Desktop PC'],
            'Elite Desktops': ['HP Elite Mini 800 G9', 'HP Elite Tower 800 G9', 'HP EliteOne 800 G9 AiO'],
            'Pro Desktops': ['HP Pro Tower 400 G9', 'HP Pro Mini 400 G9', 'HP ProOne 440 G9 AiO'],
            'Z Workstations': ['HP Z8 Fury G5', 'HP Z4 G5', 'HP Z2 Mini G9'],
            'OMEN Gaming Desktops': ['OMEN 45L', 'OMEN 25L'],
            'Victus Gaming Desktops': ['Victus 15L'],
            'Pavilion Desktops': ['HP Pavilion All-in-One', 'HP Pavilion Desktop']
        },
        'Monitors': {
            'HP Z Displays': ['HP Z40c G3 Curved', 'HP Z27u G3 QHD USB-C'],
            'HP E-Series': ['HP E27 G5', 'HP E24 G5'],
            'HP OMEN Gaming': ['OMEN 27k 4K', 'OMEN 34c WQHD Curved'],
            'HP Series 7 Pro': ['HP Series 7 Pro 31.5-inch 4K Thunderbolt 4 Monitor'],
            'HP M-Series': ['HP M27fq QHD Monitor']
        },
        'Printers (Inkjet/Laser/All-in-One)': {
            'HP OfficeJet Pro': ['OfficeJet Pro 9015e', 'OfficeJet Pro 8025e'],
            'HP LaserJet Pro': ['LaserJet Pro 4001dn', 'LaserJet Pro MFP 4101fdw'],
            'HP Smart Tank': ['Smart Tank 7301'],
            'HP ENVY Inspire': ['ENVY Inspire 7955e'],
            'HP DesignJet (Large Format)': ['DesignJet T650']
        },
        'Keyboards': {
            'HP Keyboards': ['HP 975 Dual-Mode Wireless Keyboard', 'HP 655 Wireless Keyboard and Mouse Combo', 'OMEN Sequencer Keyboard']
        },
        'Mice': {
            'HP Mice': ['HP 935 Creator Wireless Mouse', 'HP 430 Multi-Device Wireless Mouse', 'OMEN Vector Wireless Mouse']
        },
         'Docking Stations': {
             'HP Docks': ['HP Thunderbolt Dock G4', 'HP USB-C Dock G5']
         },
         'Webcams': {
             'HP Webcams': ['HP 965 4K Streaming Webcam', 'HP 325 FHD Webcam']
         }
    },
    'Lenovo Group Limited': {
        'Laptops': {
            'ThinkPad': ['ThinkPad X1 Carbon Gen 12', 'ThinkPad X1 2-in-1 Gen 9', 'ThinkPad T16 Gen 2', 'ThinkPad P1 Gen 6', 'ThinkPad Z13 Gen 2'],
            'Yoga': ['Yoga 9i 14" (Gen 9)', 'Yoga 7i 16" (Gen 9)', 'Yoga Slim 7i Pro X', 'Yoga Book 9i (Dual Screen)'],
            'Legion': ['Legion Pro 7i Gen 9', 'Legion Slim 5 Gen 9', 'Legion 9i (Gen 8)'],
            'IdeaPad': ['IdeaPad Slim 5i (16", Gen 9)', 'IdeaPad Flex 5i (14", Gen 8)', 'IdeaPad Gaming 3i'],
            'LOQ Gaming': ['LOQ 16', 'LOQ 15'],
            'ThinkBook': ['ThinkBook 16p Gen 4', 'ThinkBook 13x Gen 2']
        },
        'Desktop Computers': {
            'ThinkCentre': ['ThinkCentre M90q Gen 4 Tiny', 'ThinkCentre M90s Gen 4 SFF', 'ThinkCentre M90a Pro Gen 4 AiO'],
            'Legion Tower': ['Legion Tower 7i Gen 8', 'Legion Tower 5i Gen 8'],
            'IdeaCentre': ['IdeaCentre Mini Gen 8', 'IdeaCentre AIO 5i (27", Gen 8)'],
            'Yoga AIO': ['Yoga AIO 9i (32", Gen 8)']
        },
        'Tablets': {
            'Tab P Series': ['Lenovo Tab P12', 'Lenovo Tab P11 Pro (Gen 2)', 'Lenovo Tab P11 (Gen 2)'],
            'Tab M Series': ['Lenovo Tab M11', 'Lenovo Tab M10 Plus (Gen 3)', 'Lenovo Tab M9'],
            'ThinkPad Tablets': ['ThinkPad X1 Fold (16")']
        },
         'Monitors': {
            'ThinkVision': ['ThinkVision P32p-30 4K', 'ThinkVision T27hv-30 VOIP', 'ThinkVision P49w-30 Ultrawide'],
            'Legion Monitors': ['Legion Y34wz-30 Mini-LED Curved', 'Legion R27q-30 QHD'],
            'Lenovo L-Series': ['Lenovo L27q-35 QHD', 'Lenovo L32p-30 4K'],
            'Yoga Monitors': ['Yoga Monitor Y32p-30']
         },
         'Servers (Rack/Tower/Blade)': {
             'ThinkSystem Rack': ['ThinkSystem SR675 V3', 'ThinkSystem SR650 V3', 'ThinkSystem SR250 V3'],
             'ThinkSystem Tower': ['ThinkSystem ST650 V3', 'ThinkSystem ST50 V2'],
             'ThinkAgile HCI': ['ThinkAgile VX Series', 'ThinkAgile HX Series']
         },
         'Workstations': {
             'ThinkStation': ['ThinkStation PX', 'ThinkStation P3 Tower', 'ThinkStation P3 Ultra', 'ThinkStation P3 Tiny']
         },
         'Keyboards & Mice': {
             'ThinkPad Accessories': ['ThinkPad TrackPoint Keyboard II', 'ThinkPad Bluetooth Silent Mouse'],
             'Legion Accessories': ['Legion K500 RGB Mechanical Keyboard', 'Legion M600s Qi Wireless Gaming Mouse']
         }
    },
    'AsusTek Computer Inc.': {
        'Laptops': {
            'ROG (Republic of Gamers)': ['ROG Strix SCAR 18 (2024)', 'ROG Zephyrus G16 (2024)', 'ROG Flow X13 (2023)', 'ROG Ally (Handheld)'],
            'Zenbook': ['Zenbook DUO (2024 UX8406)', 'Zenbook 14 OLED (UX3405)', 'Zenbook S 13 OLED (UX5304)'],
            'Vivobook': ['Vivobook Pro 16X OLED', 'Vivobook S 15 OLED (K5504)', 'Vivobook 14 (X1402)'],
            'ProArt Studiobook': ['ProArt Studiobook 16 OLED (H7604)', 'ProArt Studiobook Pro 16 OLED (W7604)'],
            'ExpertBook': ['ExpertBook B9 OLED (B9403)', 'ExpertBook B5 Flip (B5602)'],
            'TUF Gaming': ['TUF Gaming A16 Advantage Edition', 'TUF Gaming F15 (2023)'],
            'Chromebook': ['Chromebook Vibe CX34 Flip', 'Chromebook CM14']
        },
        'Desktop Computers': {
            'ROG Gaming Desktops': ['ROG Strix G16CH', 'ROG Strix GA35'],
            'ProArt Station': ['ProArt Station PD5'],
            'ASUS S Series': ['ASUS S501MD (Tower)', 'ASUS S500SE (SFF)'],
            'ExpertCenter': ['ExpertCenter D7 SFF', 'ExpertCenter PN64 (Mini PC)'],
            'All-in-One PCs': ['ASUS A3 Series AiO']
        },
         'Monitors': {
            'ROG Monitors': ['ROG Swift OLED PG32UCDM (4K 240Hz)', 'ROG Swift Pro PG248QP (FHD 540Hz)', 'ROG Swift PG49WCD (QD-OLED Ultrawide)'],
            'ProArt': ['ProArt Display PA32UCG-K (Mini LED)', 'ProArt Display PA279CRV (4K HDR)'],
            'TUF Gaming Monitors': ['TUF Gaming VG27AQML1A (QHD 260Hz)', 'TUF Gaming VG34VQL3A (UWQHD Curved)'],
            'ZenScreen (Portable)': ['ZenScreen OLED MQ16AH', 'ZenScreen MB16ACV'],
            'ASUS Eye Care': ['ASUS VA27EHE', 'ASUS VY249HE']
         },
         'Motherboards': {
             'ROG Motherboards': ['ROG MAXIMUS Z790 HERO', 'ROG STRIX B650E-F GAMING WIFI'],
             'ProArt Motherboards': ['ProArt Z790-CREATOR WIFI', 'ProArt B650-CREATOR'],
             'TUF Gaming Motherboards': ['TUF GAMING Z790-PLUS WIFI', 'TUF GAMING B650-PLUS WIFI'],
             'PRIME Motherboards': ['PRIME Z790-A WIFI', 'PRIME B650M-A WIFI']
         },
         'GPUs (Graphics Cards)': {
             'ROG Strix': ['ROG Strix GeForce RTX 4090 OC Edition', 'ROG Strix Radeon RX 7900 XTX OC Edition'],
             'TUF Gaming': ['TUF Gaming GeForce RTX 4070 Ti SUPER OC', 'TUF Gaming Radeon RX 7800 XT OC Edition'],
             'ProArt': ['ProArt GeForce RTX 4080 SUPER OC', 'ProArt Radeon RX 7700 XT OC Edition'],
             'Dual': ['ASUS Dual GeForce RTX 4060 OC', 'ASUS Dual Radeon RX 6600']
         },
         'Networking': {
             'ROG Rapture Routers': ['ROG Rapture GT-BE98 Pro (WiFi 7)', 'ROG Rapture GT-AXE16000 (WiFi 6E)'],
             'ASUS ZenWiFi Mesh': ['ZenWiFi Pro ET12 (WiFi 6E Mesh)', 'ZenWiFi XT8 (WiFi 6 Mesh)'],
             'ASUS Routers': ['ASUS RT-AX88U Pro (WiFi 6)', 'ASUS RT-AX57 (WiFi 6)']
         }
    },
    'Acer Inc.': {
        'Laptops': {
            'Swift': ['Acer Swift Go 14 (SFG14-72)', 'Acer Swift X 16 (SFX16-61G)', 'Acer Swift Edge 16 (SFE16-43)'],
            'Aspire': ['Acer Aspire Vero 15 (AV15-53)', 'Acer Aspire 7 (A715-76)', 'Acer Aspire 5 (A515-58)'],
            'Predator Gaming': ['Predator Helios 18', 'Predator Helios Neo 16', 'Predator Triton 17 X'],
            'Nitro Gaming': ['Nitro V 16', 'Nitro 5 (AN515-58)'],
            'TravelMate (Business)': ['TravelMate P6 14', 'TravelMate Spin P4'],
            'ConceptD (Creator)': ['ConceptD 7 Ezel Pro', 'ConceptD 3'],
            'Chromebook': ['Acer Chromebook Plus 515', 'Acer Chromebook Spin 714']
        },
        'Desktop Computers': {
            'Aspire Desktops': ['Aspire XC-1780', 'Aspire TC-1770'],
            'Predator Orion': ['Predator Orion 7000', 'Predator Orion X'],
            'Nitro Desktops': ['Nitro 50'],
            'Veriton (Business)': ['Veriton Vero Mini', 'Veriton Z All-in-One'],
            'ConceptD Desktops': ['ConceptD 500']
        },
        'Monitors': {
            'Predator Monitors': ['Predator X34 V (OLED Ultrawide)', 'Predator XB273U F (QHD 360Hz)'],
            'Nitro Monitors': ['Nitro XV272U V (QHD 170Hz)', 'Nitro KG241Y'],
            'Acer Monitors': ['Acer K2 Series', 'Acer Vero RL Series (Eco-friendly)'],
            'ConceptD Monitors': ['ConceptD CP7271K P (4K Mini LED)']
        },
        'Projectors': { # Acer is known for projectors too
            'Home Cinema': ['Acer H6815BD (4K)', 'Acer VL7860 (Laser 4K)'],
            'Portable': ['Acer C250i'],
            'Business': ['Acer PD1530i']
        }
    },
    'Microsoft Corporation': {
         'Laptops': {
            'Surface Laptop': ['Surface Laptop 6 for Business', 'Surface Laptop 5', 'Surface Laptop Studio 2', 'Surface Laptop Go 3'],
         },
         'Tablets': {
             'Surface Pro': ['Surface Pro 10 for Business', 'Surface Pro 9 (Intel/5G)', 'Surface Go 4 for Business']
         },
         'Desktop Computers': {
             'Surface Studio': ['Surface Studio 2+ (All-in-One)']
         },
         'Home Gaming Consoles': {
             'Xbox': ['Xbox Series X', 'Xbox Series S']
         },
         'Game Controllers': {
             'Xbox Controllers': ['Xbox Wireless Controller', 'Xbox Elite Wireless Controller Series 2']
         },
         'Keyboards': {
             'Surface Keyboards': ['Surface Pro Signature Keyboard', 'Microsoft Designer Compact Keyboard', 'Microsoft Ergonomic Keyboard']
         },
         'Mice': {
             'Surface Mice': ['Surface Arc Mouse', 'Microsoft Bluetooth Ergonomic Mouse']
         },
         'Webcams': {
             'Microsoft Modern Webcam': ['Microsoft Modern Webcam']
         },
         'Operating Systems': {
             'Windows': ['Windows 11 Pro', 'Windows 11 Home', 'Windows Server 2022']
         },
         'Cloud Computing Services': {
             'Azure': ['Azure Virtual Machines', 'Azure SQL Database', 'Azure Blob Storage', 'Azure Kubernetes Service (AKS)']
         },
         'Software as a Service (SaaS)': {
             'Microsoft 365': ['Microsoft 365 Business Premium', 'Microsoft 365 E5', 'Microsoft Teams', 'Microsoft OneDrive']
         }
    },
    'Google LLC': {
        'Smartphones': {
            'Pixel': ['Pixel 8 Pro', 'Pixel 8', 'Pixel 8a', 'Pixel 7a', 'Pixel Fold']
        },
        'Wearables': {
            'Pixel Watch': ['Pixel Watch 2', 'Pixel Watch (1st gen)'],
            'Pixel Buds': ['Pixel Buds Pro', 'Pixel Buds A-Series']
        },
        'Tablets': {
            'Pixel Tablet': ['Pixel Tablet']
        },
        'Wireless Earbuds': { # Re-categorizing Buds
            'Pixel Buds': ['Pixel Buds Pro', 'Pixel Buds A-Series']
        },
        'Smart Speakers': {
            'Nest Audio': ['Nest Audio'],
            'Nest Mini': ['Nest Mini (2nd gen)'],
            'Nest Hub': ['Nest Hub (2nd gen)', 'Nest Hub Max']
        },
        'Streaming Devices (Sticks/Boxes)': {
            'Chromecast': ['Chromecast with Google TV (4K)', 'Chromecast with Google TV (HD)']
        },
        'Smart Home Hubs': { # Re-categorizing Hubs
            'Nest Hub': ['Nest Hub (2nd gen)', 'Nest Hub Max']
        },
        'Smart Thermostats': {
            'Nest Thermostat': ['Nest Thermostat', 'Nest Learning Thermostat (3rd gen)']
        },
        'Security Cameras (Smart)': {
            'Nest Cam': ['Nest Cam (wired)', 'Nest Cam (battery)', 'Nest Cam with floodlight']
        },
        'Video Doorbells': {
            'Nest Doorbell': ['Nest Doorbell (wired, 2nd gen)', 'Nest Doorbell (battery)']
        },
        'Wi-Fi Routers': {
            'Nest Wifi': ['Nest Wifi Pro (Wi-Fi 6E)', 'Nest Wifi Router (Wi-Fi 5)']
        },
        'Operating Systems': {
            'Android': ['Android 14', 'Android 13'],
            'ChromeOS': ['ChromeOS', 'ChromeOS Flex']
        },
        'Cloud Computing Services': {
            'Google Cloud Platform (GCP)': ['Compute Engine', 'Cloud Storage', 'BigQuery', 'Google Kubernetes Engine (GKE)']
        },
        'Software as a Service (SaaS)': {
            'Google Workspace': ['Gmail', 'Google Drive', 'Google Docs', 'Google Meet']
        }
    },
    'Xiaomi Corporation': {
        'Smartphones': {
            'Xiaomi Series': ['Xiaomi 14 Ultra', 'Xiaomi 14', 'Xiaomi 13T Pro', 'Xiaomi 13 Lite'],
            'Redmi Note': ['Redmi Note 13 Pro+ 5G', 'Redmi Note 13 Pro', 'Redmi Note 13 5G', 'Redmi Note 12'],
            'Redmi': ['Redmi 13C', 'Redmi 12', 'Redmi A2'],
            'POCO': ['POCO F6 Pro', 'POCO F6', 'POCO X6 Pro', 'POCO M6 Pro']
        },
        'Tablets': {
            'Xiaomi Pad': ['Xiaomi Pad 6S Pro 12.4', 'Xiaomi Pad 6'],
            'Redmi Pad': ['Redmi Pad SE']
        },
        'Wearables': {
            'Xiaomi Watch': ['Xiaomi Watch 2 Pro', 'Xiaomi Watch S3', 'Xiaomi Watch 2'],
            'Xiaomi Smart Band': ['Xiaomi Smart Band 8 Pro', 'Xiaomi Smart Band 8'],
            'Redmi Watch': ['Redmi Watch 4', 'Redmi Watch 3 Active']
        },
        'Wireless Earbuds': {
            'Xiaomi Buds': ['Xiaomi Buds 5 Pro', 'Xiaomi Buds 4 Pro'],
            'Redmi Buds': ['Redmi Buds 5 Pro', 'Redmi Buds 5']
        },
        'Laptops': {
            'Xiaomi Book': ['Xiaomi Book S 12.4" (ARM Tablet/Laptop hybrid)'], # Limited laptop presence outside China
            'Redmi Book': ['Redmi Book Pro 15 (Models vary by region)']
        },
        'Monitors': {
            'Xiaomi Gaming Monitor': ['Xiaomi Gaming Monitor G27i'],
            'Xiaomi Monitor': ['Xiaomi Monitor A27i', 'Xiaomi Curved Gaming Monitor 34"']
        },
        'Smart Speakers': {
            'Xiaomi Smart Speaker': ['Xiaomi Smart Speaker IR Control', 'Xiaomi Smart Speaker Lite']
        },
        'Streaming Devices (Sticks/Boxes)': {
            'Xiaomi TV Box': ['Xiaomi TV Box S (2nd Gen)'],
            'Xiaomi TV Stick': ['Xiaomi TV Stick 4K']
        },
        'Smart Lighting': {
            'Mi Smart LED Bulb': ['Mi Smart LED Bulb Essential (White and Color)'],
            'Mi LED Desk Lamp': ['Mi LED Desk Lamp 1S']
        },
        'Security Cameras (Smart)': {
            'Xiaomi Smart Camera': ['Xiaomi Smart Camera C400', 'Xiaomi Outdoor Camera AW300']
        },
        'Power Banks': {
             'Mi Power Bank': ['Mi Power Bank 3 Pro 20000mAh', 'Redmi Power Bank 10000mAh']
        }
    },
    'Framework Computer Inc.': { # Focus on repairability
        'Laptops': {
            'Framework Laptop': ['Framework Laptop 13 (Intel Core Ultra)', 'Framework Laptop 13 (AMD Ryzen 7040)', 'Framework Laptop 16']
        },
        'CPUs (Processors)': { # Sold as mainboards
            'Mainboards': ['Intel Core Ultra Mainboard', 'AMD Ryzen 7040 Series Mainboard']
        },
        'Keyboards': {
             'Input Modules': ['Keyboard - US English', 'Numpad Module', 'RGB Macropad Module']
        },
        'Webcams': {
             'Input Modules': ['Webcam Module (Standard)', 'Webcam Module (Privacy Switches)']
        },
        'RAM (Memory Modules)': { # Sold separately
            'DDR5 SODIMM': ['DDR5-5600 - 16GB (2 x 8GB)', 'DDR5-5600 - 32GB (2 x 16GB)']
        },
        'SSDs (Solid State Drives)': { # Sold separately
            'NVMe SSD': ['WD_BLACK SN770 NVMe - 1TB', 'WD_BLACK SN850X NVMe - 2TB']
        }
    },
    'Fairphone B.V.': { # Focus on sustainability & repairability
        'Smartphones': {
            'Fairphone Series': ['Fairphone 5', 'Fairphone 4']
        },
        'Wireless Earbuds': {
            'Fairbuds': ['Fairbuds']
        },
        'Headphones (Over-ear/On-ear)': {
             'Fairbuds XL': ['Fairbuds XL']
        },
        # They sell spare parts as "products"
        'Spare Parts (Smartphone)': {
             'FP5 Modules': ['FP5 Display Module', 'FP5 Battery', 'FP5 Rear Camera Module', 'FP5 USB-C Port'],
             'FP4 Modules': ['FP4 Display Module', 'FP4 Battery', 'FP4 Back Cover']
        },
        'Spare Parts (Headphones)': {
             'Fairbuds XL Parts': ['Fairbuds XL Battery', 'Fairbuds XL Earcups', 'Fairbuds XL Headband']
        }
    },

    # --- Component Manufacturers (Examples) ---
    'Intel Corporation': {
         'CPUs (Processors)': {
             'Core Ultra': ['Core Ultra 9 185H', 'Core Ultra 7 155H', 'Core Ultra 5 125U'],
             'Core (Desktop)': ['Core i9-14900K', 'Core i7-14700K', 'Core i5-14600K'],
             'Xeon Scalable': ['Xeon Platinum 8480+', 'Xeon Gold 6430']
         },
         'SSDs (Solid State Drives)': {
              'Optane': ['Optane SSD DC P5800X'], # Less common now
              'Client SSDs': ['Intel SSD 670p Series']
         },
         'Networking': {
              'Ethernet Adapters': ['Intel Ethernet Network Adapter E810-CQDA2']
         }
    },
    'Advanced Micro Devices, Inc. (AMD)': {
         'CPUs (Processors)': {
             'Ryzen Desktop': ['Ryzen 9 7950X3D', 'Ryzen 7 7800X3D', 'Ryzen 5 7600X'],
             'Ryzen Mobile': ['Ryzen 9 7945HX', 'Ryzen 7 7840U', 'Ryzen 5 7540U'],
             'EPYC Server': ['EPYC 9654 (Genoa)', 'EPYC 8534P (Siena)']
         },
         'GPUs (Graphics Cards)': {
             'Radeon RX Desktop': ['Radeon RX 7900 XTX', 'Radeon RX 7800 XT', 'Radeon RX 7600'],
             'Radeon PRO': ['Radeon PRO W7900', 'Radeon PRO W7600']
         }
    },
    'NVIDIA Corporation': {
         'GPUs (Graphics Cards)': {
             'GeForce RTX Consumer': ['GeForce RTX 4090', 'GeForce RTX 4080 SUPER', 'GeForce RTX 4070 Ti SUPER', 'GeForce RTX 4060'],
             'NVIDIA RTX Professional': ['RTX 6000 Ada Generation', 'RTX 4000 SFF Ada Generation'],
             'Data Center GPUs': ['H100 Tensor Core GPU', 'A100 Tensor Core GPU', 'Grace Hopper Superchip']
         },
         'Networking': { # Through Mellanox acquisition
              'Ethernet Adapters': ['ConnectX-7 Adapter Card'],
              'InfiniBand Switches': ['Quantum-2 QM9700 Switch']
         },
         'Streaming Devices (Sticks/Boxes)': {
              'SHIELD TV': ['SHIELD Android TV Pro', 'SHIELD Android TV']
         }
    },

    # --- Enterprise & Cloud (Examples) ---
    'Amazon Web Services (AWS)': {
         'Infrastructure as a Service (IaaS)': {
             'EC2 Instances': ['m7g.medium', 'c6i.large', 'r6a.xlarge', 'p5.48xlarge'],
             'S3 Storage': ['S3 Standard', 'S3 Glacier Deep Archive']
         },
         'Platform as a Service (PaaS)': {
              'RDS Databases': ['RDS for PostgreSQL', 'RDS for MySQL', 'Aurora Serverless'],
              'Lambda Functions': ['Lambda (Serverless Compute)']
         },
         'Software as a Service (SaaS)': { # Less direct focus, but examples
              'WorkSpaces': ['Amazon WorkSpaces (VDI)'],
              'Connect': ['Amazon Connect (Contact Center)']
         }
    },
     'Hewlett Packard Enterprise (HPE)': {
         'Servers (Rack/Tower/Blade)': {
             'ProLiant Rack': ['ProLiant DL380 Gen11', 'ProLiant DL360 Gen11'],
             'ProLiant Tower': ['ProLiant ML350 Gen11'],
             'ProLiant BladeSystem': ['Synergy 480 Gen11 Compute Module'],
             'Apollo (HPC)': ['Apollo 6500 Gen10 Plus System']
         },
         'Enterprise Storage Systems': {
             'Alletra Storage': ['Alletra MP', 'Alletra 9000', 'Alletra 6000'],
             'Primera': ['Primera A670'],
             'Nimble Storage': ['Nimble Storage AF Series']
         },
         'Networking': { # Through Aruba acquisition
              'Aruba Switches': ['Aruba CX 10000 Series', 'Aruba CX 6300 Series'],
              'Aruba Access Points': ['Aruba AP-655 (Wi-Fi 6E)', 'Aruba AP-535 (Wi-Fi 6)']
         }
    },

    # --- Peripherals & Accessories (Examples) ---
    'Logitech International S.A.': {
         'Keyboards': {
             'MX Series': ['MX Keys S', 'MX Mechanical'],
             'Ergo Series': ['Wave Keys', 'K860 Split Ergonomic'],
             'Gaming (G Series)': ['G915 LIGHTSPEED Wireless RGB Mechanical', 'G Pro X Keyboard']
         },
         'Mice': {
             'MX Series': ['MX Master 3S', 'MX Anywhere 3S'],
             'Ergo Series': ['Lift Vertical Ergonomic Mouse', 'MX Ergo Trackball'],
             'Gaming (G Series)': ['G Pro X Superlight 2 Mouse', 'G502 X Plus Lightspeed']
         },
         'Webcams': {
             'Brio': ['Brio 4K Pro Webcam', 'Brio 500'],
             'C920 Series': ['C920s Pro HD Webcam']
         },
         'Headsets': {
             'Zone Series (Business)': ['Zone Wireless 2', 'Zone Vibe 100'],
             'Gaming (G Series)': ['G Pro X 2 Lightspeed Wireless Headset', 'G733 Lightspeed Wireless RGB']
         },
         'Computer Speakers': {
             'Z Series': ['Z407 Bluetooth Computer Speakers', 'Z623 THX Certified']
         }
    }

    # ... Add many more entries for other companies and categories ...
}
# --- (End of Expanded Brands/Lines/Products) ---


# --- EXPANDED: Environmental Question Templates ---
QUESTION_TEMPLATES = [
    # --- Material Sourcing ---
    ('ProductModel', 'Material Sourcing', "What percentage of conflict-free minerals (3TG) is verified in the {entity_name} supply chain?", [('100% Verified', 1.0), ('High Percentage Verified (>90%)', 0.8), ('Partial Verification', 0.5), ('Verification In Progress', 0.3), ('No Verification Data', 0.1)]),
    ('ProductBrand', 'Material Sourcing', "Does {entity_name} have a public policy on sourcing recycled rare earth elements?", [('Yes, with targets', 1.0), ('Yes, policy exists', 0.7), ('Under Consideration', 0.4), ('No Policy', 0.1)]),
    ('ProductModel', 'Material Sourcing', "Is the paper used in the packaging for {entity_name} certified by FSC or PEFC?", [('Yes, 100% Certified', 1.0), ('Yes, Partially Certified', 0.7), ('Recycled Content Only', 0.5), ('No Certification', 0.1)]),
    ('ProductLine', 'Material Sourcing', "What is the average percentage of bio-based plastics used across the {entity_name} line?", [('>20%', 1.0), ('10-20%', 0.8), ('1-10%', 0.5), ('None or Negligible', 0.1)]),

    # --- Manufacturing & Production ---
    ('ProductBrand', 'Manufacturing & Production', "What percentage of the energy used in {entity_name}'s final assembly facilities comes from renewable sources?", [('>75%', 1.0), ('50-75%', 0.8), ('25-50%', 0.6), ('<25%', 0.3), ('Not Reported', 0.1)]),
    ('ProductModel', 'Manufacturing & Production', "Are Volatile Organic Compound (VOC) emissions significantly reduced during the coating/finishing process for the {entity_name}?", [('Yes, Water-based/Powder Coat', 1.0), ('Yes, High-Solids/Low-VOC', 0.7), ('Standard Processes', 0.4), ('Unknown', 0.1)]),
    ('ProductBrand', 'Manufacturing & Production', "Does {entity_name} report on its manufacturing waste diversion rate (recycling/reuse)?", [('Yes, >90%', 1.0), ('Yes, 70-90%', 0.8), ('Yes, <70%', 0.5), ('No Reporting', 0.1)]),
    ('ProductLine', 'Manufacturing & Production', "Has the {entity_name} line implemented closed-loop water recycling in its key manufacturing processes?", [('Yes, Widely Implemented', 1.0), ('Yes, Partially Implemented', 0.7), ('Pilot Stage', 0.4), ('No Implementation', 0.1)]),

    # --- Logistics & Distribution ---
    ('ProductBrand', 'Logistics & Distribution', "What is {entity_name}'s strategy for reducing emissions from product transportation (e.g., modal shift, efficient routing)?", [('Public Strategy with Targets', 1.0), ('Internal Strategy Documented', 0.7), ('Exploring Options', 0.4), ('No Specific Strategy', 0.1)]),
    ('ProductModel', 'Logistics & Distribution', "How does the packaging volume/weight ratio for the {entity_name} compare to previous generations or industry benchmarks?", [('Significantly Reduced (>20%)', 1.0), ('Moderately Reduced (5-20%)', 0.7), ('Similar/Slightly Reduced', 0.4), ('Increased/Unknown', 0.1)]),

    # --- Product Use Phase ---
    ('ProductModel', 'Product Use Phase', "Does the {entity_name} exceed the requirements of the latest relevant energy efficiency standard (e.g., Energy Star, EU Ecodesign)?", [('Yes, Significantly', 1.0), ('Yes, Meets/Slightly Exceeds', 0.8), ('Meets Minimum Requirements', 0.5), ('Does Not Meet/Not Applicable', 0.1)]),
    ('ProductLine', 'Product Use Phase', "What is the guaranteed minimum duration of OS and security updates for the {entity_name} line?", [('7+ Years', 1.0), ('5-6 Years', 0.8), ('3-4 Years', 0.6), ('<3 Years', 0.3), ('Not Specified', 0.1)]),
    ('ProductModel', 'Product Use Phase', "Does the {entity_name} offer user-configurable power saving modes beyond default OS settings?", [('Yes, Advanced Modes', 1.0), ('Yes, Basic Modes', 0.7), ('OS Defaults Only', 0.4)]),

    # --- End-of-Life Management ---
    ('ProductBrand', 'End-of-Life Management', "Does {entity_name} offer free mail-back or drop-off recycling programs for its products in major markets?", [('Yes, Widely Accessible & Free', 1.0), ('Yes, Limited Access/Cost', 0.7), ('Partnership with Recyclers Only', 0.4), ('No Program', 0.1)]),
    ('ProductBrand', 'End-of-Life Management', "Does {entity_name} publicly report the percentage of collected e-waste that is recycled versus incinerated or landfilled?", [('Yes, Detailed Reporting', 1.0), ('Yes, Aggregated Reporting', 0.7), ('Partial Reporting', 0.4), ('No Reporting', 0.1)]),
    ('ProductLine', 'End-of-Life Management', "Are products in the {entity_name} line designed for easy disassembly using common tools?", [('Yes, High Modularity', 1.0), ('Yes, Some Modularity', 0.7), ('Standard Construction (Glues/Clips)', 0.4), ('Difficult/Destructive Disassembly', 0.1)]),

    # --- Carbon Footprint (Total) ---
    ('ProductBrand', 'Carbon Footprint (Total)', "Has {entity_name} committed to validated Science-Based Targets (SBTi) for emission reduction?", [('Yes, Approved Targets (1.5°C aligned)', 1.0), ('Yes, Approved Targets (Well Below 2°C)', 0.8), ('Committed, Targets Pending Validation', 0.6), ('No Commitment', 0.1)]),
    ('ProductModel', 'Carbon Footprint (Total)', "Is a Product Carbon Footprint (PCF) report publicly available for the {entity_name}?", [('Yes, ISO 14067/GHG Protocol Compliant', 1.0), ('Yes, Simplified Report', 0.7), ('Internal Assessment Only', 0.4), ('Not Available', 0.1)]),
    ('ProductBrand', 'Carbon Footprint (Total)', "What percentage of {entity_name}'s global electricity consumption (Scope 2) is matched with renewable energy purchases/generation?", [('100%', 1.0), ('75-99%', 0.8), ('50-74%', 0.6), ('<50%', 0.3), ('Not Reported', 0.1)]),

    # --- Water Stewardship ---
    ('ProductBrand', 'Water Stewardship', "Does {entity_name} conduct water risk assessments in its supply chain, particularly in water-stressed regions?", [('Yes, Comprehensive & Public', 1.0), ('Yes, Internal Assessment', 0.7), ('Limited Assessment', 0.4), ('No Assessment Reported', 0.1)]),
    ('ProductBrand', 'Water Stewardship', "Does {entity_name} have time-bound targets for reducing water withdrawal in its operations?", [('Yes, Ambitious Targets', 1.0), ('Yes, Moderate Targets', 0.7), ('Targets Under Development', 0.4), ('No Targets', 0.1)]),

    # --- Circular Economy Integration ---
    ('ProductModel', 'Circular Economy Integration', "Does the {entity_name} utilize a modular design allowing for component upgrades or replacements?", [('Yes, Key Components (CPU/RAM/Storage/Battery)', 1.0), ('Yes, Limited Components (Battery/Storage)', 0.7), ('Minimal Modularity', 0.4), ('No Modularity', 0.1)]),
    ('ProductBrand', 'Circular Economy Integration', "Does {entity_name} offer certified refurbished products with warranty?", [('Yes, Extensive Program', 1.0), ('Yes, Limited Program', 0.7), ('Pilot/Occasional Offers', 0.4), ('No Refurbished Program', 0.1)]),
    ('ProductLine', 'Circular Economy Integration', "What is the average percentage of post-consumer recycled materials (by weight) used in the {entity_name} line?", [('>30%', 1.0), ('15-30%', 0.8), ('5-15%', 0.6), ('<5%', 0.3), ('Not Reported', 0.1)]),

    # --- Hazardous Substances Management ---
    ('ProductModel', 'Hazardous Substances Management', "Is the {entity_name} certified free of Brominated Flame Retardants (BFRs) and Polyvinyl Chloride (PVC)?", [('Yes, Fully Certified', 1.0), ('Yes, Key Components Free', 0.7), ('Complies with RoHS Only', 0.4), ('Contains BFR/PVC', 0.1)]),
    ('ProductBrand', 'Hazardous Substances Management', "Does {entity_name} maintain a public Manufacturing Restricted Substances List (MRSL) that goes beyond legal requirements?", [('Yes, Comprehensive & Public MRSL', 1.0), ('Yes, Public MRSL (Standard)', 0.7), ('Internal List Only', 0.4), ('No Specific List Beyond Compliance', 0.1)]),

    # --- Supply Chain Responsibility ---
    ('ProductBrand', 'Supply Chain Responsibility', "How frequently does {entity_name} conduct environmental audits of its key suppliers?", [('Annually or More', 1.0), ('Every 2-3 Years', 0.7), ('Infrequently/Ad-hoc', 0.4), ('Audits Not Conducted/Reported', 0.1)]),
    ('ProductBrand', 'Supply Chain Responsibility', "Does {entity_name}'s supplier code of conduct include specific environmental requirements (energy, water, waste)?", [('Yes, Detailed & Specific Requirements', 1.0), ('Yes, General Environmental Clause', 0.7), ('Limited/No Environmental Clauses', 0.4)]),

    # --- Environmental Reporting & Disclosure ---
    ('ProductBrand', 'Environmental Reporting & Disclosure', "Does {entity_name} publish an annual sustainability/ESG report following recognized frameworks (e.g., GRI, SASB)?", [('Yes, Comprehensive Report with External Assurance', 1.0), ('Yes, Comprehensive Report (Self-Assured)', 0.8), ('Yes, Limited Report', 0.5), ('No Public Report', 0.1)]),
    ('ProductBrand', 'Environmental Reporting & Disclosure', "What is {entity_name}'s latest CDP Climate Change score?", [('A / A-', 1.0), ('B', 0.8), ('C', 0.6), ('D / F / Not Disclosed', 0.2)]),

    # --- Repairability & Access to Repair ---
    ('ProductModel', 'Repairability & Access to Repair', "Are repair manuals and spare parts for the {entity_name} made available to independent repair shops and consumers?", [('Yes, Widely Available', 1.0), ('Yes, Limited Availability/High Cost', 0.7), ('Available to Authorized Repairers Only', 0.4), ('Not Available', 0.1)]),
    ('ProductModel', 'Repairability & Access to Repair', "Does the {entity_name} require proprietary tools or software pairing for common repairs (e.g., screen, battery)?", [('No, Standard Tools & No Pairing', 1.0), ('Minor Pairing/Software Steps', 0.7), ('Requires Proprietary Tools', 0.4), ('Requires Pairing for Key Components', 0.2)]),
    ('ProductBrand', 'Repairability & Access to Repair', "Does {entity_name} actively lobby against or support Right to Repair legislation?", [('Actively Supports', 1.0), ('Neutral / No Stance', 0.6), ('Actively Lobbies Against', 0.1)]),

    # --- Packaging Sustainability ---
    ('ProductModel', 'Packaging Sustainability', "What percentage of the packaging for {entity_name} (by weight) is plastic-free?", [('100%', 1.0), ('90-99%', 0.8), ('50-89%', 0.6), ('<50%', 0.3), ('Not Reported', 0.1)]),
    ('ProductModel', 'Packaging Sustainability', "Is the packaging for {entity_name} easily recyclable in typical municipal recycling streams?", [('Yes, Widely Recyclable Materials', 1.0), ('Mostly Recyclable (Minor Contaminants)', 0.7), ('Partially Recyclable (Mixed Materials)', 0.4), ('Difficult to Recycle', 0.1)]),
]
# --- (End of Expanded Question Templates) ---

# --- Helper Functions ---

def get_random_environmental_score():
    """Generates a random decimal score (0-10) representing environmental performance."""
    return Decimal(random.uniform(1, 9)).quantize(Decimal('0.01'))

def get_random_total_environmental_score():
    """Generates a random decimal score (0-100) representing overall environmental performance."""
    return Decimal(random.uniform(10, 90)).quantize(Decimal('0.1'))

def get_random_ean():
    """Generates a plausible-looking fake EAN-13 with valid check digit."""
    # First 2–3 digits: GS1 prefix (simplified to 2 here)
    country_code = random.choice(['00','01','02','03','04','05','06','07','08','09'])
    company_code = str(random.randint(10000, 99999))  # 5 digits
    product_code = str(random.randint(1000, 99999)).zfill(5)  # 5 digits

    first_12 = country_code + company_code + product_code  # total 12 digits

    # Calculate checksum
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(first_12))
    check_digit = (10 - (total % 10)) % 10

    return first_12 + str(check_digit)

# --- Data Creation Functions (Modified for Environmental Focus) ---

def create_roles():
    """Creates predefined roles."""
    Role.objects.get_or_create(name='Admin')
    Role.objects.get_or_create(name='Editor')
    Role.objects.get_or_create(name='ManufacturingUser')
    Role.objects.get_or_create(name='RetailUser')
    Role.objects.get_or_create(name='Retailer')
    Role.objects.get_or_create(name='Sustainability Analyst')
    Role.objects.get_or_create(name='Viewer')
    print("Roles created.")

def create_companies():
    """Creates companies from the static list."""
    count = 0
    for name in TECH_COMPANIES:
        _, created = Company.objects.get_or_create(name=name)
        if created:
            count += 1
    print(f"{count} Companies created (Total: {Company.objects.count()}).")

def create_aspects():
    """Creates ENVIRONMENTAL aspects and subaspects."""
    aspect_count = 0
    subaspect_count = 0

    # --- Create the special 'Transparency' Aspect first ---
    # This is required for transparency score calculations.
    transparency_aspect, created = Aspect.objects.get_or_create(name='Transparency')
    if created:
        aspect_count += 1

    # Limit to first 10 aspects
    limited_aspects = dict(list(ENVIRONMENTAL_ASPECTS.items())[:10])

    for aspect_name, subaspect_list in limited_aspects.items():
        aspect, created = Aspect.objects.get_or_create(name=aspect_name)
        if created:
            aspect_count += 1
        for subaspect_name in subaspect_list:
            # Assuming Subaspect name is primary key
            subaspect, created = Subaspect.objects.get_or_create(name=subaspect_name, defaults={'aspect': aspect})
            if created:
                subaspect_count += 1
    print(f"{aspect_count} Environmental Aspects created (Total: {Aspect.objects.count()}).")
    print(f"{subaspect_count} Environmental Subaspects created (Total: {Subaspect.objects.count()}).")


def create_questionnaire_categories():
    """Creates and returns default questionnaire category for generated data."""
    default_q_category, _ = QuestionnaireCategory.objects.get_or_create(name='General Tech')
    print(f"Questionnaire Categories available: {QuestionnaireCategory.objects.count()} (default: {default_q_category.name}).")
    return default_q_category


def create_product_categories():
    """Creates product categories from the static list."""
    default_q_category, _ = QuestionnaireCategory.objects.get_or_create(name='General Tech')
    count = 0
    for name in PRODUCT_CATEGORIES:
        category, created = ProductCategory.objects.get_or_create(
            name=name,
            defaults={'questionnaire_category': default_q_category}
        )
        if not created and category.questionnaire_category is None:
            category.questionnaire_category = default_q_category
            category.save(update_fields=['questionnaire_category'])
        if created:
            count += 1
    print(f"{count} Product Categories created (Total: {ProductCategory.objects.count()}).")

def create_users(count=20):
    """Creates a specified number of fake users with random roles."""
    roles = list(Role.objects.all())
    if not roles:
        print("Warning: No roles found. Please create roles first.")
        return
    created_count = 0
    for i in range(count):
        username = f"{fake.user_name()}_{i}"
        email = fake.email()
        # Basic check for existing user
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
             username = f"{fake.user_name()}_{i}_{random.randint(1000,9999)}"
             email = f"{i}_{fake.email()}"

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123'
            )
            # Create UserProfile, linking to user and a random role
            UserProfile.objects.create(
                user=user,
                role=random.choice(roles)
            )
            created_count += 1
        except Exception as e:
             print(f"Could not create user {username} ({email}): {e}")
             continue
    print(f"{created_count} Users created (Total: {User.objects.count()}).")


def create_brands_and_products():
    """Creates brands, product lines, and products from the static structure."""
    product_count = 0
    brand_count = 0
    line_count = 0

    for company_name, categories in BRANDS_LINES_PRODUCTS.items():
        # Create Brand
        brand, created = ProductBrand.objects.get_or_create(
            name=company_name  # Using company name as brand name
        )
        if created:
            brand_count += 1

        for category_name, lines in categories.items():
            try:
                category = ProductCategory.objects.get(name=category_name)
            except ProductCategory.DoesNotExist:
                print(f"Warning: ProductCategory '{category_name}' not found. Skipping.")
                continue

            for line_name, products in lines.items():
                # Create ProductLine (has product_category and brand_fk)
                line_defaults = {'product_category': category, 'brand_fk': brand}
                product_line, created = ProductLine.objects.get_or_create(
                    name=line_name,
                    defaults=line_defaults
                )
                if created:
                    line_count += 1

                for product_name in products:
                    # Create Product (no EAN field)
                    product_defaults = {
                        'product_line': product_line,
                        'overall_score': get_random_environmental_score()
                    }
                    prod, created = ProductModel.objects.get_or_create(
                        name=product_name,
                        defaults=product_defaults
                    )
                    if created:
                        product_count += 1

    print(f"{brand_count} Brands created (Total: {ProductBrand.objects.count()}).")
    print(f"{line_count} Product Lines created (Total: {ProductLine.objects.count()}).")
    print(f"{product_count} Products created (Total: {ProductModel.objects.count()}).")


def create_eans():
    """Creates EAN variants for all existing ProductModel instances."""
    ean_count = 0

    products = ProductModel.objects.all()
    if not products:
        print("Warning: No ProductModel instances found to create EANs for.")
        return

    for product in products:
        # Check if EANs already exist for this product
        existing_eans = EAN.objects.filter(product_model=product).count()
        if existing_eans > 0:
            print(f"Skipping {product.name} - already has {existing_eans} EANs")
            continue

        # Create multiple EAN variants for each product
        ean_variants = create_ean_variants_for_product(product)
        ean_count += len(ean_variants)
        print(f"Created {len(ean_variants)} EAN variants for {product.name}")

    print(f"{ean_count} EANs created (Total: {EAN.objects.count()}).")


def create_ean_variants_for_product(product_model):
    """Creates multiple EAN variants for a product model with different attributes."""
    variants = []

    color_options = ["Black", "White", "Silver", "Blue", "Red"]
    region_options = ["US", "EU", "APAC", "Global"]

    num_variants = random.randint(2, 3)
    for i in range(num_variants):
        color = random.choice(color_options)
        region = random.choice(region_options)
        variant_name = f"{product_model.name} {color} ({region})"

        ean = get_unique_ean()
        ean_obj = EAN.objects.create(
            ean=ean,
            name=variant_name,
            product_model=product_model
        )
        variants.append(ean_obj)

    return variants


def get_unique_ean():
    """Generates a unique EAN that doesn't exist in the database."""
    ean = get_random_ean()
    while EAN.objects.filter(ean=ean).exists():
        ean = get_random_ean()
    return ean


def create_questionnaires(count_per_category=3):
    """Creates questionnaires linking categories and ENVIRONMENTAL aspects."""
    entity_types = ['ProductBrand', 'ProductLine', 'ProductModel']
    questionnaire_count = 0
    for category in ProductCategory.objects.all():
        questionnaire_category = category.questionnaire_category
        if questionnaire_category is None:
            print(f"Skipping ProductCategory '{category}' - no questionnaire category assigned.")
            continue
        aspects = list(Aspect.objects.exclude(name='Transparency'))
        if not aspects:
            print("Warning: No Environmental Aspects found. Cannot create Questionnaires.")
            return
        for _ in range(count_per_category):
             aspect = random.choice(aspects)
             entity_type = random.choice(entity_types)
             _, created = Questionnaire.objects.get_or_create(
                 questionnaire_category=questionnaire_category,
                 aspect=aspect,
                 entity_type=entity_type
             )
             if created:
                 questionnaire_count += 1
    print(f"{questionnaire_count} Questionnaires created (Total: {Questionnaire.objects.count()}).")


def create_questions_and_options(questions_per_q=4, options_per_q=4):
    """Creates ENVIRONMENTAL questions and options for questionnaires."""
    question_count = 0
    option_count = 0

    for questionnaire in Questionnaire.objects.all():
        subaspects = list(Subaspect.objects.filter(aspect=questionnaire.aspect))
        subaspect_name_for_q = random.choice(subaspects).name.lower() if subaspects else questionnaire.aspect.name.lower()

        relevant_templates = [
            t for t in QUESTION_TEMPLATES
            if t[0] == questionnaire.entity_type and t[1] == questionnaire.aspect.name
        ]

        for _ in range(questions_per_q):
            question_text = f"Generic question about {subaspect_name_for_q} for {questionnaire.entity_type}?"
            options_list = None

            if relevant_templates:
                template = random.choice(relevant_templates)
                entity_placeholder = f"[{questionnaire.entity_type}]"
                question_text = template[2].format(entity_name=entity_placeholder)
                options_list = template[3]
            else:
                question_text = f"How does the {questionnaire.entity_type} perform regarding {questionnaire.aspect.name.lower()} ({subaspect_name_for_q})?"
                options_list = [("High", 1.0), ("Medium", 0.6), ("Low", 0.3), ("Unknown", 0.0)]

            question, created = Question.objects.get_or_create(
                 questionnaire=questionnaire,
                 question_text=question_text,
                 defaults={
                     'subaspect': random.choice(subaspects) if subaspects else None,
                     'max_score': random.uniform(3, 7)
                 }
            )
            if not created:
                 continue
            question_count +=1

            if options_list:
                for opt_text, opt_weight in options_list[:options_per_q]:
                    opt, opt_created = Option.objects.get_or_create(
                        question=question,
                        option_text=opt_text,
                        defaults={'weight': opt_weight}
                    )
                    if opt_created: option_count += 1
            else:
                 for j in range(options_per_q):
                     opt, opt_created = Option.objects.get_or_create(
                         question=question,
                         option_text=f"Level {j+1}",
                         defaults={'weight': round(random.uniform(0.1, 1.0), 2)}
                     )
                     if opt_created: option_count += 1

    print(f"{question_count} Environmental Questions created (Total: {Question.objects.count()}).")
    print(f"{option_count} Options created (Total: {Option.objects.count()}).")


def create_answers(answers_per_target=5):
    """Creates sample answers only for options in questionnaires assigned to each ProductEntity."""
    users = list(User.objects.all())
    questionnaire_links = list(
        QuestionnaireEntity.objects.select_related('product_entity', 'questionnaire')
    )
    created_count = 0
    updated_count = 0

    if not users:
        print("Warning: Need users to create answers.")
        return
    if not questionnaire_links:
        print("Warning: Need QuestionnaireEntity links to create answers.")
        return

    for link in questionnaire_links:
        options_for_questionnaire = list(
            Option.objects.filter(question__questionnaire=link.questionnaire)
        )

        if not options_for_questionnaire:
            continue

        selected_options = random.sample(
            options_for_questionnaire,
            min(answers_per_target, len(options_for_questionnaire))
        )

        for option in selected_options:
            answer_state = random.choices(
                population=['true', 'false', 'unknown'],
                weights=[45, 35, 20],
                k=1,
            )[0]

            is_true = answer_state == 'true'
            is_false = answer_state == 'false'
            source_value = fake.url() if (is_true or is_false) else None
            context_value = (
                f"Sample evidence captured for {option.question.question_text[:80]}"
                if (is_true or is_false)
                else None
            )

            answer_values = {
                'answered_by': random.choice(users),
                'is_true': is_true,
                'is_false': is_false,
                'source': source_value,
                'context': context_value,
            }

            answer, created = Answer.objects.update_or_create(
                product_entity=link.product_entity,
                option=option,
                defaults=answer_values,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

    print(
        f"{created_count} Environmental Answers created, {updated_count} updated "
        f"(Total: {Answer.objects.count()})."
    )


def create_scores():
    """Creates ENVIRONMENTAL scores linking ProductEntity instances and aspects."""
    score_count = 0
    entities = list(ProductModel.objects.all()) + list(ProductLine.objects.all()) + list(ProductBrand.objects.all())

    if not entities:
        print("Warning: Need Product, ProductLine, or Brand entities to create scores.")
        return

    for entity in entities:
        for aspect in Aspect.objects.all():
            _, created = Score.objects.get_or_create(
                aspect=aspect,
                product_entity=entity,
                defaults={'value': get_random_environmental_score()}
            )
            if created:
                score_count += 1
    print(f"{score_count} Environmental Scores created (Total: {Score.objects.count()}).")


def create_my_products(products_per_company=5):
    """Assigns some products to companies (e.g., for a retailer's inventory)."""
    myprod_count = 0
    retailer_role = Role.objects.filter(name__in=['Retailer', 'RetailUser']).first()
    if retailer_role:
        # Filter Company using the correct reverse related name 'userprofile'
        companies = list(Company.objects.filter(userprofile__role=retailer_role).distinct())
        if not companies:
             print("No companies associated with retailer role found, assigning to any company.")
             companies = list(Company.objects.all())
    else:
        print("Warning: 'Retailer' role not found. Assigning MyProducts to any company.")
        companies = list(Company.objects.all())

    all_products = list(ProductModel.objects.all())

    if not companies or not all_products:
        print("Warning: Need Companies and Products to create MyProducts.")
        return

    for company in companies:
        if company.pk is None: continue

        assigned_products = random.sample(
            all_products,
            min(products_per_company, len(all_products))
        )
        for product in assigned_products:
             if product.pk is None: continue

             _, created = MyProducts.objects.get_or_create(company=company, product=product)
             if created:
                 myprod_count += 1
    print(f"{myprod_count} MyProducts entries created (Total: {MyProducts.objects.count()}).")


def create_queries_and_suggestions(count=15):
    """Creates sample ENVIRONMENTAL queries and suggestions."""
    query_count = 0
    suggestion_count = 0

    target_roles = Role.objects.filter(name__in=['Sustainability Analyst', 'Retailer', 'RetailUser'])
    if target_roles:
        # Filter User using the 'profile' related_name from UserProfile
        eligible_users = list(User.objects.filter(profile__role__in=target_roles).distinct())
    else:
        print("Warning: Target roles ('Sustainability Analyst', 'Retailer') not found. Using any user.")
        eligible_users = list(User.objects.all())

    questions = list(Question.objects.all())
    answers = list(Answer.objects.all())

    if not eligible_users:
        print("Warning: No eligible users found to create Queries/Suggestions.")
        return
    if not questions:
        print("Warning: No questions found to create Queries.")
        return

    for _ in range(count):
        user = random.choice(eligible_users)
        question = random.choice(questions)

        # Create Query
        query, created = Query.objects.get_or_create(
             retail_user=user,
             question=question,
             defaults={'is_handled': random.choice([True, False])}
        )
        if created:
            query_count += 1

            # Suggest a relevant answer if answers exist
            if answers:
                relevant_answers = Answer.objects.filter(option__question=question)
                if relevant_answers:
                     suggested_answer_obj = random.choice(list(relevant_answers))
                     # **FIX:** Remove the 'query=query' argument as it's not in the Suggestion model
                     sug, sug_created = Suggestion.objects.get_or_create(
                         retail_user=user, # User making the suggestion
                         answer=suggested_answer_obj, # The suggested answer record
                         defaults={'suggested_answer': random.choice([True, False])}
                     )
                     if sug_created:
                         suggestion_count += 1

    print(f"{query_count} Environmental Queries created (Total: {Query.objects.count()}).")
    print(f"{suggestion_count} Environmental Suggestions created (Total: {Suggestion.objects.count()}).")


def create_aspect_total_scores():
    """Creates aggregated ENVIRONMENTAL aspect scores for products."""
    total_score_count = 0
    products = list(ProductModel.objects.all())
    aspects = list(Aspect.objects.all())

    if not products or not aspects:
        print("Warning: Need Products and Aspects to create AspectTotalScores.")
        return

    for product in products:
         if product.pk is None: continue
         # Ensure related objects exist and have PKs before querying Scores
         try:
            # Use .select_related for efficiency if accessing related fields often
            product_line = product.product_line
            if product_line is None or product_line.pk is None:
                # print(f"Warning: ProductLine missing or not saved for Product {product.name}.")
                continue
            brand = product_line.brand_fk
            if brand is None or brand.pk is None:
                # print(f"Warning: Brand missing or not saved for ProductLine {product_line.name}.")
                continue
         except ObjectDoesNotExist: # Catch potential DoesNotExist errors
             print(f"Warning: Related object (ProductLine/Brand) not found for Product {product.name}. Skipping AspectTotalScore calculation.")
             continue


         for aspect in aspects:
             # Fetch the three Score objects if they exist
             product_score = Score.objects.filter(aspect=aspect, product_entity=product).first()
             line_score    = Score.objects.filter(aspect=aspect, product_entity=product_line).first()
             brand_score   = Score.objects.filter(aspect=aspect, product_entity=brand).first()

             # Sum them up safely
             total_score_val = Decimal('0.0')
             for s in [product_score, line_score, brand_score]:
                 if s and s.value is not None:
                     total_score_val += s.value

             # Update or create the AspectTotalScore record
             _, created = AspectTotalScore.objects.update_or_create(
                 product_model=product,
                 aspect=aspect,
                 defaults={'value': total_score_val}
             )
             if created:
                 total_score_count += 1

         # After calculating all aspect totals for a product, update its overall score
         avg_score_dict = AspectTotalScore.objects.filter(product_model=product).aggregate(avg_value=Avg('value'))
         avg_score = avg_score_dict['avg_value'] or Decimal('0.0')
         product.overall_score = round(Decimal(avg_score), 1)
         product.save(update_fields=['overall_score'])


    print(f"{total_score_count} Environmental AspectTotalScores created/updated (Total: {AspectTotalScore.objects.count()}).")

def create_questionnaire_entities():
    # --- Brand: For each product_category the brand has via its ProductLines ---
    for brand in ProductBrand.objects.all():
        categories = ProductLine.objects.filter(brand_fk=brand).values_list('product_category', flat=True).distinct()
        for category in categories:
            if category is None:
                continue
            product_category = ProductCategory.objects.filter(pk=category).first()
            if not product_category or product_category.questionnaire_category is None:
                continue
            questionnaires = Questionnaire.objects.filter(
                questionnaire_category=product_category.questionnaire_category,
                entity_type='ProductBrand'
            )
            for questionnaire in questionnaires:
                try:
                    QuestionnaireEntity.objects.get_or_create(
                        questionnaire=questionnaire,
                        product_entity=brand
                    )
                except Exception as e:
                    print(f"Error creating QuestionnaireEntity for Brand {brand} (category {category}): {e}")

    # Create QuestionnaireEntity for ProductLine entities
    for product_line in ProductLine.objects.all():
        if product_line.product_category is None or product_line.product_category.questionnaire_category is None:
            continue
        questionnaires = Questionnaire.objects.filter(
            questionnaire_category=product_line.product_category.questionnaire_category,
            entity_type='ProductLine'
        )
        for questionnaire in questionnaires:
            try:
                QuestionnaireEntity.objects.get_or_create(
                    questionnaire=questionnaire,
                    product_entity=product_line
                )
            except Exception as e:
                print(f"Error creating QuestionnaireEntity for ProductLine {product_line}: {e}")

    # --- Product: Use product_line.product_category ---
    for product in ProductModel.objects.all():
        category = product.product_line.product_category
        if category is None or category.questionnaire_category is None:
            continue
        questionnaires = Questionnaire.objects.filter(
            questionnaire_category=category.questionnaire_category,
            entity_type='ProductModel'
        )
        for questionnaire in questionnaires:
            try:
                QuestionnaireEntity.objects.get_or_create(
                    questionnaire=questionnaire,
                    product_entity=product
                )
            except Exception as e:
                print(f"Error creating QuestionnaireEntity for Product {product}: {e}")

# --- Management Command ---
class Command(BaseCommand):
    help = 'Populate the database with static tech data focused on ENVIRONMENTAL aspects'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting data population with ENVIRONMENTAL focus...")

        all_creation_functions = [
            create_roles,
            create_companies,
            create_aspects,
            create_questionnaire_categories,
            create_product_categories,
            create_users,
            create_brands_and_products,
            create_eans,
            create_questionnaires,
            create_questions_and_options,
            create_questionnaire_entities,
            create_answers,
            create_scores,
            create_my_products,
            create_queries_and_suggestions,
            create_aspect_total_scores
        ]

        for func in all_creation_functions:
            self.stdout.write(f"Running {func.__name__}...")
            try:
                func()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error during {func.__name__}: {e}"))
                import traceback
                traceback.print_exc()
                self.stderr.write(self.style.ERROR(f"Stopping population due to error in {func.__name__}."))
                raise e # Stop execution on first error

        self.stdout.write(self.style.SUCCESS('Environmental data population complete.'))
