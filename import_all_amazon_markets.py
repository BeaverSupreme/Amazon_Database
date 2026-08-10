#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_all_amazon_markets.py — WIELOPLATFORMOWY IMPORTER E-COMMERCE (0 zł / Chmura)
===================================================================================
ZAKTUALIZOWANA WERSJA MULTI-MARKETPLACE:
Obsługuje 5 największych platform e-commerce na świecie (w tym polskie Allegro!):
  1. Amazon     (amazon.pl, amazon.de, amazon.co.uk, amazon.com...)
  2. Allegro    (allegro.pl — lider e-commerce w Polsce i Europie Środkowej)
  3. eBay       (ebay.com, ebay.de, ebay.co.uk...)
  4. AliExpress (aliexpress.com / aliexpress.pl)
  5. Walmart    (walmart.com — gigant w USA)

Użycie na Render.com / lokalnie:
  python3 import_all_amazon_markets.py --seed-all 100000
"""

import os
import re
import csv
import sys
import time
import json
import random
import sqlite3
import argparse
import tempfile
import urllib.request
import urllib.parse
from html import unescape

# 5 Największych platform E-Commerce
PLATFORMS = [
    {"code": "Amazon", "name": "Amazon (8 rynków)", "domain": "amazon.com", "weight": 450000},
    {"code": "Allegro", "name": "Allegro (Polska/CEE)", "domain": "allegro.pl", "weight": 280000},
    {"code": "eBay", "name": "eBay (Global)", "domain": "ebay.com", "weight": 180000},
    {"code": "AliExpress", "name": "AliExpress (Global/PL)", "domain": "aliexpress.pl", "weight": 140000},
    {"code": "Walmart", "name": "Walmart (USA)", "domain": "walmart.com", "weight": 110000}
]

MARKETPLACES = [
    {"code": "PL", "name": "Poland", "domain": "amazon.pl", "weight": 310000, "currency": "PLN", "symbol": "zł", "rate": 3.98},
    {"code": "DE", "name": "Germany", "domain": "amazon.de", "weight": 493232, "currency": "EUR", "symbol": "€", "rate": 0.92},
    {"code": "UK", "name": "United Kingdom", "domain": "amazon.co.uk", "weight": 503063, "currency": "GBP", "symbol": "£", "rate": 0.78},
    {"code": "US", "name": "United States", "domain": "amazon.com", "weight": 588184, "currency": "USD", "symbol": "$", "rate": 1.00},
    {"code": "FR", "name": "France", "domain": "amazon.fr", "weight": 461861, "currency": "EUR", "symbol": "€", "rate": 0.92},
    {"code": "IT", "name": "Italy", "domain": "amazon.it", "weight": 447828, "currency": "EUR", "symbol": "€", "rate": 0.92},
    {"code": "ES", "name": "Spain", "domain": "amazon.es", "weight": 406369, "currency": "EUR", "symbol": "€", "rate": 0.92},
    {"code": "CA", "name": "Canada", "domain": "amazon.ca", "weight": 386550, "currency": "CAD", "symbol": "$", "rate": 1.36}
]

CATEGORIES = [
    {"slug": "apparel", "name": "Apparel", "weight": 365923},
    {"slug": "appliances", "name": "Appliances", "weight": 26663},
    {"slug": "automotive", "name": "Automotive", "weight": 160610},
    {"slug": "baby", "name": "Baby", "weight": 119506},
    {"slug": "beauty", "name": "Beauty", "weight": 69743},
    {"slug": "books", "name": "Books", "weight": 4470},
    {"slug": "clothing", "name": "Clothing", "weight": 35550},
    {"slug": "computers", "name": "Computers", "weight": 68344},
    {"slug": "drugstore", "name": "Drugstore", "weight": 111296},
    {"slug": "electronics", "name": "Electronics", "weight": 123476},
    {"slug": "garden", "name": "Garden", "weight": 106771},
    {"slug": "grocery", "name": "Grocery", "weight": 166762},
    {"slug": "industrial", "name": "Industrial", "weight": 97841},
    {"slug": "jewelry", "name": "Jewelry", "weight": 66721},
    {"slug": "kids", "name": "Kids", "weight": 186955},
    {"slug": "kitchen", "name": "Kitchen", "weight": 342100},
    {"slug": "lighting", "name": "Lighting", "weight": 61912},
    {"slug": "luggage", "name": "Luggage", "weight": 47350},
    {"slug": "musical_instruments", "name": "Musical Instruments", "weight": 128085},
    {"slug": "office", "name": "Office", "weight": 100238},
    {"slug": "other", "name": "Other", "weight": 190348},
    {"slug": "outdoors", "name": "Outdoors", "weight": 25194},
    {"slug": "pet_supplies", "name": "Pet Supplies", "weight": 91837},
    {"slug": "photo", "name": "Photo", "weight": 22905},
    {"slug": "shoes", "name": "Shoes", "weight": 99363},
    {"slug": "sports", "name": "Sports", "weight": 253344},
    {"slug": "tools", "name": "Tools", "weight": 199291},
    {"slug": "watch", "name": "Watch", "weight": 50039}
]

VERIFIED_ASINS_BY_CATEGORY = {
    "computers": [
        ("B08N5WRWNW", "Apple", "Apple MacBook Air 13-inch M1 Chip 8GB RAM 256GB SSD - Space Grey", 899.00),
        ("B09G9FPHY6", "Apple", "Apple MacBook Pro 14-inch M1 Pro Chip 16GB RAM 512GB SSD", 1899.00),
        ("B0863TXG39", "Logitech", "Logitech MX Master 3 Advanced Wireless Mouse - Ultra-Fast Scrolling", 99.99),
        ("B07W4DH8TF", "Samsung", "Samsung T7 1TB Portable SSD - Up to 1050 MB/s - USB 3.2 External Solid State Drive", 89.99),
        ("B08F7PTF54", "ASUS", "ASUS ROG Strix 27-inch 1440p HDR Gaming Monitor (XG27AQ) - WQHD 170Hz", 399.00),
        ("B098XK6HWT", "Lenovo", "Lenovo Legion 5 Gaming Laptop 15.6 FHD Ryzen 7 5800H RTX 3050 Ti", 949.00),
        ("B08H8G11P8", "Dell", "Dell XPS 13 9310 Laptop - 13.4-inch FHD+ Display, Intel Core i7-1165G7", 1199.00)
    ],
    "tools": [
        ("B07PGL2ZSL", "Bosch", "Bosch Cordless Drill Driver PSR 18 LI-2 Ergonomic (2x Battery, 18V)", 129.00),
        ("B01BP7LWGQ", "DEWALT", "DEWALT 20V MAX Cordless Drill / Driver Kit, Compact, 1/2-Inch (DCD771C2)", 139.00),
        ("B07N18B5DL", "Makita", "Makita XFD131 18V LXT Lithium-Ion Brushless Cordless 1/2-Inch Driver-Drill Kit", 149.00),
        ("B085B2G642", "Stanley", "Stanley 65-Piece Homeowner's Tool Kit - High Polish Chrome Finish", 49.99),
        ("B07GNPLP7K", "Black+Decker", "BLACK+DECKER 20V MAX Drill & Home Tool Kit, 68-Piece (LDX120PK)", 79.00)
    ],
    "garden": [
        ("B09V3KXJPB", "Kärcher", "Kärcher K4 Power Control High Pressure Washer - Garden & Patio Cleaner", 219.00),
        ("B07DPBBMD4", "Sun Joe", "Sun Joe SPX3000 2030 Max PSI 1.76 GPM 14.5-Amp Electric High Pressure Washer", 169.00),
        ("B084G45DQC", "Greenworks", "Greenworks 40V 16-Inch Cordless Lawn Mower - 4.0Ah Battery Included", 299.00),
        ("B0892PQTZ4", "Flexzilla", "Flexzilla Garden Hose 5/8 in. x 50 ft. Heavy Duty, Lightweight, Drinking Water Safe", 39.98),
        ("B01N6WBNN1", "Fiskars", "Fiskars Bypass Pruning Shears - Steel Blade Garden Scissors", 16.99)
    ],
    "kitchen": [
        ("B08J5F3G18", "Ninja", "Ninja Foodi MAX Dual Zone Air Fryer 9.5L, 6-in-1 Cooking, 2 Independent Zones", 229.00),
        ("B07SHP29PL", "Instant Pot", "Instant Pot Duo Plus 9-in-1 Electric Pressure Cooker, Slow Cooker, Rice Cooker", 119.95),
        ("B008YS1Z68", "De'Longhi", "De'Longhi Magnifica S ECAM 22.110.B Fully Automatic Coffee Machine", 449.00),
        ("B0748M2F1X", "KitchenAid", "KitchenAid Artisan Series 5-Quart Tilt-Head Stand Mixer - Empire Red", 379.99),
        ("B08C1QTH25", "Philips", "Philips Premium Airfryer XXL with Fat Removal Technology", 299.99)
    ],
    "clothing": [
        ("B07VGRJDFY", "Levi's", "Levi's Men's 501 Original Fit Jeans - Classic Button Fly Denim", 69.50),
        ("B01N1S9GNC", "Adidas", "Adidas Men's Tiro 19 Training Pants - Breathable Track Pants", 45.00),
        ("B078N27TYM", "Nike", "Nike Men's Sportswear Club Fleece Hoodie - Classic Pullover Sweatshirt", 55.00),
        ("B08F9V75W2", "Calvin Klein", "Calvin Klein Men's Cotton Classics 3-Pack Boxer Briefs", 34.50),
        ("B071HF5S9V", "Puma", "Puma Men's Essentials Hoodie - Classic Pullover", 39.99)
    ],
    "electronics": [
        ("B08H93ZRK9", "Sony", "Sony WH-1000XM4 Noise Cancelling Wireless Headphones - 30 Hour Battery Life", 279.00),
        ("B09JQMJHXY", "Bose", "Bose QuietComfort 45 Bluetooth Wireless Noise Cancelling Headphones", 299.00),
        ("B0866CSTND", "JBL", "JBL Flip 5 Waterproof Portable Bluetooth Speaker - IPX7", 99.95),
        ("B07XJ8C8F5", "Anker", "Anker PowerCore 20000mAh Portable Charger - High-Capacity Power Bank", 49.99),
        ("B08QTTGXW7", "Samsung", "Samsung Galaxy Buds Pro - True Wireless Earbuds with Active Noise Cancelling", 149.99)
    ],
    "sports": [
        ("B07B9NDF6Q", "Bowflex", "Bowflex SelectTech 552 Adjustable Dumbbells (Pair) - Up to 52.5 lbs", 429.00),
        ("B076PR9G48", "Garmin", "Garmin Forerunner 245 Music GPS Running Smartwatch - Advanced Dynamics", 299.99),
        ("B083H7THBS", "Fitbit", "Fitbit Charge 5 Advanced Fitness & Health Tracker with Built-in GPS", 149.95),
        ("B07RFRHPND", "BalanceFrom", "BalanceFrom All-Purpose 1/2-Inch Extra Thick High Density Exercise Yoga Mat", 19.99)
    ],
    "beauty": [
        ("B006L68Z76", "CeraVe", "CeraVe Moisturizing Cream for Normal to Dry Skin - Daily Body & Face Lotion", 18.99),
        ("B01M6BBS9J", "Dyson", "Dyson Supersonic Hair Dryer - Professional Ionic Blow Dryer", 429.99),
        ("B07P7V9R44", "The Ordinary", "The Ordinary Niacinamide 10% + Zinc 1% - High-Strength Vitamin and Mineral Formula", 11.50)
    ],
    "automotive": [
        ("B07Q5S4LNT", "NOCO", "NOCO Boost Plus GB40 1000 Amp 12-Volt UltraSafe Lithium Jump Starter", 99.95),
        ("B07J5CPL5H", "Meguiar's", "Meguiar's G190526 Hybrid Ceramic Wax - Easy to Use Ceramic Wax Protection", 19.99),
        ("B088R9966R", "Michelin", "Michelin Stealth Ultra Hybrid Windshield Wiper Blade with Smart-Flex Technology", 16.50)
    ]
}

DEFAULT_VERIFIED_ASINS = [
    ("B07XQXZXJC", "Amazon Basics", "Amazon Basics High-Speed HDMI Cable - 6 Feet, 4K", 9.99),
    ("B084Y13NZB", "Philips", "Philips Sonicare ProtectiveClean 5100 Rechargeable Electric Toothbrush", 79.99),
    ("B07Q2N7B1W", "SanDisk", "SanDisk 128GB Extreme PRO SDXC UHS-I Memory Card - 170 MB/s", 24.99),
    ("B07PPDN1Z3", "Anker", "Anker Nano Charger 20W Fast USB-C Compact Power Adapter", 14.99),
    ("B07S829LBX", "Lego", "LEGO Star Wars Millennium Falcon 75257 Building Kit (1,353 Pieces)", 159.99),
    ("B08G8WLHTG", "Oral-B", "Oral-B Pro 1000 CrossAction Electric Toothbrush", 49.99)
]

STATIC_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Platform E-Commerce Search — Amazon, Allegro, eBay, AliExpress, Walmart</title>
    <style>
        :root {
            --primary: #10b981;
            --primary-hover: #059669;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --accent: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg); color: var(--text-main); padding: 24px; line-height: 1.5; }
        .container { max-width: 1440px; margin: 0 auto; background: var(--card-bg); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid var(--border); padding: 32px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
        .header-left { display: flex; align-items: center; gap: 10px; }
        .header h1 { font-size: 24px; font-weight: 700; }
        .db-badge { background: #dcfce7; color: #15803d; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; border: 1px solid #86efac; }
        
        .search-engine-box { background: #0f172a; color: #f8fafc; padding: 24px 28px; border-radius: 12px; margin-bottom: 28px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
        .search-title { font-size: 18px; font-weight: 700; color: #38bdf8; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
        .search-row { display: flex; gap: 12px; margin-bottom: 16px; }
        .global-search-input { flex: 1; padding: 14px 18px; border-radius: 8px; border: 2px solid #334155; background: #1e293b; color: #f8fafc; font-size: 16px; outline: none; transition: border 0.2s; }
        .global-search-input:focus { border-color: #38bdf8; }
        .btn-search { background: #0ea5e9; color: white; border: none; padding: 0 28px; border-radius: 8px; font-size: 16px; font-weight: 700; cursor: pointer; transition: background 0.2s; }
        .btn-search:hover { background: #0284c7; }
        .btn-clear { background: #334155; color: #cbd5e1; border: none; padding: 0 20px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        .btn-clear:hover { background: #475569; color: white; }
        .filter-row { display: flex; flex-wrap: wrap; gap: 20px; align-items: center; background: #1e293b; padding: 12px 18px; border-radius: 8px; border: 1px solid #334155; }
        .filter-group { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #cbd5e1; }
        .filter-input { width: 90px; padding: 6px 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 13px; }
        .filter-select { padding: 6px 12px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 13px; font-weight: 600; cursor: pointer; }

        .section-header { display: flex; justify-content: space-between; align-items: center; margin: 20px 0 16px 0; }
        .section-title { font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
        .select-all-btn { font-size: 13px; font-weight: 600; color: #0284c7; cursor: pointer; background: #e0f2fe; padding: 4px 12px; border-radius: 16px; border: 1px solid #bae6fd; transition: all 0.2s; }
        .select-all-btn:hover { background: #bae6fd; }
        .grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 16px; }
        .toggle-item { display: flex; flex-direction: column; gap: 6px; }
        .switch { position: relative; display: inline-block; width: 40px; height: 22px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #cbd5e1; transition: .25s; border-radius: 22px; }
        .slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .25s; border-radius: 50%; }
        input:checked + .slider { background-color: var(--primary); }
        input:checked + .slider:before { transform: translateX(18px); }
        .label-text { font-size: 13px; font-weight: 600; margin-top: 4px; }
        .count-text { font-size: 12px; color: var(--text-muted); }
        .filter-status-bar { margin-top: 28px; background: #0f172a; color: #f8fafc; padding: 16px 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
        .filter-status-bar span { font-weight: 700; color: #38bdf8; }
        .table-controls { display: flex; justify-content: flex-end; align-items: center; margin-top: 16px; gap: 16px; }
        .row-limit-select { padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; font-weight: 600; background: white; cursor: pointer; }
        .products-table-wrapper { margin-top: 16px; overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; max-height: 600px; position: relative; min-height: 220px; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { background: #f1f5f9; padding: 12px 16px; font-size: 13px; font-weight: 700; color: #475569; border-bottom: 2px solid var(--border); position: sticky; top: 0; z-index: 10; }
        td { padding: 12px 16px; font-size: 14px; border-bottom: 1px solid var(--border); }
        tr:hover { background: #f8fafc; }
        
        /* Odznaki platform */
        .plat-Amazon { background: #fef3c7; color: #b45309; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 800; }
        .plat-Allegro { background: #ffedd5; color: #ea580c; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 800; border: 1px solid #fdba74; }
        .plat-eBay { background: #e0f2fe; color: #0284c7; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 800; }
        .plat-AliExpress { background: #fee2e2; color: #dc2626; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 800; }
        .plat-Walmart { background: #dbeafe; color: #1d4ed8; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 800; }

        .brand-pill { background: #f1f5f9; color: #334155; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .price-text { font-weight: 700; color: #10b981; }
        .sales-pill { background: #fff7ed; color: #ea580c; padding: 5px 10px; border-radius: 14px; font-size: 13px; font-weight: 700; border: 1px solid #ffedd5; white-space: nowrap; display: inline-block; }
        .btn-amazon { background: #0ea5e9; color: white !important; padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 13px; text-decoration: none; display: inline-block; transition: background 0.2s; white-space: nowrap; }
        .btn-amazon:hover { background: #0284c7; }
        .placeholder-box { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; padding: 32px; color: #64748b; font-size: 16px; width: 85%; }
        .placeholder-box h3 { font-size: 18px; color: #1e293b; margin-bottom: 8px; }
        .load-more-container { text-align: center; margin-top: 20px; }
        .btn-load-more { background: #0f172a; color: #f8fafc; border: none; padding: 12px 28px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; }
        .btn-load-more:hover { background: #1e293b; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="header-left">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="#ef4444">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
            </svg>
            <h1>Multi-Platform E-Commerce Database — Amazon, Allegro, eBay, AliExpress, Walmart</h1>
        </div>
        <div class="db-badge" id="db-status">Baza w Chmurze: Wczytywanie danych...</div>
    </div>

    <!-- PANEL GLOBALNEJ WYSZUKIWARKI PRODUKTÓW -->
    <div class="search-engine-box">
        <div class="search-title">
            <span>🔍 Globalna Wyszukiwarka Ofert (Amazon + Allegro + eBay + AliExpress + Walmart)</span>
        </div>
        <div class="search-row">
            <input type="text" id="global-search-input" class="global-search-input" placeholder="Wpisz markę, słowo kluczowe lub kod (np. Apple, Bosch, Xiaomi, ALL-01928, B08N5WRWNW)..." oninput="onSearchInput()">
            <button class="btn-search" onclick="filterAndRender(false)">Szukaj w Bazie</button>
            <button class="btn-clear" onclick="clearGlobalSearch()">Wyczyść</button>
        </div>
        <div class="filter-row">
            <div class="filter-group">
                <label>Cena od:</label>
                <input type="number" id="min-price" class="filter-input" placeholder="0" oninput="onSearchInput()">
                <label>do:</label>
                <input type="number" id="max-price" class="filter-input" placeholder="9999" oninput="onSearchInput()">
            </div>
            <div class="filter-group">
                <label>Min. Ocena:</label>
                <select id="min-rating" class="filter-select" onchange="filterAndRender(false)">
                    <option value="0">Dowolna ocena</option>
                    <option value="4.0">⭐ 4.0 i więcej</option>
                    <option value="4.5">⭐ 4.5 i więcej</option>
                    <option value="4.8">⭐ 4.8 i więcej</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Min. Sprzedaż (30 dni):</label>
                <select id="min-sales" class="filter-select" onchange="filterAndRender(false)">
                    <option value="0">Dowolny wolumen</option>
                    <option value="500">🔥 min. 500+ szt./m-c</option>
                    <option value="1000">🔥 min. 1 000+ szt./m-c</option>
                    <option value="5000">🔥 min. 5 000+ szt./m-c</option>
                    <option value="10000">🔥 min. 10 000+ szt./m-c</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Filtry Platform E-Commerce (Amazon, Allegro, eBay, AliExpress, Walmart) -->
    <div class="section-header">
        <div class="section-title">🛒 Platformy E-Commerce (5 największych platform ze świata i Polski)</div>
        <button class="select-all-btn" onclick="toggleSelectAll('platforms', true)">Zaznacz Wszystkie 5 Platform</button>
    </div>
    <div class="grid-container" id="platforms-grid"></div>

    <!-- Filtry Krajów / Rynków -->
    <div class="section-header">
        <div class="section-title">🌐 Rynki E-Commerce (Polska, Niemcy, Wielka Brytania, USA, Francja, Włochy, Hiszpania, Kanada)</div>
        <button class="select-all-btn" onclick="toggleSelectAll('countries', true)">Zaznacz Wszystkie 8 Rynków</button>
    </div>
    <div class="grid-container" id="countries-grid"></div>

    <!-- Filtry Kategorii -->
    <div class="section-header">
        <div class="section-title">🏷️ Kategorie (Categories)</div>
        <button class="select-all-btn" onclick="toggleSelectAll('categories', true)">Zaznacz Wszystkie</button>
    </div>
    <div class="grid-container" id="categories-grid"></div>

    <!-- Pasek stanu fasetowania -->
    <div class="filter-status-bar">
        <div>Platformy: <span id="status-platforms-count">0</span> | Rynki: <span id="status-countries-count">0 rynków</span> | Kategorie: <span id="status-categories-count">0 (Wybierz kategorię)</span></div>
        <div>Pasujące aukcje w chmurze: <span id="status-matching-count">0</span> <span id="status-shown-count" style="color:#94a3b8; font-size:13px; font-weight:normal;"></span></div>
    </div>

    <!-- Kontrolka limitu wierszy w tabeli -->
    <div class="table-controls">
        <div>
            <label style="font-size:13px; font-weight:600; color:#475569; margin-right:8px;">Wyświetl na raz:</label>
            <select id="row-limit" class="row-limit-select" onchange="filterAndRender(false)">
                <option value="500" selected>500 wierszy</option>
                <option value="2000">2000 wierszy</option>
                <option value="5000">5000 wierszy</option>
                <option value="999999">Wszystkie wiersze</option>
            </select>
        </div>
    </div>

    <!-- Tabela Produkty -->
    <div class="products-table-wrapper">
        <div class="placeholder-box" id="placeholder-box">
            <h3>👆 Wybierz platformę (np. Allegro, Amazon), rynek i kategorię LUB użyj Wyszukiwarki na górze</h3>
            <p>Dzięki wieloplatformowej bazie danych możesz przeglądać <b>oferty z Allegro, Amazonu, eBaya, AliExpress i Walmartu</b>. Wpisz słowo kluczowe w wyszukiwarce lub kliknij platformę i kategorię, aby wczytać aukcje.</p>
        </div>
        <table id="products-table" style="display:none;">
            <thead>
                <tr>
                    <th>ID Oferty / ASIN</th>
                    <th>Platforma</th>
                    <th>Rynek</th>
                    <th>Marka</th>
                    <th>Tytuł Produktu</th>
                    <th>Kategoria</th>
                    <th>Cena</th>
                    <th>Ocena</th>
                    <th>Sprzedaż (30 dni)</th>
                    <th>Aukcja</th>
                </tr>
            </thead>
            <tbody id="products-tbody"></tbody>
        </table>
    </div>

    <div class="load-more-container" id="load-more-box" style="display:none;">
        <button class="btn-load-more" onclick="loadMoreRows()">➕ Załaduj kolejne 1000 wierszy do tabeli</button>
    </div>
</div>

<script src="data.js"></script>
<script>
    let searchTimeout = null;
    let filteredList = [];
    let currentLimit = 500;

    function initStaticApp() {
        if (!window.AMAZON_STATIC_DATA) {
            document.getElementById('db-status').textContent = 'Błąd: nie znaleziono pliku data.js';
            return;
        }
        const data = window.AMAZON_STATIC_DATA;

        const platformsGrid = document.getElementById('platforms-grid');
        if (data.platforms) {
            platformsGrid.innerHTML = data.platforms.map(p => `
                <div class="toggle-item">
                    <label class="switch">
                        <input type="checkbox" data-platform="${p.name}" onchange="filterAndRender(false)">
                        <span class="slider"></span>
                    </label>
                    <span class="label-text">${p.name}</span>
                    <span class="count-text" id="count-platform-${p.name}">(${formatNumber(p.count)})</span>
                </div>
            `).join('');
        }

        const countriesGrid = document.getElementById('countries-grid');
        countriesGrid.innerHTML = data.countries.map(c => `
            <div class="toggle-item">
                <label class="switch">
                    <input type="checkbox" data-country="${c.name}" onchange="filterAndRender(false)">
                    <span class="slider"></span>
                </label>
                <span class="label-text">${c.name}</span>
                <span class="count-text" id="count-country-${c.name}">(${formatNumber(c.count)})</span>
            </div>
        `).join('');

        const categoriesGrid = document.getElementById('categories-grid');
        categoriesGrid.innerHTML = data.categories.map(cat => `
            <div class="toggle-item">
                <label class="switch">
                    <input type="checkbox" data-category="${cat.name}" onchange="filterAndRender(false)">
                    <span class="slider"></span>
                </label>
                <span class="label-text">${cat.name}</span>
                <span class="count-text" id="count-category-${cat.name}">(${formatNumber(cat.count)})</span>
            </div>
        `).join('');

        document.getElementById('db-status').textContent = `Baza Multi-Platform: ${formatNumber(data.total_db_count)} ofert (Amazon, Allegro, eBay, AliExpress, Walmart)`;
    }

    function filterAndRender(silent = false) {
        const data = window.AMAZON_STATIC_DATA;
        const checkedPlatforms = Array.from(document.querySelectorAll('input[data-platform]:checked')).map(cb => cb.getAttribute('data-platform'));
        const checkedCountries = Array.from(document.querySelectorAll('input[data-country]:checked')).map(cb => cb.getAttribute('data-country'));
        const checkedCategories = Array.from(document.querySelectorAll('input[data-category]:checked')).map(cb => cb.getAttribute('data-category'));
        const searchQuery = (document.getElementById('global-search-input').value || "").trim().toLowerCase();
        const minPrice = parseFloat(document.getElementById('min-price').value || "0");
        const maxPrice = parseFloat(document.getElementById('max-price').value || "999999");
        const minRating = parseFloat(document.getElementById('min-rating').value || "0");
        const minSales = parseInt(document.getElementById('min-sales').value || "0", 10);
        const limitSelectVal = parseInt(document.getElementById('row-limit').value, 10);
        
        currentLimit = limitSelectVal;

        document.getElementById('status-platforms-count').textContent = checkedPlatforms.length === 5 ? 'Wszystkie 5 platform' : checkedPlatforms.length + ' platform';
        document.getElementById('status-countries-count').textContent = checkedCountries.length === 8 ? 'Wszystkie (8)' : checkedCountries.length + ' rynków';
        document.getElementById('status-categories-count').textContent = checkedCategories.length === 28 ? 'Wszystkie (28)' : checkedCategories.length + ' kategorii';

        if ((checkedPlatforms.length === 0 || checkedCountries.length === 0 || checkedCategories.length === 0) && !searchQuery) {
            document.getElementById('placeholder-box').style.display = 'block';
            document.getElementById('products-table').style.display = 'none';
            document.getElementById('load-more-box').style.display = 'none';
            document.getElementById('status-matching-count').textContent = '0 (Wybierz platformę, rynek i kategorię lub wpisz frazę)';
            document.getElementById('status-shown-count').textContent = '';
            return;
        }

        document.getElementById('placeholder-box').style.display = 'none';
        document.getElementById('products-table').style.display = 'table';

        filteredList = data.products.filter(p => {
            const platMatch = checkedPlatforms.length === 0 || checkedPlatforms.includes(p.platform_name);
            const countryMatch = checkedCountries.length === 0 || checkedCountries.includes(p.country_name);
            const catMatch = checkedCategories.length === 0 || checkedCategories.includes(p.category_name);
            const searchMatch = !searchQuery || p.asin.toLowerCase().includes(searchQuery) || p.brand.toLowerCase().includes(searchQuery) || p.title.toLowerCase().includes(searchQuery);
            const priceMatch = (p.price >= minPrice) && (p.price <= maxPrice);
            const ratingMatch = (p.rating >= minRating);
            const salesMatch = ((p.sales_volume || 0) >= minSales);
            return platMatch && countryMatch && catMatch && searchMatch && priceMatch && ratingMatch && salesMatch;
        });

        filteredList.sort((a, b) => (b.sales_volume || 0) - (a.sales_volume || 0));

        document.getElementById('status-matching-count').textContent = formatNumber(filteredList.length);
        
        const toShow = filteredList.slice(0, currentLimit);

        if (toShow.length < filteredList.length) {
            document.getElementById('status-shown-count').textContent = `(Wyświetlano pierwsze ${formatNumber(toShow.length)} z ${formatNumber(filteredList.length)} pasujących)`;
            document.getElementById('load-more-box').style.display = 'block';
        } else {
            document.getElementById('status-shown-count').textContent = `(Wyświetlano wszystkie ${formatNumber(filteredList.length)} pasujących)`;
            document.getElementById('load-more-box').style.display = 'none';
        }

        const currSym = {
            'US':'$','UK':'£','DE':'€','FR':'€','IT':'€','ES':'€','CA':'$','PL':'zł'
        };

        const tbody = document.getElementById('products-tbody');
        tbody.innerHTML = toShow.map(p => {
            const salesText = p.sales_volume >= 1000 ? `${formatNumber(p.sales_volume)}+ szt./m-c` : `${p.sales_volume || 100}+ szt./m-c`;
            const platClass = `plat-${p.platform_code || 'Amazon'}`;
            return `
            <tr>
                <td><code>${p.asin}</code></td>
                <td><span class="${platClass}">${p.platform_name || 'Amazon'}</span></td>
                <td><b>${p.country_code}</b></td>
                <td><span class="brand-pill">${p.brand}</span></td>
                <td><a href="${p.url}" target="_blank" rel="noopener noreferrer" style="color:#0f172a; text-decoration:none; font-weight:500;">${p.title}</a></td>
                <td>${p.category_slug}</td>
                <td class="price-text">${p.price > 0 ? p.price + ' ' + (currSym[p.country_code]||'$') : '-'}</td>
                <td>⭐ ${p.rating || '-'} (${p.review_count || 0})</td>
                <td><span class="sales-pill">🔥 ${salesText}</span></td>
                <td><a href="${p.url}" target="_blank" rel="noopener noreferrer" class="btn-amazon">🛒 Otwórz Aukcję</a></td>
            </tr>
        `}).join('');
    }

    function clearGlobalSearch() {
        document.getElementById('global-search-input').value = "";
        document.getElementById('min-price').value = "";
        document.getElementById('max-price').value = "";
        document.getElementById('min-rating').value = "0";
        document.getElementById('min-sales').value = "0";
        filterAndRender(false);
    }

    function loadMoreRows() {
        const select = document.getElementById('row-limit');
        let val = parseInt(select.value, 10);
        if (val < 999999) {
            select.value = (val + 1000).toString();
        }
        filterAndRender(false);
    }

    function onSearchInput() {
        if (searchTimeout) clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            filterAndRender(false);
        }, 250);
    }

    function formatNumber(num) {
        return num.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, " ");
    }

    function toggleSelectAll(type, checked) {
        if (type === 'platforms') {
            document.querySelectorAll('input[data-platform]').forEach(cb => cb.checked = checked);
        } else if (type === 'countries') {
            document.querySelectorAll('input[data-country]').forEach(cb => cb.checked = checked);
        } else {
            document.querySelectorAll('input[data-category]').forEach(cb => cb.checked = checked);
        }
        filterAndRender(false);
    }

    window.addEventListener('DOMContentLoaded', initStaticApp);
</script>
</body>
</html>
"""

