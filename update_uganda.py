import os
import re

replacements = [
    (r'\$45k', 'UGX 45M'),
    (r'\$22k', 'UGX 22M'),
    (r'\$80k', 'UGX 80M'),
    (r'\$12k', 'UGX 12M'),
    (r'\$30k', 'UGX 30M'),
    (r'\$18k', 'UGX 18M'),
    (r'\$65k', 'UGX 65M'),
    (r'\$38k', 'UGX 38M'),
    (r'Victoria Island, Lagos', 'Kololo, Kampala'),
    (r'Victoria Island', 'Kololo'),
    (r'Lekki Phase 1, Lagos', 'Naalya, Kampala'),
    (r'Lekki Phase 1', 'Naalya'),
    (r'Lekki', 'Naalya'),
    (r'Ikoyi', 'Muyenga'),
    (r'Maitama, Abuja', 'Ntinda, Kampala'),
    (r'Banana Island', 'Kira'),
    (r'Wuse 2, Abuja', 'Najjera, Kampala'),
    (r'Asokoro, Abuja', 'Entebbe'),
    (r'Eko Atlantic', 'Naguru'),
    (r'\$12,500', 'UGX 12.5M'),
    (r'\$45,000', 'UGX 45M'),
    (r'\$22,000', 'UGX 22M'),
    (r'\$4,500', 'UGX 4.5M'),
    (r'\$450', 'UGX 450K'),
    (r'\$49,950', 'UGX 49.95M'),
]

templates_dir = '/home/ronnie/trust_files/core/templates'
for root, _, files in os.walk(templates_dir):
    for filename in files:
        if filename.endswith('.html'):
            filepath = os.path.join(root, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements:
                new_content = re.sub(old, new, new_content)
            
            if content != new_content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
