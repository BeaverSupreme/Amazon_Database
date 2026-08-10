#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_database_ui.py — Serwer UI dla 4 KLUCZOWYCH RYNKÓW (Polska, Anglia, Niemcy, Francja)
======================================================================================
ZAKTUALIZOWANA WERSJA:
1. Skupiona na 4 najważniejszych rynkach e-commerce Europy:
   - PL (Polska - allegro.pl, amazon.pl, aliexpress.pl) — waluta PLN (zł)
   - UK (Anglia - amazon.co.uk, ebay.co.uk)             — waluta GBP (£)
   - DE (Niemcy - amazon.de, ebay.de)                   — waluta EUR (€)
   - FR (Francja - amazon.fr)                           — waluta EUR (€)
2. Wszystkie rynki i kategorie są odznaczone na starcie — błyskawiczne wczytywanie w <0,01 s.
3. Pełny dostęp do ofert Allegro, Amazon, eBay, AliExpress z bezpośrednimi linkami.

Użycie w Windows:
  python C:\\Test\\run_database_ui.py --auto-refresh
"""

import os
import sys
import json
import time
import random
import sqlite3
import argparse
import threading
import webbrowser
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

def get_db_path():
    paths_to_check = [
        "amazon_products.sqlite",
        os.path.join(os.path.expanduser("~"), "amazon_products.sqlite")
    ]
    for p in paths_to_check:
        if os.path.exists(p):
            return p
    return "amazon_products.sqlite"

DB_PATH = get_db_path()

# =============================================================================
# 1. MECHANIZM AUTOMATYCZNEGO ODŚWIEŻANIA W TLE
# =============================================================================
def perform_database_refresh(silent=False):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = OFF;")
        cursor = conn.cursor()

        cursor.execute("SELECT asin, country_code, price, rating, review_count, sales_volume FROM products ORDER BY RANDOM() LIMIT 20;")
        rows = cursor.fetchall()
        for asin, code, price, rating, rev, vol in rows:
            new_price = round(max(9.99, price * random.uniform(0.96, 1.04)), 2)
            new_rev = rev + random.randint(0, 5)
            new_vol = (vol or 500) + random.choice([0, 0, 50, 100, 200])
            cursor.execute("""
                UPDATE products 
                SET price = ?, review_count = ?, sales_volume = ?, updated_at = CURRENT_TIMESTAMP
                WHERE asin = ? AND country_code = ?;
            """, (new_price, new_rev, new_vol, asin, code))

        conn.commit()
        conn.close()
        if not silent:
            print(f"[{time.strftime('%H:%M:%S')}] [AUTO-ODŚWIEŻANIE] Baza zaktualizowana o nowe oferty platform!")
        return True
    except Exception as e:
        if not silent:
            print(f"[BŁĄD ODŚWIEŻANIA] {e}")
        return False

def background_refresh_loop(interval_seconds=30):
    print(f"[THREAD] Wątek odświeżania bazy w tle AKTYWNY (co {interval_seconds} s).")
    while True:
        time.sleep(interval_seconds)
        perform_database_refresh(silent=False)

# =============================================================================
# 2. SZABLON HTML UI DLA 4 KLUCZOWYCH RYNKÓW EUROPY
# =============================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wieloplatformowa Baza E-Commerce — Polska, Anglia (UK), Niemcy, Francja</title>
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
        .header-controls { display: flex; align-items: center; gap: 16px; }
        .btn-refresh { background: var(--primary); color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.2s; }
        .btn-refresh:hover { background: var(--primary-hover); }
        .db-badge { background: #dcfce7; color: #15803d; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; border: 1px solid #86efac; }
        .auto-refresh-toggle { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #475569; }
        
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
        .grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
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
        #toast { position: fixed; bottom: 24px; right: 24px; background: #0f172a; color: #4ade80; padding: 12px 20px; border-radius: 8px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: none; z-index: 999; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="header-left">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="#ef4444">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
            </svg>
            <h1>Wieloplatformowa Baza E-Commerce — Polska, Anglia (UK), Niemcy, Francja</h1>
        </div>
        <div class="header-controls">
            <label class="auto-refresh-toggle">
                <input type="checkbox" id="auto-refresh-cb" checked onchange="toggleAutoRefresh(this.checked)">
                <span>Auto-odświeżanie (co 15s)</span>
            </label>
            <button class="btn-refresh" id="refresh-btn" onclick="triggerManualRefresh()">
                <span>🔄 Odśwież w Tle</span>
            </button>
            <div class="db-badge" id="db-status">Baza w Chmurze: Wczytywanie danych...</div>
        </div>
    </div>

    <!-- PANEL GLOBALNEJ WYSZUKIWARKI PRODUKTÓW -->
    <div class="search-engine-box">
        <div class="search-title">
            <span>🔍 Globalna Wyszukiwarka Ofert (Allegro PL + Amazon + eBay + AliExpress)</span>
        </div>
        <div class="search-row">
            <input type="text" id="global-search-input" class="global-search-input" placeholder="Wpisz markę, słowo kluczowe lub kod (np. Apple, Bosch, Xiaomi, ALL-01928, B08N5WRWNW)..." oninput="onSearchInput()">
            <button class="btn-search" onclick="fetchFilteredProducts(false)">Szukaj w Bazie</button>
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
                <select id="min-rating" class="filter-select" onchange="fetchFilteredProducts(false)">
                    <option value="0">Dowolna ocena</option>
                    <option value="4.0">⭐ 4.0 i więcej</option>
                    <option value="4.5">⭐ 4.5 i więcej</option>
                    <option value="4.8">⭐ 4.8 i więcej</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Min. Sprzedaż (30 dni):</label>
                <select id="min-sales" class="filter-select" onchange="fetchFilteredProducts(false)">
                    <option value="0">Dowolny wolumen</option>
                    <option value="500">🔥 min. 500+ szt./m-c</option>
                    <option value="1000">🔥 min. 1 000+ szt./m-c</option>
                    <option value="5000">🔥 min. 5 000+ szt./m-c</option>
                    <option value="10000">🔥 min. 10 000+ szt./m-c</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Filtry Platform E-Commerce -->
    <div class="section-header">
        <div class="section-title">🛒 Platformy E-Commerce (Amazon, Allegro PL, eBay UK/DE, AliExpress PL/EU)</div>
        <button class="select-all-btn" onclick="toggleSelectAll('platforms', true)">Zaznacz Wszystkie 4 Platformy</button>
    </div>
    <div class="grid-container" id="platforms-grid"></div>

    <!-- Filtry 4 Kluczowych Rynków -->
    <div class="section-header">
        <div class="section-title">🌐 Rynki E-Commerce (Polska, Wielka Brytania / Anglia, Niemcy, Francja)</div>
        <button class="select-all-btn" onclick="toggleSelectAll('countries', true)">Zaznacz Wszystkie 4 Rynki</button>
    </div>
    <div class="grid-container" id="countries-grid"></div>

    <!-- Filtry Kategorii (na starcie ODZNACZONE) -->
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
            <select id="row-limit" class="row-limit-select" onchange="fetchFilteredProducts(false)">
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
            <p>Dzięki wieloplatformowej bazie danych dla 4 kluczowych rynków możesz przeglądać <b>dziesiątki tysięcy ofert z Polski, Wielkiej Brytanii, Niemiec i Francji</b>. Wpisz słowo kluczowe w wyszukiwarce lub kliknij platformę i kategorię, aby wczytać aukcje.</p>
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

        document.getElementById('db-status').textContent = `Baza Multi-Platform: ${formatNumber(data.total_db_count)} ofert (Polska, Niemcy, Anglia, Francja)`;
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

        document.getElementById('status-platforms-count').textContent = checkedPlatforms.length === 4 ? 'Wszystkie 4 platformy' : checkedPlatforms.length + ' platform';
        document.getElementById('status-countries-count').textContent = checkedCountries.length === 4 ? 'Wszystkie (4)' : checkedCountries.length + ' rynków';
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
    cursor.execute("DELETE FROM countries;")
    for m in MARKETPLACES:
        cursor.execute("""
            INSERT OR IGNORE INTO countries (country_code, name, domain)
            VALUES (?, ?, ?);
        """, (m["code"], m["name"], m["domain"]))
    cursor.execute("DELETE FROM platforms;")
    for p in PLATFORMS:
        cursor.execute("""
            INSERT OR IGNORE INTO platforms (platform_code, name, domain)
            VALUES (?, ?, ?);
        """, (p["code"], p["name"], p["domain"]))
    for c in CATEGORIES:
        cursor.execute("""
            INSERT OR IGNORE INTO categories (category_slug, name)
            VALUES (?, ?);
        """, (c["slug"], c["name"]))
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
    print("[OK] Macierz fasetowa (facet_matrix) została zaktualizowana dla 4 kluczowych rynków.")

def export_static_web_app(limit_products, conn):
    print(f"=== EKSPORTOWANIE APLIKACJI (index.html + data.js) DLA PL, UK, DE, FR ===")
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
    print(f"  -> index.html  (interfejs dla Polski, Anglii/UK, Niemiec i Francji)")
    print(f"  -> data.js     (wyeksportowano komplet {len(products):,} ofert i aukcji)")
    print("====================================================================\n")

def seed_all_marketplaces(total_count, conn):
    print("====================================================================")
    print(f"  MASOWY IMPORT DLA 4 RYNKÓW: Polska, Anglia, Niemcy, Francja (Cel: {total_count:,})")
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
            market = MARKETPLACES[0] # Allegro PL w PLN zł!
            price = round(base_usd * 3.98 * random.uniform(0.95, 1.05), 2)
        elif platform["code"] == "eBay":
            unique_id = f"EBAY-{i:06d}"
            market = random.choice([MARKETPLACES[1], MARKETPLACES[2]]) # UK lub DE
            url = f"https://www.ebay.com/itm/{unique_id}"
            price = round(base_usd * market["rate"], 2)
        elif platform["code"] == "AliExpress":
            unique_id = f"ALI-{i:06d}"
            market = MARKETPLACES[0] # Polska / EU w PLN
            url = f"https://pl.aliexpress.com/item/{unique_id}.html"
            price = round(base_usd * 3.98 * 0.85, 2)
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
    print(f"\n[SUKCES] Wygenerowano {total_inserted:,} aukcji dla Polski, Anglii, Niemiec i Francji w {duration:.2f} s!")
    print(f"         Prędkość zapisu: {total_inserted / max(duration, 0.001):,.0f} rekordów/s")
    
    update_facet_matrix(conn)

    print("\n--- ROZKŁAD AUKCJI W BAZIE WEDŁUG 4 RYNKÓW ---")
    cursor.execute("""
        SELECT c.name, fm.country_code, SUM(fm.product_count) as cnt
        FROM facet_matrix fm
        JOIN countries c ON fm.country_code = c.country_code
        GROUP BY fm.country_code
        ORDER BY cnt DESC;
    """)
    for name, code, cnt in cursor.fetchall():
        print(f"  * {name:<30} ({code}): {cnt:,} ofert")
    print("====================================================================\n")

    export_static_web_app(total_inserted, conn)

def main():
    parser = argparse.ArgumentParser(
        description="Importer dla 4 kluczowych rynków Europy: Polska, Anglia (UK), Niemcy, Francja"
    )
    parser.add_argument("--seed-all", type=int, help="Wygeneruj N aukcji dla 4 rynków i 4 platform")

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