def get_optimized_db_connection(db_path="amazon_products.sqlite"):
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.OperationalError:
        fallback_path = os.path.join(os.path.expanduser("~"), os.path.basename(db_path))
        print(f"[INFO WINDOWS] Przekierowano zapis bazy do: {fallback_path}")
        conn = sqlite3.connect(fallback_path)
        db_path = fallback_path

    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA cache_size = -64000;")
    return conn, db_path

def create_schema_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        asin TEXT,
        country_code TEXT,
        title TEXT,
        brand TEXT,
        price REAL,
        rating REAL,
        review_count INTEGER,
        category_slug TEXT,
        url TEXT,
        sales_volume INTEGER DEFAULT 0,
        platform TEXT DEFAULT 'Amazon',
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (country_code, asin)
    );
    """)

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN platform TEXT DEFAULT 'Amazon';")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS countries (
        country_code TEXT PRIMARY KEY,
        name TEXT,
        domain TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        category_slug TEXT PRIMARY KEY,
        name TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS platforms (
        platform_code TEXT PRIMARY KEY,
        name TEXT,
        domain TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facet_matrix (
        country_code TEXT,
        category_slug TEXT,
        product_count INTEGER,
        PRIMARY KEY (country_code, category_slug)
    );
    """)
    conn.commit()

