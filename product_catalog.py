#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
product_catalog.py — REALISTYCZNY KATALOG PRODUKTÓW DLA 28 KATEGORII
====================================================================
Zastępuje starą, wadliwą listę VERIFIED_ASINS_BY_CATEGORY, przez którą:
  * kategoria "Musical Instruments" dostawała szczoteczki do zębów,
  * kategoria "Shoes" dostawała kabel HDMI,
  * wyszukiwanie "Apple" zwracało wyłącznie 2 modele MacBooka M1.

Co zawiera ten moduł (tylko biblioteka standardowa, zero zależności):
  1. CATEGORY_PRODUCTS — dla KAŻDEJ z 28 kategorii lista realnych produktów
     (marka, tytuł, cena bazowa USD, typ wariantu).
  2. VARIANT_POOLS      — warianty (kolor / rozmiar / pojemność / rozmiar buta),
     dzięki którym generujemy różnorodne, realistyczne tytuły.
  3. CATEGORY_SALES     — REALISTYCZNE progi sprzedaży 30-dniowej per kategoria
     (np. laptopy max ~3 500 szt./m-c, a nie 40 000).
  4. make_product_title / realistic_sales — funkcje pomocnicze generatora.
"""

import math
import random

# ---------------------------------------------------------------------------
# REALISTYCZNE PROGI SPRZEDAŻY 30-DNIOWEJ (szt./mies.) DLA KAŻDEJ KATEGORII
# ---------------------------------------------------------------------------
# Filozofia: tanie artykuły konsumpcyjne (chemia, kosmetyki, artykuły
# spożywcze, akcesoria) sprzedają się w ogromnych wolumenach; drogie i
# rzadkie towary (komputery, instrumenty, elektronika premium) — znacznie
# mniej. Poniższe widełki odzwierciedlają realia marketplace'ów (PL/DE/UK/FR).
CATEGORY_SALES = {
    "apparel":              (400,  30000),   # odzież masowa
    "appliances":           (150,   9000),   # AGD / RTV duże
    "automotive":           (100,   6000),   # części i akcesoria auto
    "baby":                 (300,  20000),   # pieluchy, wózki, zabawki
    "beauty":               (500,  45000),   # kosmetyki (bardzo wysoki obrót)
    "books":                (200,  15000),   # książki
    "clothing":             (400,  30000),   # moda
    "computers":            (80,    3500),   # LAPTOPY: maks. ~3,5 tys./m-c!
    "drugstore":            (500,  45000),   # drogeria / chemia
    "electronics":          (200,  20000),   # smartfony/słuchawki/akcesoria
    "garden":               (100,   6000),   # ogród
    "grocery":              (600,  45000),   # spożywcze (FMCG)
    "industrial":           (50,    2500),   # przemysł
    "jewelry":              (200,   8000),   # biżuteria
    "kids":                 (400,  20000),   # zabawki
    "kitchen":              (150,  10000),   # kuchnia
    "lighting":             (200,   9000),   # oświetlenie
    "luggage":              (100,   5000),   # walizki / torby
    "musical_instruments":  (50,    3000),   # INSTRUMENTY: niszowy rynek
    "office":               (200,  12000),   # biuro
    "other":                (100,   8000),   # pozostałe
    "outdoors":             (150,  10000),   # outdoor
    "pet_supplies":         (300,  18000),   # zoologia
    "photo":                (60,    2500),   # foto / kamery (drogi sprzęt)
    "shoes":                (300,  22000),   # obuwie
    "sports":               (150,  10000),   # sport
    "tools":                (120,   8000),   # narzędzia
    "watch":                (150,   8000),   # zegarki / smartwatche
}

# ---------------------------------------------------------------------------
# WARIANTY TYTUŁÓW
# ---------------------------------------------------------------------------
VARIANT_POOLS = {
    "color":     ["Czarny", "Biały", "Srebrny", "Niebieski", "Czerwony",
                  "Zielony", "Grafit", "Złoty", "Beżowy", "Fioletowy"],
    "size":      ["Rozmiar S", "Rozmiar M", "Rozmiar L", "Rozmiar XL",
                  "Rozmiar XXL"],
    "shoesize":  ["Rozmiar 38", "Rozmiar 39", "Rozmiar 40", "Rozmiar 41",
                  "Rozmiar 42", "Rozmiar 43", "Rozmiar 44", "Rozmiar 45",
                  "Rozmiar 46", "Rozmiar 47"],
    "capacity":  ["128 GB", "256 GB", "512 GB", "1 TB", "2 TB"],
    "none":      [""],
}

# ---------------------------------------------------------------------------
# KATALOG PRODUKTÓW PER KATEGORIA
# Format wpisu: (marka, tytuł bazowy, cena bazowa USD, typ wariantu)
# ---------------------------------------------------------------------------
CATEGORY_PRODUCTS = {
    "apparel": [
        ("Nike", "Nike Men's Sportswear Club Fleece Full-Zip Hoodie", 55.00, "size"),
        ("Adidas", "Adidas Men's Tiro 23 Training Pants", 45.00, "size"),
        ("Levi's", "Levi's 501 Original Fit Jeans - Classic Blue", 69.50, "size"),
        ("Calvin Klein", "Calvin Klein Men's Cotton Classics 3-Pack Boxer Briefs", 34.50, "size"),
        ("H&M", "H&M Men's Regular Fit Oxford Shirt", 29.99, "size"),
        ("Under Armour", "Under Armour Men's Tech 2.0 Short-Sleeve T-Shirt", 22.00, "size"),
        ("Columbia", "Columbia Men's Silver Ridge Long Sleeve Shirt", 45.00, "size"),
        ("The North Face", "The North Face Men's 1996 Retro Nuptse Jacket", 200.00, "size"),
        ("Carhartt", "Carhartt Men's Loose Fit Midweight Sweatshirt", 55.00, "size"),
        ("Tommy Hilfiger", "Tommy Hilfiger Men's Classic Oxford Shirt", 59.90, "size"),
        ("Gildan", "Gildan Men's Heavy Cotton T-Shirt 6-Pack", 24.99, "size"),
        ("Pepe Jeans", "Pepe Jeans Men's Slim Fit Jeans", 59.00, "size"),
    ],
    "appliances": [
        ("Bosch", "Bosch Series 8 Front-Load Washing Machine 9kg 1400rpm", 799.00, "none"),
        ("Samsung", "Samsung Bespoke French Door Refrigerator 700L", 2199.00, "none"),
        ("LG", "LG WashTower Washer & Dryer Combo", 2199.00, "none"),
        ("Miele", "Miele Complete C3 PowerLine Vacuum Cleaner", 599.00, "none"),
        ("Dyson", "Dyson V15 Detect Cordless Vacuum Cleaner", 649.00, "none"),
        ("Philips", "Philips Airfryer XXL 7.3L Digital", 299.99, "none"),
        ("De'Longhi", "De'Longhi Magnifica S Fully Automatic Espresso Machine", 449.00, "none"),
        ("Electrolux", "Electrolux Pure C9 Vacuum Cleaner", 349.00, "none"),
        ("Rowenta", "Rowenta Turbo Pro Steam Iron 2800W", 89.99, "none"),
        ("Beko", "Beko Freestanding Dishwasher 60cm 14 Place Settings", 399.00, "none"),
    ],
    "automotive": [
        ("NOCO", "NOCO Boost Plus GB40 1000A Lithium Jump Starter", 99.95, "none"),
        ("Michelin", "Michelin CrossClimate 2 All-Season Tire 205/55 R16", 89.00, "none"),
        ("Bosch", "Bosch AeroTwin Wiper Blades Set 2-Piece", 24.99, "none"),
        ("Castrol", "Castrol Edge 5W-30 Engine Oil 4L", 42.00, "none"),
        ("Meguiar's", "Meguiar's Hybrid Ceramic Wax Spray 709ml", 19.99, "none"),
        ("Continental", "Continental EcoContact 6 Summer Tire 195/65 R15", 75.00, "none"),
        ("Philips", "Philips X-tremeVision Pro Car Headlight Bulbs H7", 39.99, "none"),
        ("Varta", "Varta Blue Dynamic E23 Car Battery 74Ah", 99.00, "none"),
        ("Dunlop", "Dunlop Winter Sport 5 Winter Tire 205/55 R16", 95.00, "none"),
        ("Autel", "Autel MaxiCOM MK808 OBD2 Diagnostic Scanner", 499.00, "none"),
    ],
    "baby": [
        ("Pampers", "Pampers Baby-Dry Diapers Size 4 160-Pack", 44.99, "none"),
        ("Philips", "Philips Avent Natural Baby Bottle 4-Pack 260ml", 32.99, "none"),
        ("Chicco", "Chicco Next2Me Magic Side Sleeping Crib", 199.00, "none"),
        ("Graco", "Graco Extend2Fit Convertible Car Seat", 249.00, "none"),
        ("Fisher-Price", "Fisher-Price Rock-a-Stack Classic Toy", 9.99, "none"),
        ("BabyBjorn", "BabyBjorn Baby Carrier One Air", 179.00, "none"),
        ("Britax", "Britax Römer Dualfix M i-Size Car Seat", 329.00, "none"),
        ("Lego", "LEGO DUPLO My First Number Train 10954", 19.99, "none"),
        ("Munchkin", "Munchkin Miracle 360 Sippy Cup 2-Pack", 13.99, "none"),
        ("Skip Hop", "Skip Hop Baby Activity Gym - Silver Lining Cloud", 59.99, "none"),
    ],
    "beauty": [
        ("CeraVe", "CeraVe Moisturizing Cream for Dry Skin 539g", 18.99, "none"),
        ("The Ordinary", "The Ordinary Niacinamide 10% + Zinc 1% 30ml", 11.50, "none"),
        ("L'Oreal", "L'Oreal Paris Revitalift Filler Serum 30ml", 24.99, "none"),
        ("La Roche-Posay", "La Roche-Posay Anthelios SPF50+ Invisible Fluid 50ml", 21.50, "none"),
        ("Dyson", "Dyson Supersonic Hair Dryer Professional Edition", 429.99, "color"),
        ("ghd", "ghd Platinum+ Professional Styler Straightener", 249.00, "none"),
        ("Nivea", "Nivea Soft Moisturizing Cream 200ml", 5.99, "none"),
        ("Estee Lauder", "Estée Lauder Advanced Night Repair Serum 50ml", 89.00, "none"),
        ("Clinique", "Clinique Dramatically Different Moisturizing Gel 125ml", 39.00, "none"),
        ("Maybelline", "Maybelline Lash Sensational Sky High Mascara", 10.99, "none"),
    ],
    "books": [
        ("Penguin", "Book: Atomic Habits by James Clear (Hardcover)", 16.99, "none"),
        ("Canongate", "Book: The Midnight Library by Matt Haig", 14.99, "none"),
        ("Profile Books", "Book: The 48 Laws of Power by Robert Greene", 20.99, "none"),
        ("Vintage", "Book: Sapiens by Yuval Noah Harari", 18.99, "none"),
        ("Taschen", "Book: The Art Book - Revised Edition", 29.99, "none"),
        ("Plata Publishing", "Book: Rich Dad Poor Dad by Robert Kiyosaki", 15.99, "none"),
        ("PWN", "Książka: Pan Tadeusz - Adam Mickiewicz (wyd. kolekcjonerskie)", 29.90, "none"),
        ("Znak", "Książka: Zbrodnia i kara - Fiodor Dostojewski", 39.90, "none"),
        ("Czarne", "Książka: Cesarz - Ryszard Kapuściński", 34.90, "none"),
        ("Wielka Litera", "Książka: Chłopki. Opowieść o naszych babkach", 44.90, "none"),
    ],
    "clothing": [
        ("Nike", "Nike Women's Dri-FIT Running Top", 35.00, "size"),
        ("Adidas", "Adidas Women's Tiro 23 Track Jacket", 49.95, "size"),
        ("Hugo Boss", "Hugo Boss Men's Slim Fit Suit Jacket", 399.00, "size"),
        ("Massimo Dutti", "Massimo Dutti Women's Cashmere Sweater", 129.00, "size"),
        ("Pepe Jeans", "Pepe Jeans Men's Skinny Jeans", 59.00, "size"),
        ("H&M", "H&M Women's Wide Leg Trousers", 24.99, "size"),
        ("Uniqlo", "Uniqlo Men's Ultra Light Down Jacket", 69.90, "size"),
        ("Zara", "Zara Men's Classic Fit Blazer", 89.90, "size"),
        ("Lacoste", "Lacoste Men's Classic Pique Polo Shirt", 89.00, "size"),
        ("Reserved", "Reserved Women's Midi Dress", 39.99, "size"),
    ],
    "computers": [
        ("Apple", "Apple MacBook Air 13-inch M2 8-core 8GB/256GB", 1099.00, "capacity"),
        ("Apple", "Apple MacBook Air 15-inch M2 8-core 8GB/256GB", 1299.00, "capacity"),
        ("Apple", "Apple MacBook Air 13-inch M3 8-core 16GB/512GB", 1399.00, "capacity"),
        ("Apple", "Apple MacBook Pro 14-inch M3 Pro 18GB/512GB", 1999.00, "capacity"),
        ("Apple", "Apple MacBook Pro 16-inch M3 Max 36GB/1TB", 3499.00, "capacity"),
        ("Apple", "Apple iMac 24-inch M3 All-in-One 8GB/256GB", 1399.00, "capacity"),
        ("Apple", "Apple Mac mini M2 8GB/256GB Desktop Computer", 599.00, "capacity"),
        ("Apple", "Apple Mac Studio M2 Ultra 64GB/1TB", 3999.00, "capacity"),
        ("Apple", "Apple iPad Pro 11-inch M4 8GB/256GB Tablet", 999.00, "capacity"),
        ("Apple", "Apple iPad Air 13-inch M2 8GB/128GB Tablet", 799.00, "capacity"),
        ("Apple", "Apple iPad 10.9-inch 10th Generation 64GB", 449.00, "capacity"),
        ("ASUS", "ASUS ROG Zephyrus G14 Gaming Laptop 14-inch RTX 4060", 1599.00, "capacity"),
        ("Lenovo", "Lenovo ThinkPad X1 Carbon Gen 11 14-inch i7", 1799.00, "capacity"),
        ("Dell", "Dell XPS 15 9530 15.6-inch i7 RTX 4070", 2199.00, "capacity"),
        ("HP", "HP Spectre x360 16-inch 2-in-1 i7 16GB/1TB", 1499.00, "capacity"),
        ("Acer", "Acer Swift 3 14-inch Ryzen 7 16GB/512GB", 749.00, "capacity"),
        ("MSI", "MSI Katana 15 15.6-inch RTX 4060 Gaming Laptop", 1299.00, "capacity"),
        ("Samsung", "Samsung Galaxy Book3 Pro 14-inch i7 16GB", 1249.00, "capacity"),
        ("Logitech", "Logitech MX Master 3S Wireless Performance Mouse", 99.99, "none"),
        ("Logitech", "Logitech MX Keys S Wireless Illuminated Keyboard", 109.99, "none"),
        ("LG", "LG UltraFine 27-inch 4K UHD USB-C Monitor", 499.00, "none"),
        ("Samsung", "Samsung T7 Shield 2TB Portable SSD", 149.99, "capacity"),
        ("Razer", "Razer BlackWidow V4 Mechanical Gaming Keyboard", 179.99, "none"),
        ("ASUS", "ASUS ROG Strix 27-inch 1440p 170Hz Gaming Monitor", 399.00, "none"),
    ],
    "drugstore": [
        ("Oral-B", "Oral-B Pro 1000 CrossAction Electric Toothbrush", 49.99, "none"),
        ("Philips", "Philips Sonicare ProtectiveClean 5100 Electric Toothbrush", 79.99, "none"),
        ("Colgate", "Colgate Total Whitening Toothpaste 6-Pack 75ml", 14.99, "none"),
        ("Gillette", "Gillette Fusion5 ProGlide Razor Blades 12-Pack", 39.99, "none"),
        ("Head & Shoulders", "Head & Shoulders Classic Clean Shampoo 500ml", 6.49, "none"),
        ("Dove", "Dove Men+Care Shower Gel 6-Pack 250ml", 17.99, "none"),
        ("Sensodyne", "Sensodyne Pronamel Toothpaste 75ml", 6.99, "none"),
        ("Nivea", "Nivea Men Active Energy Shower Gel 250ml", 4.99, "none"),
        ("Pantene", "Pantene Pro-V Repair & Care Conditioner 400ml", 7.99, "none"),
        ("Listerine", "Listerine Cool Mint Mouthwash 6x500ml", 24.99, "none"),
    ],
    "electronics": [
        ("Apple", "Apple AirPods Pro (2nd Generation) with USB-C", 249.00, "none"),
        ("Apple", "Apple AirPods (3rd Generation)", 169.00, "none"),
        ("Apple", "Apple AirPods Max - Space Gray", 549.00, "none"),
        ("Apple", "Apple iPhone 15 128GB Smartphone", 799.00, "capacity"),
        ("Apple", "Apple iPhone 15 Plus 128GB Smartphone", 899.00, "capacity"),
        ("Apple", "Apple iPhone 15 Pro 128GB Titanium", 999.00, "capacity"),
        ("Apple", "Apple iPhone 15 Pro Max 256GB Titanium", 1199.00, "capacity"),
        ("Apple", "Apple iPhone 14 128GB Smartphone", 699.00, "capacity"),
        ("Apple", "Apple iPhone SE (3rd Generation) 64GB", 429.00, "capacity"),
        ("Apple", "Apple HomePod mini Smart Speaker", 99.00, "none"),
        ("Apple", "Apple TV 4K (3rd Generation) 64GB", 149.00, "capacity"),
        ("Apple", "Apple AirTag (4-Pack) Item Tracker", 99.00, "none"),
        ("Apple", "Apple MagSafe Charger", 39.00, "none"),
        ("Apple", "Apple 20W USB-C Power Adapter", 19.00, "none"),
        ("Apple", "Apple USB-C to Lightning Cable (1m)", 19.00, "none"),
        ("Sony", "Sony WH-1000XM5 Wireless Noise Cancelling Headphones", 399.00, "color"),
        ("Bose", "Bose QuietComfort Ultra Wireless Noise Cancelling Headphones", 429.00, "none"),
        ("Samsung", "Samsung 55-inch QLED 4K Smart TV Q80C", 1099.00, "none"),
        ("LG", "LG OLED evo 65-inch 4K Smart TV G3", 1999.00, "none"),
        ("JBL", "JBL Flip 6 Waterproof Portable Bluetooth Speaker", 129.95, "color"),
        ("Anker", "Anker PowerCore 20000mAh Portable Power Bank", 49.99, "none"),
        ("Xiaomi", "Xiaomi Redmi Note 13 Pro 5G 256GB", 329.00, "capacity"),
        ("Samsung", "Samsung Galaxy S24 5G 128GB", 859.00, "capacity"),
        ("Samsung", "Samsung Galaxy Buds2 Pro True Wireless", 179.99, "none"),
        ("Amazon", "Amazon Echo Dot (5th Gen) Smart Speaker", 49.99, "none"),
        ("Philips", "Philips Hue White & Color Ambiance Starter Kit", 199.99, "none"),
    ],
    "garden": [
        ("Karcher", "Kärcher K5 Premium High Pressure Washer", 399.00, "none"),
        ("Greenworks", "Greenworks 40V 16-inch Cordless Lawn Mower", 299.00, "none"),
        ("Bosch", "Bosch Rotak 43 LI Cordless Lawnmower", 349.00, "none"),
        ("Husqvarna", "Husqvarna Automower 415X Robotic Lawn Mower", 1699.00, "none"),
        ("Fiskars", "Fiskars Bypass Pruning Shears - Steel Blade", 16.99, "none"),
        ("Gardena", "Gardena Comfort Garden Hose 50m", 59.99, "none"),
        ("Sun Joe", "Sun Joe SPX3000 Electric Pressure Washer", 169.00, "none"),
        ("STIHL", "STIHL MSA 200 C-B Cordless Chainsaw", 399.00, "none"),
        ("Wolf-Garten", "Wolf-Garten Multi-Change Cultivator Set", 49.99, "none"),
        ("Outsunny", "Outsunny 3x2m Garden Gazebo with Netting", 129.99, "none"),
    ],
    "grocery": [
        ("Nestle", "Nestlé KitKat 4-Finger Milk Chocolate 24-Pack", 19.99, "none"),
        ("Kellogg's", "Kellogg's Corn Flakes 750g", 3.99, "none"),
        ("Coca-Cola", "Coca-Cola Original Taste 24x330ml Cans", 15.99, "none"),
        ("Nescafe", "Nescafé Gold Blend Instant Coffee 200g", 12.99, "none"),
        ("Lipton", "Lipton Yellow Label Tea 100 Tea Bags", 6.99, "none"),
        ("Milka", "Milka Alpine Milk Chocolate 300g", 4.99, "none"),
        ("Danone", "Danone Activia Natural Yogurt 8x125g", 5.49, "none"),
        ("Barilla", "Barilla Spaghetti Pasta 500g", 2.49, "none"),
        ("Lavazza", "Lavazza Qualità Rossa Coffee Beans 1kg", 13.99, "none"),
        ("Ferrero", "Ferrero Rocher 24-Piece Chocolate Box", 14.99, "none"),
    ],
    "industrial": [
        ("3M", "3M Peltor X5A Over-the-Head Ear Protection", 34.99, "none"),
        ("Stanley", "Stanley FatMax 16m Tape Measure", 24.99, "none"),
        ("DEWALT", "DEWALT 5m Laser Distance Measurer", 99.00, "none"),
        ("Bosch", "Bosch GSB 13 RE Impact Drill 600W", 89.00, "none"),
        ("Makita", "Makita HR2470 Rotary Hammer 780W", 199.00, "none"),
        ("Wera", "Wera Kraftform Plus Screwdriver Set 26-Piece", 79.00, "none"),
        ("Knipex", "Knipex Cobra Water Pump Pliers 250mm", 49.90, "none"),
        ("RIDGID", "RIDGID 36A Heavy-Duty Pipe Wrench 14-inch", 55.00, "none"),
        ("Hilti", "Hilti TE 4-A22 Cordless Rotary Hammer", 899.00, "none"),
        ("Milwaukee", "Milwaukee M18 FUEL 1/2-inch Impact Wrench", 299.00, "none"),
    ],
    "jewelry": [
        ("Pandora", "Pandora Moments Heart Charm", 45.00, "none"),
        ("Swarovski", "Swarovski Crystal Tennis Bracelet", 199.00, "none"),
        ("Thomas Sabo", "Thomas Sabo Sterling Silver Necklace", 89.00, "none"),
        ("TOUS", "TOUS Bear Sterling Silver Earrings", 69.00, "none"),
        ("ARCOR", "ARCOR 14k Yellow Gold Chain 45cm", 499.00, "none"),
        ("W.Kruk", "W.Kruk Diamond Stud Earrings 0.10ct", 1299.00, "none"),
        ("APART", "APART Gold-Plated Bangle", 399.00, "none"),
        ("YES", "YES! Silver Bangle Set of 3", 89.00, "none"),
        ("Kruger", "Kruger Sterling Silver Ring", 59.00, "none"),
        ("Michael Kors", "Michael Kors Gold-Tone Bracelet", 149.00, "none"),
    ],
    "kids": [
        ("Lego", "LEGO City Police Station 60316 Building Kit", 99.99, "none"),
        ("LEGO", "LEGO Technic Bugatti Bolide 42151", 49.99, "none"),
        ("LEGO", "LEGO Harry Potter Hogwarts Castle 76405", 449.99, "none"),
        ("Hasbro", "Hasbro Nerf Elite 2.0 Commander Blaster", 24.99, "none"),
        ("Mattel", "Mattel Hot Wheels 20-Car Gift Pack", 24.99, "none"),
        ("Fisher-Price", "Fisher-Price Laugh & Learn Smart Stages Chair", 34.99, "none"),
        ("PAW Patrol", "PAW Patrol Mighty Pups Lookout Tower", 59.99, "none"),
        ("Ravensburger", "Ravensburger 1000-Piece Puzzle - Skyline", 19.99, "none"),
        ("VTech", "VTech KidiZoom Smartwatch DX2", 49.99, "none"),
        ("PLAYMOBIL", "PLAYMOBIL 1.2.3 Aqua Park 71350", 29.99, "none"),
    ],
    "kitchen": [
        ("Ninja", "Ninja Foodi MAX Dual Zone Air Fryer 9.5L", 229.00, "none"),
        ("Instant Pot", "Instant Pot Duo Plus 9-in-1 Pressure Cooker 6QT", 119.95, "none"),
        ("De'Longhi", "De'Longhi Magnifica S ECAM 22.110.B Espresso Machine", 449.00, "none"),
        ("KitchenAid", "KitchenAid Artisan 5QT Stand Mixer - Empire Red", 379.99, "color"),
        ("Philips", "Philips Premium Airfryer XXL 7.3L", 299.99, "none"),
        ("Tefal", "Tefal Ingenio Non-Stick Cookware Set 12-Piece", 149.00, "none"),
        ("Zwilling", "Zwilling Pro Chef Knife 20cm", 99.00, "none"),
        ("Le Creuset", "Le Creuset Cast Iron Dutch Oven 24cm", 329.00, "color"),
        ("Bodum", "Bodum Chambord French Press Coffee Maker 1L", 34.95, "none"),
        ("Sage", "Sage Barista Express Espresso Machine", 749.00, "none"),
        ("SMEG", "SMEG Retro Electric Kettle 1.7L", 139.00, "color"),
        ("Russell Hobbs", "Russell Hobbs 2-Slice Toaster", 34.99, "none"),
    ],
    "lighting": [
        ("Philips", "Philips Hue White Smart Bulb 2-Pack", 39.99, "none"),
        ("IKEA", "IKEA TRÅDFRI LED Bulb 3-Pack E27", 24.99, "none"),
        ("Nanoleaf", "Nanoleaf Shapes Hexagon Starter Kit", 199.99, "none"),
        ("Govee", "Govee LED Strip Lights 10m RGBIC", 39.99, "none"),
        ("Osram", "Osram LEDvance Smart+ WiFi Bulb", 19.99, "none"),
        ("LIFX", "LIFX Color A19 Smart Bulb", 49.99, "none"),
        ("Paulmann", "Paulmann Smart LED Panel 60x60cm", 89.99, "none"),
        ("HAMA", "HAMA LED String Lights 200 LEDs", 12.99, "none"),
        ("Astro", "Astro Gozo Floor Lamp", 149.00, "none"),
        ("Briloner", "Briloner LED Ceiling Lamp 3-Bulb", 49.99, "none"),
    ],
    "luggage": [
        ("Samsonite", "Samsonite S'Cure Spinner 55cm Cabin Case", 199.00, "color"),
        ("American Tourister", "American Tourister Vibe Spinner 67cm", 129.00, "color"),
        ("RIMOWA", "RIMOWA Essential Cabin S 33L", 1450.00, "none"),
        ("Delsey", "Delsey Helium Aero 55cm Cabin Trolley", 179.00, "none"),
        ("Bric's", "Bric's Bellagio 2.0 Trolley 67cm", 349.00, "none"),
        ("Eastpak", "Eastpak Tranverz L Duffel Bag 60L", 99.00, "color"),
        ("Herschel", "Herschel Settlement Backpack", 64.99, "color"),
        ("Samsonite", "Samsonite Liteshock Laptop Backpack", 89.00, "none"),
        ("TUMI", "TUMI Alpha 3 Brief Pack", 595.00, "none"),
        ("Victorinox", "Victorinox Werks Traveler 2.0 55cm", 249.00, "none"),
    ],
    "musical_instruments": [
        ("Fender", "Fender Player Stratocaster Electric Guitar", 799.00, "color"),
        ("Gibson", "Gibson Les Paul Standard '60s Electric Guitar", 2699.00, "color"),
        ("Yamaha", "Yamaha P-125 Digital Piano 88-Key", 599.00, "none"),
        ("Yamaha", "Yamaha FG800 Solid Top Acoustic Guitar", 199.00, "none"),
        ("Epiphone", "Epiphone SG Standard Electric Guitar", 549.00, "color"),
        ("Ibanez", "Ibanez GRX70QA Electric Guitar", 199.00, "color"),
        ("Shure", "Shure SM58-LC Vocal Microphone", 99.00, "none"),
        ("Roland", "Roland TD-07KV Electronic Drum Kit", 999.00, "none"),
        ("Squier", "Squier Affinity Series Telecaster Guitar", 249.00, "color"),
        ("Fender", "Fender Champion 20 Guitar Amplifier", 139.00, "none"),
        ("Korg", "Korg B2 88-Key Digital Piano", 549.00, "none"),
        ("Stagg", "Stagg Violin Outfit 4/4 Full Size", 119.00, "none"),
        ("Casio", "Casio CT-S300 61-Key Portable Keyboard", 129.00, "none"),
        ("Roland", "Roland FP-10 88-Key Digital Piano", 499.00, "none"),
        ("Pearl", "Pearl Roadshow 5-Piece Drum Set with Cymbals", 549.00, "none"),
        ("Snark", "Snark SN-8 Clip-On Instrument Tuner", 19.99, "none"),
        ("D'Addario", "D'Addario EJ16 Phosphor Bronze Guitar Strings", 7.99, "none"),
        ("Marshall", "Marshall MG15GR 15W Guitar Combo Amplifier", 129.00, "none"),
        ("Hohner", "Hohner Special 20 Harmonica", 39.90, "none"),
        ("Kawai", "Kawai ES120 88-Key Digital Piano", 799.00, "none"),
        ("Martin", "Martin D-28 Acoustic Guitar", 2699.00, "none"),
        ("Yamaha", "Yamaha YRS-302B Soprano Recorder", 6.99, "none"),
    ],
    "office": [
        ("Fellowes", "Fellowes P-48C Paper Shredder", 59.99, "none"),
        ("HP", "HP DeskJet 2752 Wireless Inkjet Printer", 89.99, "none"),
        ("Brother", "Brother HL-L2350DW Laser Printer", 129.00, "none"),
        ("Canon", "Canon PIXMA TS3350 All-in-One Printer", 69.99, "none"),
        ("Ergotron", "Ergotron LX Monitor Arm", 139.00, "none"),
        ("Secretlab", "Secretlab TITAN Evo Gaming Chair", 549.00, "none"),
        ("IKEA", "IKEA MARKUS Office Chair", 199.00, "none"),
        ("Fellowes", "Fellowes Mousepad with Gel Wrist Rest", 12.99, "none"),
        ("Avery", "Avery A4 Address Labels 100-Pack", 9.99, "none"),
        ("Leitz", "Leitz 5532 Heavy-Duty Hole Punch", 24.99, "none"),
        ("Staedtler", "Staedtler Noris 120 Graphite Pencils 12-Pack", 8.99, "none"),
        ("Pelikan", "Pelikan 4001 Fountain Pen Ink 4x30ml", 19.99, "none"),
        ("Herman Miller", "Herman Miller Aeron Ergonomic Chair", 1495.00, "none"),
    ],
    "other": [
        ("IKEA", "IKEA BILLY Bookcase White", 89.99, "none"),
        ("Amazon Basics", "Amazon Basics Paper Towels 12-Pack", 29.99, "none"),
        ("Generic", "Multipurpose Plastic Storage Box 60L", 19.99, "none"),
        ("Generic", "LED Desk Lamp with Touch Control", 24.99, "none"),
        ("Generic", "Stainless Steel Insulated Water Bottle 1L", 14.99, "color"),
        ("Generic", "Non-Slip Bathroom Mat 60x90cm", 12.99, "color"),
        ("Generic", "Gift Box Set with Ribbon - 5 Pieces", 15.99, "none"),
        ("Generic", "Photo Frame 15x20cm Set of 2", 17.99, "none"),
        ("Generic", "Scented Candle Gift Set 3-Pack", 21.99, "none"),
        ("Generic", "Silent Quartz Wall Clock", 19.99, "none"),
    ],
    "outdoors": [
        ("The North Face", "The North Face Resolve 2 Waterproof Jacket", 99.00, "size"),
        ("Jack Wolfskin", "Jack Wolfskin Vojo 3 Texapore Hiking Boots", 129.00, "shoesize"),
        ("Salomon", "Salomon Speedcross 6 Trail Running Shoes", 139.95, "shoesize"),
        ("Quechua", "Quechua 2 Seconds Easy Pop-Up Tent 3-Person", 99.99, "none"),
        ("Coleman", "Coleman FyreNight 3-Person Tent", 149.00, "none"),
        ("Thermos", "Thermos Stainless Steel Flask 1.2L", 49.99, "none"),
        ("Stanley", "Stanley Classic Adventure Flask 1.1L", 44.99, "none"),
        ("Black Diamond", "Black Diamond Trail Backpack 25L", 89.95, "color"),
        ("Petzl", "Petzl Actik Core Rechargeable Headlamp", 59.95, "none"),
        ("Sea to Summit", "Sea to Summit Aeros Ultralight Pillow", 29.95, "none"),
        ("Fjallraven", "Fjällräven Kånken Classic Backpack", 109.00, "color"),
        ("Osprey", "Osprey Daylite Daypack 20L", 70.00, "color"),
    ],
    "pet_supplies": [
        ("Royal Canin", "Royal Canin Maxi Adult Dog Food 15kg", 79.99, "none"),
        ("Hill's", "Hill's Science Diet Adult Dog Food 12kg", 74.99, "none"),
        ("Whiskas", "Whiskas 1+ Years Cat Food 10kg", 34.99, "none"),
        ("Pedigree", "Pedigree Adult Complete Dry Dog Food 10kg", 29.99, "none"),
        ("Trixie", "Trixie Cat Tree 3-Level with Sisal Posts", 49.99, "none"),
        ("KONG", "KONG Classic Dog Toy Size L", 13.99, "none"),
        ("PetSafe", "PetSafe Automatic Dog Food Feeder", 89.99, "none"),
        ("Ferplast", "Ferplast Atlas 120 Pet Cage", 129.00, "none"),
        ("Rocco", "Rocco Classic Beef Dog Food 12x800g", 39.99, "none"),
        ("Josera", "Josera Sensitive Dog Food 12.5kg", 49.99, "none"),
    ],
    "photo": [
        ("Canon", "Canon EOS R50 Mirrorless Camera with 18-45mm Lens", 679.00, "none"),
        ("Canon", "Canon EOS 2000D DSLR Camera with 18-55mm", 549.00, "none"),
        ("Nikon", "Nikon D7500 DSLR Camera Body", 999.00, "none"),
        ("Nikon", "Nikon Z50 Mirrorless Camera with 16-50mm", 859.00, "none"),
        ("Sony", "Sony Alpha A7 IV Full-Frame Mirrorless Camera", 2499.00, "none"),
        ("Fujifilm", "Fujifilm X-T30 II Camera with 18-55mm", 1299.00, "none"),
        ("GoPro", "GoPro HERO12 Black Action Camera", 399.99, "none"),
        ("DJI", "DJI Mini 4 Pro Drone with Remote", 759.00, "none"),
        ("Instax", "Fujifilm Instax Mini 12 Instant Camera", 69.99, "color"),
        ("SanDisk", "SanDisk 128GB Extreme PRO SDXC Memory Card", 24.99, "none"),
        ("Manfrotto", "Manfrotto BeFree Compact Tripod", 159.00, "none"),
        ("Tamron", "Tamron 18-200mm Di II VC Lens", 449.00, "none"),
    ],
    "shoes": [
        ("Nike", "Nike Air Max 270 Men's Running Shoes", 119.00, "shoesize"),
        ("Nike", "Nike Air Force 1 '07 Men's Sneakers", 99.00, "shoesize"),
        ("Nike", "Nike Pegasus 41 Men's Running Shoes", 139.00, "shoesize"),
        ("Adidas", "Adidas Ultraboost 22 Running Shoes", 159.95, "shoesize"),
        ("Adidas", "Adidas Samba OG Classic Sneakers", 99.95, "shoesize"),
        ("New Balance", "New Balance 574 Classic Sneakers", 89.99, "shoesize"),
        ("New Balance", "New Balance Fresh Foam 1080v12", 149.99, "shoesize"),
        ("ASICS", "ASICS Gel-Kayano 29 Running Shoes", 159.95, "shoesize"),
        ("Puma", "Puma Suede Classic Sneakers", 79.95, "shoesize"),
        ("Vans", "Vans Old Skool Classic Skate Shoes", 69.00, "shoesize"),
        ("Converse", "Converse Chuck Taylor All Star High Top", 74.99, "shoesize"),
        ("Crocs", "Crocs Classic Clogs", 49.99, "shoesize"),
        ("Birkenstock", "Birkenstock Arizona Sandals", 64.99, "shoesize"),
        ("Timberland", "Timberland 6-Inch Premium Waterproof Boots", 185.00, "shoesize"),
        ("Skechers", "Skechers Go Walk 5 Sneakers", 84.99, "shoesize"),
        ("Salomon", "Salomon X Ultra 4 GTX Hiking Boots", 159.95, "shoesize"),
        ("Dr. Martens", "Dr. Martens 1460 Smooth Leather Boots", 179.00, "shoesize"),
    ],
    "sports": [
        ("Bowflex", "Bowflex SelectTech 552 Adjustable Dumbbells (Pair)", 429.00, "none"),
        ("Garmin", "Garmin Forerunner 265 GPS Running Watch", 449.99, "none"),
        ("Fitbit", "Fitbit Charge 6 Advanced Fitness Tracker", 159.95, "none"),
        ("Nike", "Nike Competition Ball - Size 5 Football", 29.99, "none"),
        ("Wilson", "Wilson NBA DRV Basketball - Size 7", 29.99, "none"),
        ("Adidas", "Adidas 4-Stripes Soccer Ball - Size 5", 24.99, "none"),
        ("Tunturi", "Tunturi Weight Bench with 50kg Weight Set", 199.00, "none"),
        ("DOMYOS", "DOMYOS Folding Treadmill 120", 599.00, "none"),
        ("NordicTrack", "NordicTrack Commercial 1750 Treadmill", 1799.00, "none"),
        ("Yonex", "Yonex Badminton Racket Set of 2", 49.99, "none"),
        ("KETTLER", "KETTLER Home Trainer Exercise Bike", 399.00, "none"),
        ("Polar", "Polar H10 Heart Rate Sensor", 89.95, "none"),
        ("Decathlon", "Decathlon B'TWIN 100 City Bike", 299.00, "none"),
        ("Liforme", "Liforme Yoga Mat - Eco-Friendly", 99.00, "color"),
    ],
    "tools": [
        ("Bosch", "Bosch Professional GSR 18V-55 Cordless Drill", 149.00, "none"),
        ("Bosch", "Bosch PSB 500 RE Impact Drill 500W", 79.00, "none"),
        ("DEWALT", "DEWALT DCD771C2 20V Max Drill/Driver Kit", 139.00, "none"),
        ("Makita", "Makita DHP484Z 18V Combi Drill", 129.00, "none"),
        ("Makita", "Makita 18V LXT Circular Saw 165mm", 199.00, "none"),
        ("Stanley", "Stanley 65-Piece Homeowner's Tool Kit", 49.99, "none"),
        ("Milwaukee", "Milwaukee M18 FUEL Hammer Drill", 249.00, "none"),
        ("Einhell", "Einhell TE-CD 18/40 Li-i Cordless Drill", 69.99, "none"),
        ("Hilti", "Hilti SF 2-A12 Cordless Drill", 249.00, "none"),
        ("Festool", "Festool TS 55 F Plunge-Cut Circular Saw", 829.00, "none"),
        ("Black+Decker", "BLACK+DECKER 20V Max Cordless Drill Kit", 79.00, "none"),
        ("Knipex", "Knipex 250mm Cobra Water Pump Pliers", 49.90, "none"),
        ("Wera", "Wera Kraftform Micro Screwdriver Set", 59.90, "none"),
        ("Irwin", "Irwin VISE-GRIP 10-inch Locking Pliers", 24.99, "none"),
    ],
    "watch": [
        ("Apple", "Apple Watch Series 9 GPS 45mm", 429.00, "color"),
        ("Apple", "Apple Watch Ultra 2 GPS+Cellular 49mm", 799.00, "none"),
        ("Apple", "Apple Watch SE (2nd Gen) GPS 44mm", 249.00, "color"),
        ("Apple", "Apple Watch Sport Band 38/40/41mm", 49.00, "color"),
        ("Casio", "Casio G-Shock GA-2100 Watch", 99.00, "color"),
        ("Casio", "Casio Classic F-91W Digital Watch", 14.99, "none"),
        ("Seiko", "Seiko 5 Sports Automatic Watch", 219.00, "color"),
        ("Orient", "Orient Bambino Automatic Dress Watch", 249.00, "color"),
        ("Tissot", "Tissot PRX Powermatic 80 Watch", 675.00, "color"),
        ("Swatch", "Swatch Original Gent Watch", 84.99, "color"),
        ("Fossil", "Fossil Gen 6 Hybrid Smartwatch", 249.00, "color"),
        ("Garmin", "Garmin Venu 3 GPS Smartwatch", 449.99, "none"),
        ("Timex", "Timex Weekender 38mm Watch", 34.99, "none"),
        ("Longines", "Longines HydroConquest Automatic Watch", 1350.00, "color"),
        ("Michael Kors", "Michael Kors Access Lexington Smartwatch", 199.00, "color"),
    ],
}

# ---------------------------------------------------------------------------
# FUNKCJE POMOCNICZE
# ---------------------------------------------------------------------------
def make_product_title(base_title, variant_kind, seed_idx):
    """Zwraca realistyczny tytuł z wariantem (kolor/rozmiar/pojemność).
    seed_idx gwarantuje deterministyczną różnorodność bez powtórzeń."""
    pool = VARIANT_POOLS.get(variant_kind, [""])
    if not pool or pool == [""]:
        return base_title
    variant = pool[seed_idx % len(pool)]
    return f"{base_title} - {variant}" if variant else base_title


def realistic_sales(category_slug, price_usd, rng=None):
    """Realistyczny wolumen sprzedaży 30-dniowej dla danej kategorii i ceny.

    Zasady:
      * widełki kategorii (CATEGORY_SALES) — np. laptopy max ~3 500 szt./m-c;
      * rozkład log-regularny (większość produktów średnio, część hitów);
      * współczynnik ceny — tanie produkty konsumpcyjne sprzedają się lepiej;
      * sporadyczny "boost" bestsellera (5% ofert)."""
    if rng is None:
        rng = random
    lo, hi = CATEGORY_SALES.get(category_slug, (100, 8000))
    log_lo, log_hi = math.log(lo), math.log(hi)
    base = math.exp(rng.uniform(log_lo, log_hi))
    # cena: poniżej ~200 USD sprzedaż pełna, powyżej maleje
    price_factor = max(0.40, min(1.0, 200.0 / max(price_usd, 1.0)))
    vol = base * price_factor
    if rng.random() < 0.05:
        vol *= rng.uniform(1.5, 2.5)
    return max(20, min(int(round(vol)), int(hi * 1.10)))


def random_product_for_category(category_slug, rng=None):
    """Losuje produkt (marka, tytuł bazowy, cena USD, typ wariantu) dla kategorii."""
    if rng is None:
        rng = random
    pool = CATEGORY_PRODUCTS.get(category_slug)
    if not pool:
        pool = CATEGORY_PRODUCTS.get("other", [])
    return rng.choice(pool)


def product_count_for_category(category_slug):
    return len(CATEGORY_PRODUCTS.get(category_slug, []))
