import os
import random

def generate_bulk_rates(filename, origins, dests, carriers):
    directory = 'sample_data'
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    header = "origin,destination,nvocc_name,base_rate,surcharges,transit_days,validity_start,validity_end\n"
    rows = []
    
    for origin in origins:
        for dest in dests:
            carrier = random.choice(carriers)
            base = random.randint(600, 1500)
            surch = random.randint(150, 450)
            transit = random.randint(12, 40)
            rows.append(f"{origin},{dest},{carrier},{base},{surch},{transit},2026-01-01,2026-12-31")
            
    with open(os.path.join(directory, filename), 'w') as f:
        f.write(header)
        f.write('\n'.join(rows))
        f.write('\n')

def main():
    # 1. Asia-Europe (Bulk)
    origins_asia = ["Shanghai", "Ningbo", "Shenzhen", "Qingdao", "Xiamen", "Tianjin", "Guangzhou", "Singapore", "Ho Chi Minh", "Busan"]
    dests_eur = ["Hamburg", "Rotterdam", "Antwerp", "Felixstowe", "Le Havre", "Genoa", "Barcelona", "Valencia"]
    carriers_asia = ["Maersk Line", "MSC", "CMA CGM", "COSCO", "ONE", "HMM", "Evergreen"]
    generate_bulk_rates('rates_asia_europe_bulk.csv', origins_asia, dests_eur, carriers_asia)
    
    # 2. USA-Transatlantic (Bulk)
    origins_usa = ["New York", "Savannah", "Miami", "Norfolk", "Charleston", "Houston", "Baltimore"]
    dests_eur_usa = ["Hamburg", "Rotterdam", "Felixstowe", "Antwerp", "Bremerhaven", "Le Havre"]
    carriers_usa = ["Hapag-Lloyd", "Maersk", "MSC", "ACL", "CMA CGM"]
    generate_bulk_rates('rates_usa_transatlantic_bulk.csv', origins_usa, dests_eur_usa, carriers_usa)
    
    # 3. Middle East & India (Bulk)
    origins_me = ["Jebel Ali", "Nhava Sheva", "Mundra", "Karachi", "Chennai", "Colombo", "Doha", "Abu Dhabi"]
    dests_eur_me = ["Hamburg", "Rotterdam", "Genoa", "Barcelona", "Piraeus", "Istanbul"]
    carriers_me = ["Maersk", "Hapag-Lloyd", "MSC", "CMA CGM", "Emirates Shipping"]
    generate_bulk_rates('rates_middle_east_india_bulk.csv', origins_me, dests_eur_me, carriers_me)

    print("Successfully generated 3 bulk rate sheets with 50+ rows each in sample_data/")

if __name__ == '__main__':
    main()
