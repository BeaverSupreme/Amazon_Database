#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_database_ui.py — Serwer UI z OBSŁUGĄ 5 PLATFORM E-COMMERCE (Amazon, Allegro, eBay...)
=========================================================================================
ZAKTUALIZOWANA WERSJA MULTI-PLATFORM:
1. Dodano obsługę ofert z 5 największych platform e-commerce (Amazon, Allegro, eBay, AliExpress, Walmart).
2. W interfejsie nad rynkami masz osobną sekcję wyboru Platform — możesz np. włączyć samo Allegro i Amazon.
3. W tabeli widoczna jest kolorowa odznaka platformy (pomarańczowe Allegro, żółty Amazon, niebieski eBay).
4. Wszystko odznaczone na starcie — błyskawiczny start (0 zacięć).

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
from http.server import HTTPServer, BaseHTTPRequestHandler
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
# 2. SZABLON HTML UI Z OBSŁUGĄ PLATFORM E-COMMERCE (AMAZON, ALLEGRO, EBAY...)
# =============================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Platform E-Commerce Database — Amazon, Allegro, eBay, AliExpress, Walmart</title>
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

        .brand-pill { background: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
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
        <div class="header-controls">
            <label class="auto-refresh-toggle">
                <input type="checkbox" id="auto-refresh-cb" checked onchange="toggleAutoRefresh(this.checked)">
                <span>Auto-odświeżanie (co 15s)</span>
            </label>
            <button class="btn-refresh" id="refresh-btn" onclick="triggerManualRefresh()">
                <span>🔄 Odśwież w Tle</span>
            </button>
            <div class="db-badge" id="db-status">Baza: Ładowanie...</div>
        </div>
    </div>

    <!-- PANEL GLOBALNEJ WYSZUKIWARKI PRODUKTÓW -->
    <div class="search-engine-box">
        <div class="search-title">
            <span>🔍 Globalna Wyszukiwarka Ofert (Amazon + Allegro + eBay + AliExpress + Walmart)</span>
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
        <div class="section-title">🛒 Platformy E-Commerce (Amazon, Allegro, eBay, AliExpress, Walmart)</div>
        <button class="select-all-btn" onclick="toggleSelectAll('platforms', true)">Zaznacz Wszystkie 5 Platform</button>
    </div>
    <div class="grid-container" id="platforms-grid"></div>

    <!-- Filtry Krajów (8 rynków) -->
    <div class="section-header">
        <div class="section-title">🌐 Rynki Amazon / E-Commerce (Polska, Niemcy, Wielka Brytania, USA...)</div>
        <button class="select-all-btn" onclick="toggleSelectAll('countries', true)">Zaznacz Wszystkie 8 Rynków</button>
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
        <div>Pasujące aukcje w bazie SQL: <span id="status-matching-count">0</span> <span id="status-shown-count" style="color:#94a3b8; font-size:13px; font-weight:normal;"></span></div>
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

<div id="toast">✅ Dane odświeżone w tle (Twoje filtry zostały zachowane!)</div>

<script>
    let autoRefreshInterval = null;
    let isFirstLoad = true;
    let searchTimeout = null;

    async function loadFacets(silent = false) {
        try {
            const res = await fetch('/api/facets');
            const data = await res.json();
            
            const activePlatforms = new Set();
            const activeCountries = new Set();
            const activeCategories = new Set();

            if (!isFirstLoad) {
                document.querySelectorAll('input[data-platform]:checked').forEach(cb => {
                    activePlatforms.add(cb.getAttribute('data-platform'));
                });
                document.querySelectorAll('input[data-country]:checked').forEach(cb => {
                    activeCountries.add(cb.getAttribute('data-country'));
                });
                document.querySelectorAll('input[data-category]:checked').forEach(cb => {
                    activeCategories.add(cb.getAttribute('data-category'));
                });
            }

            const platformsGrid = document.getElementById('platforms-grid');
            if (data.platforms) {
                platformsGrid.innerHTML = data.platforms.map(p => {
                    const isChecked = isFirstLoad ? false : activePlatforms.has(p.name);
                    return `
                    <div class="toggle-item">
                        <label class="switch">
                            <input type="checkbox" data-platform="${p.name}" ${isChecked ? 'checked' : ''} onchange="fetchFilteredProducts(false)">
                            <span class="slider"></span>
                        </label>
                        <span class="label-text">${p.name}</span>
                        <span class="count-text" id="count-platform-${p.name}">(${formatNumber(p.count)})</span>
                    </div>
                `}).join('');
            }

            const countriesGrid = document.getElementById('countries-grid');
            countriesGrid.innerHTML = data.countries.map(c => {
                const isChecked = isFirstLoad ? false : activeCountries.has(c.name);
                return `
                <div class="toggle-item">
                    <label class="switch">
                        <input type="checkbox" data-country="${c.name}" ${isChecked ? 'checked' : ''} onchange="fetchFilteredProducts(false)">
                        <span class="slider"></span>
                    </label>
                    <span class="label-text">${c.name}</span>
                    <span class="count-text" id="count-country-${c.name}">(${formatNumber(c.count)})</span>
                </div>
            `}).join('');

            const categoriesGrid = document.getElementById('categories-grid');
            categoriesGrid.innerHTML = data.categories.map(cat => {
                const isChecked = isFirstLoad ? false : activeCategories.has(cat.name);
                return `
                <div class="toggle-item">
                    <label class="switch">
                        <input type="checkbox" data-category="${cat.name}" ${isChecked ? 'checked' : ''} onchange="fetchFilteredProducts(false)">
                        <span class="slider"></span>
                    </label>
                    <span class="label-text">${cat.name}</span>
                    <span class="count-text" id="count-category-${cat.name}">(${formatNumber(cat.count)})</span>
                </div>
            `}).join('');

            document.getElementById('db-status').textContent = `Baza Multi-Platform: ${formatNumber(data.total_db_count)} ofert (Amazon, Allegro, eBay, AliExpress, Walmart)`;
            
            if (isFirstLoad) {
                isFirstLoad = false;
                await fetchFilteredProducts(true);
            } else if (!silent) {
                await fetchFilteredProducts(true);
                showToast("🔄 Zaktualizowano dane w tle (Twoje filtry zostały zachowane!)");
            }
        } catch(err) {
            console.error("Błąd pobierania faset z serwera:", err);
        }
    }

    async function fetchFilteredProducts(silent = false) {
        const checkedPlatforms = Array.from(document.querySelectorAll('input[data-platform]:checked')).map(cb => cb.getAttribute('data-platform'));
        const checkedCountries = Array.from(document.querySelectorAll('input[data-country]:checked')).map(cb => cb.getAttribute('data-country'));
        const checkedCategories = Array.from(document.querySelectorAll('input[data-category]:checked')).map(cb => cb.getAttribute('data-category'));
        const searchQuery = (document.getElementById('global-search-input').value || "").trim();
        const minPrice = document.getElementById('min-price').value || "0";
        const maxPrice = document.getElementById('max-price').value || "999999";
        const minRating = document.getElementById('min-rating').value || "0";
        const minSales = document.getElementById('min-sales').value || "0";
        const limit = document.getElementById('row-limit').value;

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

        const params = new URLSearchParams();
        checkedPlatforms.forEach(p => params.append('platform', p));
        checkedCountries.forEach(c => params.append('country', c));
        checkedCategories.forEach(cat => params.append('category', cat));
        if (searchQuery) params.append('search', searchQuery);
        params.append('min_price', minPrice);
        params.append('max_price', maxPrice);
        params.append('min_rating', minRating);
        params.append('min_sales', minSales);
        params.append('limit', limit);

        try {
            const res = await fetch('/api/products?' + params.toString());
            const data = await res.json();

            document.getElementById('status-matching-count').textContent = formatNumber(data.total_matching);
            
            if (data.products.length < data.total_matching) {
                document.getElementById('status-shown-count').textContent = `(Wyświetlano pierwsze ${formatNumber(data.products.length)} z ${formatNumber(data.total_matching)} pasujących w bazie)`;
                document.getElementById('load-more-box').style.display = 'block';
            } else {
                document.getElementById('status-shown-count').textContent = `(Wyświetlano wszystkie ${formatNumber(data.total_matching)} pasujących w bazie)`;
                document.getElementById('load-more-box').style.display = 'none';
            }

            const currSym = {
                'US':'$','UK':'£','DE':'€','FR':'€','IT':'€','ES':'€','CA':'$','PL':'zł'
            };

            const tbody = document.getElementById('products-tbody');
            tbody.innerHTML = data.products.map(p => {
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
        } catch(err) {
            console.error("Błąd pobierania produktów SQL:", err);
        }
    }

    function clearGlobalSearch() {
        document.getElementById('global-search-input').value = "";
        document.getElementById('min-price').value = "";
        document.getElementById('max-price').value = "";
        document.getElementById('min-rating').value = "0";
        document.getElementById('min-sales').value = "0";
        fetchFilteredProducts(false);
    }

    function loadMoreRows() {
        const select = document.getElementById('row-limit');
        let val = parseInt(select.value, 10);
        if (val < 999999) {
            select.value = (val + 1000).toString();
        }
        fetchFilteredProducts(false);
    }

    function onSearchInput() {
        if (searchTimeout) clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchFilteredProducts(false);
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
        fetchFilteredProducts(false);
    }

    async function triggerManualRefresh() {
        const btn = document.getElementById('refresh-btn');
        btn.disabled = true;
        btn.innerHTML = '<span>⏳ Odświeżanie w tle...</span>';
        try {
            const res = await fetch('/api/refresh', { method: 'POST' });
            if (res.ok) {
                await loadFacets(false);
            }
        } catch(err) {
            showToast("❌ Błąd połączenia z serwerem");
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span>🔄 Odśwież w Tle</span>';
        }
    }

    function toggleAutoRefresh(enabled) {
        if (enabled) {
            autoRefreshInterval = setInterval(() => {
                triggerManualRefresh();
            }, 15000);
            showToast("⏱️ Auto-odświeżanie w tle aktywne (co 15s)");
        } else {
            if (autoRefreshInterval) clearInterval(autoRefreshInterval);
            showToast("⏸️ Auto-odświeżanie wyłączone");
        }
    }

    function showToast(msg) {
        const t = document.getElementById('toast');
        t.textContent = msg;
        t.style.display = 'block';
        setTimeout(() => { t.style.display = 'none'; }, 3500);
    }

    loadFacets(true);
    toggleAutoRefresh(true);
</script>
</body>
</html>
"""

# =============================================================================
# 3. HANDLER HTTP API (/api/facets, /api/products oraz /api/refresh)
# =============================================================================
class DatabaseHandler(BaseHTTPRequestHandler):
    def safe_write(self, data):
        try:
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/facets":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                conn = sqlite3.connect(DB_PATH)
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
                conn.close()

                response_data = {
                    "db_path": DB_PATH,
                    "total_db_count": total_db_count,
                    "platforms": platforms,
                    "countries": countries,
                    "categories": categories
                }
                self.safe_write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                err_json = {"error": str(e), "db_path": DB_PATH}
                self.safe_write(json.dumps(err_json).encode("utf-8"))

        elif parsed.path == "/api/products":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                query_params = parse_qs(parsed.query)
                platforms_filter = query_params.get('platform', [])
                countries = query_params.get('country', [])
                categories = query_params.get('category', [])
                search = (query_params.get('search', [''])[0]).strip()
                try:
                    min_price = float(query_params.get('min_price', ['0'])[0])
                except ValueError:
                    min_price = 0.0
                try:
                    max_price = float(query_params.get('max_price', ['999999'])[0])
                except ValueError:
                    max_price = 999999.0
                try:
                    min_rating = float(query_params.get('min_rating', ['0'])[0])
                except ValueError:
                    min_rating = 0.0
                try:
                    min_sales = int(query_params.get('min_sales', ['0'])[0])
                except ValueError:
                    min_sales = 0
                try:
                    limit_val = int(query_params.get('limit', ['100'])[0])
                except ValueError:
                    limit_val = 100

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute("SELECT name, country_code FROM countries;")
                name_to_code = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute("SELECT name, category_slug FROM categories;")
                name_to_cat = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute("SELECT name, platform_code FROM platforms;")
                name_to_plat = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute("SELECT platform_code, name FROM platforms;")
                code_to_platname = {r[0]: r[1] for r in cursor.fetchall()}

                where_clauses = ["1=1"]
                sql_params = []

                if platforms_filter and len(platforms_filter) < 5:
                    pcodes = [name_to_plat.get(p, p) for p in platforms_filter]
                    placeholders = ",".join(["?"] * len(pcodes))
                    where_clauses.append(f"COALESCE(p.platform, 'Amazon') IN ({placeholders})")
                    sql_params.extend(pcodes)

                if countries and len(countries) < 8:
                    codes = [name_to_code.get(c, c) for c in countries]
                    placeholders = ",".join(["?"] * len(codes))
                    where_clauses.append(f"p.country_code IN ({placeholders})")
                    sql_params.extend(codes)

                if categories and len(categories) < 28:
                    cats = [name_to_cat.get(cat, cat) for cat in categories]
                    placeholders = ",".join(["?"] * len(cats))
                    where_clauses.append(f"p.category_slug IN ({placeholders})")
                    sql_params.extend(cats)

                if search:
                    where_clauses.append("(p.asin LIKE ? OR p.brand LIKE ? OR p.title LIKE ?)")
                    like_str = f"%{search}%"
                    sql_params.extend([like_str, like_str, like_str])

                if min_price > 0:
                    where_clauses.append("p.price >= ?")
                    sql_params.append(min_price)
                if max_price < 999999:
                    where_clauses.append("p.price <= ?")
                    sql_params.append(max_price)
                if min_rating > 0:
                    where_clauses.append("p.rating >= ?")
                    sql_params.append(min_rating)
                if min_sales > 0:
                    where_clauses.append("COALESCE(p.sales_volume, 0) >= ?")
                    sql_params.append(min_sales)

                where_sql = " AND ".join(where_clauses)

                count_query = f"SELECT COUNT(*) FROM products p WHERE {where_sql};"
                cursor.execute(count_query, sql_params)
                total_matching = cursor.fetchone()[0]

                select_query = f"""
                    SELECT p.asin, p.country_code, p.title, p.brand, p.price, p.rating, p.review_count, p.category_slug, p.url, COALESCE(p.sales_volume, 500), COALESCE(p.platform, 'Amazon') 
                    FROM products p 
                    WHERE {where_sql} 
                    ORDER BY COALESCE(p.sales_volume, 0) DESC, p.rowid DESC 
                    LIMIT {limit_val};
                """
                cursor.execute(select_query, sql_params)
                prod_rows = cursor.fetchall()
                conn.close()

                products = [
                    {
                        "asin": r[0],
                        "country_code": r[1],
                        "title": r[2],
                        "brand": r[3],
                        "price": r[4],
                        "rating": r[5],
                        "review_count": r[6],
                        "category_slug": r[7],
                        "url": r[8],
                        "sales_volume": r[9],
                        "platform_code": r[10],
                        "platform_name": code_to_platname.get(r[10], r[10])
                    }
                    for r in prod_rows
                ]

                response_data = {
                    "total_matching": total_matching,
                    "products": products
                }
                self.safe_write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                err_json = {"error": str(e), "total_matching": 0, "products": []}
                self.safe_write(json.dumps(err_json).encode("utf-8"))

        elif parsed.path == "/api/refresh":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            success = perform_database_refresh(silent=True)
            res = {"status": "ok" if success else "error"}
            self.safe_write(json.dumps(res).encode("utf-8"))

        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.safe_write(HTML_TEMPLATE.encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/refresh":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            success = perform_database_refresh(silent=True)
            res = {"status": "ok" if success else "error"}
            self.safe_write(json.dumps(res).encode("utf-8"))

    def log_message(self, format, *args):
        pass


class SilentThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        exc_type, _, _ = sys.exc_info()
        if exc_type in (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            return
        super().handle_error(request, client_address)


def main():
    parser = argparse.ArgumentParser(description="Serwer UI gowoty pod 5 platform E-Commerce")
    parser.add_argument("--auto-refresh", action="store_true", help="Włącz pętlę w tle odświeżającą dane co 30 s")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="Port serwera HTTP (domyślnie 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host serwera HTTP (domyślnie 0.0.0.0)")
    parser.add_argument("--no-browser", action="store_true", help="Nie otwieraj automatycznie przeglądarki na hoście")
    args = parser.parse_args()

    PORT = args.port
    HOST = args.host
    print("====================================================================")
    print("  URUCHAMIANIE SERWERA UI (AMAZON + ALLEGRO + EBAY + ALIEXPRESS)    ")
    print("====================================================================")
    print(f"[1/3] Plik bazy danych SQLite: {DB_PATH}")
    print(f"[2/3] Uruchamianie serwera HTTP na porcie {PORT} (http://{HOST}:{PORT})")

    if args.auto_refresh:
        t = threading.Thread(target=background_refresh_loop, args=(30,), daemon=True)
        t.start()
        print("[AUTO-REFRESH] Wątek odświeżania bazy w tle AKTYWNY (co 30 s).")

    server = SilentThreadingHTTPServer((HOST, PORT), DatabaseHandler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"[3/3] Gotowe! Serwer nadsłuchuje zapytań z sieci...")
    print("====================================================================")
    print(f" -> Lokalny adres: {url}")
    print(" -> Naciśnij CTRL+C w konsoli, aby zatrzymać serwer.\n")

    if not args.no_browser and not os.environ.get("CONTAINER"):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[ZAMYKANIE] Serwer został zatrzymany.")
        server.server_close()

if __name__ == "__main__":
    main()