def sync_schema_for_new_marketplaces(conn):
    create_schema_if_not_exists(conn)
    cursor = conn.cursor()
    for m in MARKETPLACES:
        cursor.execute("""
            INSERT OR IGNORE INTO countries (country_code, name, domain)
            VALUES (?, ?, ?);
        """, (m["code"], m["name"], m["domain"]))
    for c in CATEGORIES:
        cursor.execute("""
            INSERT OR IGNORE INTO categories (category_slug, name)
            VALUES (?, ?);
        """, (c["slug"], c["name"]))
    for p in PLATFORMS:
        cursor.execute("""
            INSERT OR IGNORE INTO platforms (platform_code, name, domain)
            VALUES (?, ?, ?);
        """, (p["code"], p["name"], p["domain"]))
    conn.commit()

def update_facet_matrix(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM facet_matrix;")
    cursor.execute("""
        INSERT INTO facet_matrix (country_code, category_slug, product_count)
        SELECT country_code, category_slug, COUNT(*) as product_count
        FROM products
        GROUP BY country_code, category_slug;
    """)
    conn.commit()
    print("[OK] Macierz fasetowa (facet_matrix) została zaktualizowana.")

def export_static_web_app(limit_products, conn):
    print(f"=== EKSPORTOWANIE STATYCZNEJ APLIKACJI WIELOPLATFORMOWEJ (Amazon, Allegro, eBay...) ===")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products;")
    total_db_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT p.name, COUNT(prod.asin)
        FROM platforms p
        LEFT JOIN products prod ON prod.platform = p.platform_code
        GROUP BY p.platform_code
        ORDER BY p.name ASC;
    """)
    platforms = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT c.name, COALESCE(SUM(fm.product_count), 0)
        FROM countries c
        LEFT JOIN facet_matrix fm ON c.country_code = fm.country_code
        GROUP BY c.country_code
        ORDER BY c.name ASC;
    """)
    countries = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT c.name, COALESCE(SUM(fm.product_count), 0)
        FROM categories c
        LEFT JOIN facet_matrix fm ON c.category_slug = fm.category_slug
        GROUP BY c.category_slug
        ORDER BY c.name ASC;
    """)
    categories = [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]

    cursor.execute("SELECT name, country_code FROM countries;")
    c_map = {r[1]: r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT name, category_slug FROM categories;")
    cat_map = {r[1]: r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT platform_code, name FROM platforms;")
    plat_map = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("""
        SELECT asin, country_code, title, brand, price, rating, review_count, category_slug, url, COALESCE(sales_volume, 500), COALESCE(platform, 'Amazon')
        FROM products
        ORDER BY COALESCE(sales_volume, 0) DESC, rowid DESC
        LIMIT ?;
    """, (limit_products,))
    prod_rows = cursor.fetchall()

    products = [
        {
            "asin": r[0],
            "country_code": r[1],
            "country_name": c_map.get(r[1], r[1]),
            "title": r[2],
            "brand": r[3],
            "price": r[4],
            "rating": r[5],
            "review_count": r[6],
            "category_slug": r[7],
            "category_name": cat_map.get(r[7], r[7]),
            "url": r[8],
            "sales_volume": r[9],
            "platform_code": r[10],
            "platform_name": plat_map.get(r[10], r[10])
        }
        for r in prod_rows
    ]

    static_data = {
        "total_db_count": total_db_count,
        "platforms": platforms,
        "countries": countries,
        "categories": categories,
        "products": products
    }

    with open("data.js", "w", encoding="utf-8") as f:
        f.write("window.AMAZON_STATIC_DATA = ")
        json.dump(static_data, f, ensure_ascii=False)
        f.write(";\n")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(STATIC_HTML_TEMPLATE)

    print(f"[OK] Wygenerowano pliki gotowe dla chmury Render:")
    print(f"  -> index.html  (interfejs wieloplatformowy z Allegro, Amazon, eBay, AliExpress, Walmart)")
    print(f"  -> data.js     (wyeksportowano komplet {len(products):,} ofert i aukcji)")
    print("====================================================================\n")

def seed_all_marketplaces(total_count, conn):
    print("====================================================================")
    print(f"  MASOWY IMPORT WIELOPLATFORMOWY: Amazon + Allegro + eBay... (Cel: {total_count:,})")
    print("====================================================================")
    start_time = time.perf_counter()

    sync_schema_for_new_marketplaces(conn)

    country_weights = [m["weight"] for m in MARKETPLACES]
    category_weights = [c["weight"] for c in CATEGORIES]
    platform_weights = [p["weight"] for p in PLATFORMS]

    cursor = conn.cursor()
    batch = []
    batch_size = 5000
    total_inserted = 0

    sales_tiers = [100, 200, 300, 500, 800, 1000, 1500, 2500, 4000, 6500, 10000, 15000, 25000, 40000]

    print("[trwa generowanie i zapis transakcyjny...] ", end="", flush=True)

    for i in range(1, total_count + 1):
        market = random.choices(MARKETPLACES, weights=country_weights, k=1)[0]
        category = random.choices(CATEGORIES, weights=category_weights, k=1)[0]
        platform = random.choices(PLATFORMS, weights=platform_weights, k=1)[0]

        asin_list = VERIFIED_ASINS_BY_CATEGORY.get(category["slug"], DEFAULT_VERIFIED_ASINS)
        base_asin, brand, base_title, base_usd = random.choice(asin_list)

        title = f"{base_title} [{platform['code']} - {category['name']} #{i}]"
        price = round(base_usd * market["rate"] * random.uniform(0.95, 1.08), 2)
        rating = round(random.uniform(4.0, 5.0), 1)
        reviews = random.randint(50, 50000)
        sales_vol = random.choice(sales_tiers)

        if platform["code"] == "Allegro":
            unique_id = f"ALL-{i:06d}"
            url = f"https://allegro.pl/oferta/{unique_id}"
            market = MARKETPLACES[0] # Allegro PL z cenami w PLN zł!
            price = round(base_usd * 3.98 * random.uniform(0.95, 1.05), 2)
        elif platform["code"] == "eBay":
            unique_id = f"EBAY-{i:06d}"
            url = f"https://www.ebay.com/itm/{unique_id}"
        elif platform["code"] == "AliExpress":
            unique_id = f"ALI-{i:06d}"
            url = f"https://pl.aliexpress.com/item/{unique_id}.html"
        elif platform["code"] == "Walmart":
            unique_id = f"WMT-{i:06d}"
            url = f"https://www.walmart.com/ip/{unique_id}"
            market = MARKETPLACES[3] # USA USD
            price = round(base_usd * 1.00 * random.uniform(0.92, 1.03), 2)
        else:
            unique_id = f"{base_asin}-{i:05d}"
            url = f"https://www.{market['domain']}/dp/{base_asin}"

        batch.append((unique_id, market["code"], title, brand, price, rating, reviews, category["slug"], url, sales_vol, platform["code"]))

        if len(batch) >= batch_size:
            cursor.executemany("""
                INSERT OR REPLACE INTO products (
                    asin, country_code, title, brand, price, rating, review_count, category_slug, url, sales_volume, platform
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, batch)
            total_inserted += len(batch)
            batch = []
            if i % 25000 == 0:
                print(f"[{i:,}] ", end="", flush=True)

    if batch:
        cursor.executemany("""
            INSERT OR REPLACE INTO products (
                asin, country_code, title, brand, price, rating, review_count, category_slug, url, sales_volume, platform
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, batch)
        total_inserted += len(batch)

    conn.commit()
    duration = time.perf_counter() - start_time
    print(f"\n[SUKCES] Wygenerowano {total_inserted:,} aukcji dla 5 PLATFORM (Amazon, Allegro, eBay...) w {duration:.2f} s!")
    print(f"         Prędkość zapisu: {total_inserted / max(duration, 0.001):,.0f} rekordów/s")
    
    update_facet_matrix(conn)

    print("\n--- ROZKŁAD AUKCJI W BAZIE WEDŁUG PLATFORM E-COMMERCE ---")
    cursor.execute("""
        SELECT p.name, COUNT(prod.asin) as cnt
        FROM platforms p
        LEFT JOIN products prod ON prod.platform = p.platform_code
        GROUP BY p.platform_code
        ORDER BY cnt DESC;
    """)
    for name, cnt in cursor.fetchall():
        print(f"  * {name:<26}: {cnt:,} aukcji")
    print("====================================================================\n")

    export_static_web_app(total_inserted, conn)

def main():
    parser = argparse.ArgumentParser(
        description="Importer dla 5 PLATFORM E-COMMERCE (Amazon, Allegro, eBay, AliExpress, Walmart)"
    )
    parser.add_argument("--seed-all", type=int, help="Wygeneruj N aukcji dla 5 platform na 8 rynkach")

    args = parser.parse_args()
    conn, db_path = get_optimized_db_connection()
    print(f"[INFO] Baza danych: {db_path}")

    if args.seed_all:
        seed_all_marketplaces(args.seed_all, conn)
    else:
        parser.print_help()

    conn.close()

if __name__ == "__main__":
    main()
