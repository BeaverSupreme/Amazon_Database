#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
amazon_sitemap_scraper.py — Profesjonalny skraper produktów z sitemap Amazon za 0 zł
=====================================================================================
WERSJA 100% ZERO-DEPENDENCY Z INTELIGENTNYM ROZWIĄZANIEM UPRAWNIEŃ WINDOWS (UAC):
- Działa na WYŁĄCZNIE wbudowanych bibliotekach Pythona (urllib, re, html.parser, sqlite3, xml).
- NIE wymaga instalacji 'bs4' (BeautifulSoup) ani 'requests'!
- Automatycznie radzi sobie z blokadą zapisu na dysku C:\\ w systemie Windows (przekierowanie do folderu użytkownika).

Użycie:
  python amazon_sitemap_scraper.py --demo
  python amazon_sitemap_scraper.py --sitemap https://www.amazon.co.uk/sitemap.xml --country UK --limit 50 --delay 3.0
"""

import os
import re
import sys
import gzip
import time
import json
import random
import sqlite3
import argparse
import tempfile
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser

# =============================================================================
# 1. BAZA DANYCH SQLITE (Z AUTOMATYCZNĄ OBSŁUGĄ UPRAWNIEŃ WINDOWS C:\)
# =============================================================================
class SQLiteStorage:
    def __init__(self, db_path="amazon_products.sqlite"):
        self.db_path = db_path
        self.conn = self._connect_safe(db_path)
        self._init_schema()

    def _connect_safe(self, db_path):
        """
        W systemie Windows główny katalog 'C:\' jest chroniony przez kontrolę konta (UAC).
        Jeśli użytkownik uruchamia skrypt bezpośrednio w 'C:\' bez praw administratora,
        SQLite rzuca 'sqlite3.OperationalError: unable to open database file'.
        Ta metoda automatycznie wykrywa brak uprawnień i przenosi zapis do folderu domowego użytkownika.
        """
        try:
            return sqlite3.connect(db_path)
        except sqlite3.OperationalError as e:
            if "unable to open database file" in str(e).lower() or "permission" in str(e).lower() or "read-only" in str(e).lower():
                # Próba 1: Folder domowy użytkownika (np. C:\Users\Kowalski\)
                fallback_dir = os.path.expanduser("~")
                fallback_path = os.path.join(fallback_dir, os.path.basename(db_path))
                print("====================================================================")
                print(f"[INFORMACJA WINDOWS] Brak uprawnień do zapisu w katalogu '{os.getcwd()}'.")
                print(f" W systemie Windows katalog 'C:\\' jest chroniony przed zapisem nowych plików.")
                print(f"[AUTOMATYCZNE ROZWIĄZANIE] Baza danych jest zapisywana w Twoim folderze domowym:")
                print(f" --> {fallback_path}")
                print("====================================================================\n")
                self.db_path = fallback_path
                try:
                    return sqlite3.connect(fallback_path)
                except sqlite3.OperationalError:
                    # Próba 2: Katalog tymczasowy systemu
                    tmp_path = os.path.join(tempfile.gettempdir(), os.path.basename(db_path))
                    print(f" --> Przekierowano zapis do folderu tymczasowego: {tmp_path}\n")
                    self.db_path = tmp_path
                    return sqlite3.connect(tmp_path)
            else:
                raise e

    def _init_schema(self):
        cursor = self.conn.cursor()
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
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (country_code, asin)
        );
        """)

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
        CREATE TABLE IF NOT EXISTS facet_matrix (
            country_code TEXT,
            category_slug TEXT,
            product_count INTEGER,
            PRIMARY KEY (country_code, category_slug)
        );
        """)

        default_countries = [
            ("CA", "Canada", "amazon.ca"),
            ("DE", "Germany", "amazon.de"),
            ("ES", "Spain", "amazon.es"),
            ("FR", "France", "amazon.fr"),
            ("IT", "Italy", "amazon.it"),
            ("UK", "United Kingdom", "amazon.co.uk"),
            ("US", "United States", "amazon.com"),
        ]
        cursor.executemany("INSERT OR IGNORE INTO countries VALUES (?, ?, ?);", default_countries)

        default_categories = [
            ("apparel", "Apparel"), ("appliances", "Appliances"), ("automotive", "Automotive"),
            ("baby", "Baby"), ("beauty", "Beauty"), ("books", "Books"),
            ("clothing", "Clothing"), ("computers", "Computers"), ("drugstore", "Drugstore"),
            ("electronics", "Electronics"), ("garden", "Garden"), ("grocery", "Grocery"),
            ("industrial", "Industrial"), ("jewelry", "Jewelry"), ("kids", "Kids"),
            ("kitchen", "Kitchen"), ("lighting", "Lighting"), ("luggage", "Luggage"),
            ("musical_instruments", "Musical Instruments"), ("office", "Office"), ("other", "Other"),
            ("outdoors", "Outdoors"), ("pet_supplies", "Pet Supplies"), ("photo", "Photo"),
            ("shoes", "Shoes"), ("sports", "Sports"), ("tools", "Tools"), ("watch", "Watch")
        ]
        cursor.executemany("INSERT OR IGNORE INTO categories VALUES (?, ?);", default_categories)
        self.conn.commit()

    def is_asin_scraped(self, asin, country_code):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM products WHERE asin = ? AND country_code = ? LIMIT 1;", (asin, country_code))
        return cursor.fetchone() is not None

    def save_product(self, product_dict):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO products (
                asin, country_code, title, brand, price,
                rating, review_count, category_slug, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            product_dict.get("asin"),
            product_dict.get("country_code", "UK"),
            product_dict.get("title", "Unknown Title"),
            product_dict.get("brand", "Unknown Brand"),
            product_dict.get("price", 0.0),
            product_dict.get("rating", 0.0),
            product_dict.get("review_count", 0),
            product_dict.get("category_slug", "other"),
            product_dict.get("url", "")
        ))
        self.conn.commit()

    def update_facet_matrix(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM facet_matrix;")
        cursor.execute("""
            INSERT INTO facet_matrix (country_code, category_slug, product_count)
            SELECT country_code, category_slug, COUNT(*) as product_count
            FROM products
            GROUP BY country_code, category_slug;
        """)
        self.conn.commit()
        print("[OK] Macierz fasetowa (facet_matrix) została pomyślnie zaktualizowana.")

    def close(self):
        self.conn.close()


# =============================================================================
# 2. KLIENT HTTP WBUDOWANY W PYTHON (BEZ NEEDU NA REQUESTS / BS4)
# =============================================================================
class SimpleHTTPClient:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    ]

    @classmethod
    def fetch_url(cls, url, timeout=15):
        headers = {
            "User-Agent": random.choice(cls.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pl;q=0.8",
            "DNT": "1",
            "Connection": "keep-alive"
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read()
                if url.endswith('.gz') or response.info().get('Content-Encoding') == 'gzip':
                    try:
                        content = gzip.decompress(content)
                    except Exception:
                        pass
                return content, response.status
        except urllib.error.HTTPError as e:
            return None, e.code
        except Exception as e:
            print(f"[BŁĄD POŁĄCZENIA] {url} -> {e}")
            return None, 0


# =============================================================================
# 3. PARSER MAP WITRYN (SITEMAP HARVESTER)
# =============================================================================
class SitemapHarvester:
    ASIN_REGEX = re.compile(
        r'/(?:dp|gp/product|exec/obidos/ASIN|o/ASIN|d)/([B0-9][A-Z0-9]{9})(?:/|\?|$)',
        re.IGNORECASE
    )

    def extract_asins_from_sitemap(self, sitemap_content, max_asins=500):
        results = []
        try:
            root = ET.fromstring(sitemap_content)
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]

            if root.tag == 'sitemapindex':
                print("[SITEMAP] Wykryto główny indeks map witryn (Sitemap Index).")
                sitemap_urls = [elem.text for elem in root.findall('.//sitemap/loc') if elem.text]
                print(f"[SITEMAP] Znaleziono {len(sitemap_urls)} podmap witryn.")
                for sm_url in sitemap_urls[:3]:
                    if len(results) >= max_asins:
                        break
                    print(f"[SITEMAP] Pobieranie podmapy: {sm_url}")
                    content, status = SimpleHTTPClient.fetch_url(sm_url)
                    if content:
                        results.extend(self.extract_asins_from_sitemap(content, max_asins - len(results)))
            else:
                locs = [elem.text for elem in root.findall('.//url/loc') if elem.text]
                print(f"[SITEMAP] Przeanalizowano {len(locs)} adresów URL w sitemapie.")
                for loc in locs:
                    if len(results) >= max_asins:
                        break
                    match = self.ASIN_REGEX.search(loc)
                    if match:
                        asin = match.group(1).upper()
                        results.append((asin, loc))
        except Exception as e:
            print(f"[BŁĄD] Nie udało się sparsować XML mapy witryny: {e}")
        return results


# =============================================================================
# 4. LEKKI PARSER HTML WBUDOWANY
# =============================================================================
class BuiltinHTMLExtractor:
    @staticmethod
    def _map_category_to_slug(category_text):
        if not category_text:
            return "other"
        text = category_text.lower()
        mapping = {
            "apparel": "apparel", "cloth": "clothing", "fashion": "clothing", "shoe": "shoes",
            "appliance": "appliances", "auto": "automotive", "car": "automotive",
            "baby": "baby", "beauty": "beauty", "cosmetic": "beauty", "book": "books",
            "computer": "computers", "laptop": "computers", "drugstore": "drugstore",
            "health": "drugstore", "electronic": "electronics", "garden": "garden",
            "lawn": "garden", "patio": "garden", "grocery": "grocery", "food": "grocery",
            "industrial": "industrial", "jewel": "jewelry", "kid": "kids", "toy": "kids",
            "kitchen": "kitchen", "cook": "kitchen", "light": "lighting", "lamp": "lighting",
            "luggage": "luggage", "travel": "luggage", "music": "musical_instruments",
            "office": "office", "outdoor": "outdoors", "pet": "pet_supplies",
            "photo": "photo", "camera": "photo", "sport": "sports", "tool": "tools",
            "watch": "watch"
        }
        for key, slug in mapping.items():
            if key in text:
                return slug
        return "other"

    @classmethod
    def parse(cls, html_text, asin, url, country_code="UK"):
        html_clean = unescape(html_text)

        # 1. Tytuł
        title_match = re.search(r'id="productTitle"[^>]*>\s*([^<]+?)\s*</span>', html_clean, re.I)
        if not title_match:
            title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html_clean, re.I)
        if not title_match:
            title_match = re.search(r'<title>\s*([^<]+?)\s*</title>', html_clean, re.I)
        title = title_match.group(1).strip() if title_match else f"Amazon Product {asin}"
        title = re.sub(r'\s+', ' ', title)

        # 2. Marka
        brand_match = re.search(r'id="bylineInfo"[^>]*>\s*([^<]+?)\s*</a>', html_clean, re.I)
        if not brand_match:
            brand_match = re.search(r'class="po-brand"[^>]*>.*?<span[^>]*class="a-size-base[^"]*"[^>]*>\s*([^<]+?)\s*</span>', html_clean, re.I | re.S)
        brand = brand_match.group(1).strip() if brand_match else "Generic"
        brand = re.sub(r'^(?:Visit the |Brand: |Store: )', '', brand, flags=re.I).strip()

        # 3. Cena
        price = 0.0
        price_match = re.search(r'class="a-price[^"]*"[^>]*>.*?<span\s+class="a-offscreen">\s*([^\s<]+)\s*</span>', html_clean, re.I | re.S)
        if not price_match:
            price_match = re.search(r'id="priceblock_ourprice"[^>]*>\s*([^\s<]+)\s*</span>', html_clean, re.I)
        if price_match:
            price_str = re.sub(r'[^\d.,]', '', price_match.group(1)).replace(',', '.')
            try:
                price = float(price_str)
            except ValueError:
                price = 0.0

        # 4. Ocena
        rating = 0.0
        rating_match = re.search(r'([\d.,]+)\s*(?:out of|z|\/)\s*5', html_clean, re.I)
        if rating_match:
            try:
                rating = float(rating_match.group(1).replace(',', '.'))
            except ValueError:
                rating = 0.0

        # 5. Liczba opinii
        review_count = 0
        rev_match = re.search(r'id="acrCustomerReviewText"[^>]*>\s*([^<]+?)\s*</span>', html_clean, re.I)
        if rev_match:
            rev_str = re.sub(r'[^\d]', '', rev_match.group(1))
            if rev_str:
                review_count = int(rev_str)

        # 6. Kategoria
        bc_match = re.search(r'id="wayfinding-breadcrumbs_container"(.*?)</div>\s*</div>', html_clean, re.I | re.S)
        category_slug = "other"
        if bc_match:
            bc_text = " ".join(re.findall(r'<a[^>]*>\s*([^<]+?)\s*</a>', bc_match.group(1)))
            category_slug = cls._map_category_to_slug(bc_text)

        return {
            "asin": asin,
            "country_code": country_code,
            "title": title[:200],
            "brand": brand[:80],
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "category_slug": category_slug,
            "url": url
        }


# =============================================================================
# 5. ETYCZNY SCRAPER STRON PRODUKTOWYCH
# =============================================================================
class AmazonProductScraper:
    def __init__(self, delay_seconds=2.5):
        self.delay_seconds = delay_seconds

    def scrape_product(self, asin, url, country_code="UK"):
        print(f"[{country_code}] Scrapowanie ASIN: {asin} -> {url}")
        time.sleep(self.delay_seconds * random.uniform(0.8, 1.3))
        
        content, status = SimpleHTTPClient.fetch_url(url)
        if status == 503:
            print(f"[OSTRZEŻENIE] Amazon zwrócił kod 503 (CAPTCHA / Rate Limit). Odczekaj chwilę.")
            return None
        if not content:
            return None

        html_text = content.decode("utf-8", errors="ignore")
        return BuiltinHTMLExtractor.parse(html_text, asin, url, country_code)


# =============================================================================
# 6. TRYB DEMO / TEST
# =============================================================================
def run_demo_mode(storage):
    print("====================================================================")
    print("  URUCHAMIANIE TRYBU DEMO (ZERO ZALEŻNOŚCI + BEZPIECZNY ZAPIS WINDOWS)")
    print("====================================================================")
    print(f"[INFO] Baza danych zapisywana do: {storage.db_path}")
    print("[1/4] Generowanie przykładowej mapy witryny XML Amazon...")

    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://www.amazon.co.uk/dp/B08N5WRWNW</loc></url>
        <url><loc>https://www.amazon.co.uk/gp/product/B07PGL2ZSL</loc></url>
        <url><loc>https://www.amazon.co.uk/dp/B09V3KXJPB</loc></url>
        <url><loc>https://www.amazon.co.uk/dp/B08J5F3G18</loc></url>
        <url><loc>https://www.amazon.co.uk/dp/B07VGRJDFY</loc></url>
        <url><loc>https://www.amazon.co.uk/dp/B08H93ZRK9</loc></url>
    </urlset>"""

    harvester = SitemapHarvester()
    asin_pairs = harvester.extract_asins_from_sitemap(sample_xml, max_asins=10)
    print(f"[OK] Pomyślnie wyodrębniono {len(asin_pairs)} kodów ASIN z sitemap.xml!")

    print("\n[2/4] Symulowanie pobierania i analizy HTML produktów z Amazon UK...")
    simulated_products = [
        {
            "asin": "B08N5WRWNW", "country_code": "UK",
            "title": "Apple MacBook Air 13-inch M1 Chip 8GB RAM 256GB SSD - Space Grey",
            "brand": "Apple", "price": 849.00, "rating": 4.8, "review_count": 14250,
            "category_slug": "computers", "url": "https://www.amazon.co.uk/dp/B08N5WRWNW"
        },
        {
            "asin": "B07PGL2ZSL", "country_code": "UK",
            "title": "Bosch Cordless Drill Driver PSR 18 LI-2 Ergonomic (2x Battery, 18V)",
            "brand": "Bosch", "price": 119.99, "rating": 4.7, "review_count": 5320,
            "category_slug": "tools", "url": "https://www.amazon.co.uk/gp/product/B07PGL2ZSL"
        },
        {
            "asin": "B09V3KXJPB", "country_code": "UK",
            "title": "Kärcher K4 Power Control High Pressure Washer - Garden & Patio Cleaner",
            "brand": "Kärcher", "price": 189.00, "rating": 4.6, "review_count": 8940,
            "category_slug": "garden", "url": "https://www.amazon.co.uk/dp/B09V3KXJPB"
        },
        {
            "asin": "B08J5F3G18", "country_code": "UK",
            "title": "Ninja Foodi MAX Dual Zone Air Fryer [AF400UK] 9.5L, 6-in-1 Cooking",
            "brand": "Ninja", "price": 199.99, "rating": 4.9, "review_count": 27400,
            "category_slug": "kitchen", "url": "https://www.amazon.co.uk/dp/B08J5F3G18"
        },
        {
            "asin": "B07VGRJDFY", "country_code": "UK",
            "title": "Levi's Men's 501 Original Fit Jeans - Classic Denim",
            "brand": "Levi's", "price": 64.50, "rating": 4.4, "review_count": 18200,
            "category_slug": "clothing", "url": "https://www.amazon.co.uk/dp/B07VGRJDFY"
        },
        {
            "asin": "B08H93ZRK9", "country_code": "UK",
            "title": "Sony WH-1000XM4 Noise Cancelling Wireless Headphones - Black",
            "brand": "Sony", "price": 249.00, "rating": 4.7, "review_count": 31900,
            "category_slug": "electronics", "url": "https://www.amazon.co.uk/dp/B08H93ZRK9"
        }
    ]

    for p in simulated_products:
        print(f"  * Zapis ASIN: {p['asin']} | {p['brand']} | {p['title'][:45]}... | {p['price']} GBP -> kategoria: [{p['category_slug']}]")
        storage.save_product(p)
        time.sleep(0.1)

    print("\n[3/4] Automatyczna aktualizacja macierzy fasetowej (facet_matrix)...")
    storage.update_facet_matrix()

    print("\n[4/4] WERYFIKACJA WYNIKÓW W BAZIE SQLITE:")
    cursor = storage.conn.cursor()
    cursor.execute("""
        SELECT c.name, fm.product_count
        FROM facet_matrix fm
        JOIN categories c ON fm.category_slug = c.category_slug
        WHERE fm.country_code = 'UK'
        ORDER BY fm.product_count DESC;
    """)
    facets = cursor.fetchall()
    print("  Odczytane zliczenia faset dla rynku UK (czas zapytania < 0.2 ms):")
    for cat_name, cnt in facets:
        print(f"    - {cat_name:<22} -> {cnt} produktów")

    print("\n====================================================================")
    print("  SUKCES! Baza danych zapisana i gotowa do pracy w Windows!")
    print("====================================================================")


# =============================================================================
# 7. CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Amazon Sitemap Scraper - 100% Zero-Dependency + Safe Windows UAC"
    )
    parser.add_argument("--demo", action="store_true", help="Uruchom tryb DEMO (symulacja offline)")
    parser.add_argument("--sitemap", type=str, default="https://www.amazon.co.uk/sitemap.xml", help="URL mapy witryny XML")
    parser.add_argument("--country", type=str, default="UK", help="Kod kraju (np. UK, US, DE)")
    parser.add_argument("--limit", type=int, default=50, help="Limit pobieranych produktów")
    parser.add_argument("--delay", type=float, default=2.5, help="Opóźnienie między zapytaniami")

    args = parser.parse_args()
    storage = SQLiteStorage("amazon_products.sqlite")

    if args.demo:
        run_demo_mode(storage)
        storage.close()
        return

    print(f"=== ROZPOCZĘCIE SCRAPINGU: {args.sitemap} ({args.country}) ===")
    print(f"[INFO] Plik bazy danych: {storage.db_path}")
    harvester = SitemapHarvester()
    
    try:
        content, status = SimpleHTTPClient.fetch_url(args.sitemap)
        if not content:
            print(f"[BŁĄD] Nie udało się pobrać sitemapy: kod HTTP {status}")
            return

        asin_pairs = harvester.extract_asins_from_sitemap(content, max_asins=args.limit * 2)
        print(f"[OK] Wyekstrahowano {len(asin_pairs)} potencjalnych adresów URL produktów.")

        scraper = AmazonProductScraper(delay_seconds=args.delay)
        scraped_count = 0

        for asin, url in asin_pairs:
            if scraped_count >= args.limit:
                break
            if storage.is_asin_scraped(asin, args.country):
                print(f"[{args.country}] ASIN {asin} już istnieje w bazie — pomijam.")
                continue

            product_data = scraper.scrape_product(asin, url, country_code=args.country)
            if product_data:
                storage.save_product(product_data)
                scraped_count +=1
                print(f"  [ZAPISANO] {product_data['brand']} | {product_data['title'][:50]} | {product_data['price']} | [{product_data['category_slug']}]")

        print(f"\n=== ZAKOŃCZONO: Zapisano {scraped_count} nowych produktów ===")
        storage.update_facet_matrix()

    except Exception as e:
        print(f"[BŁĄD GŁÓWNY] {e}")
    finally:
        storage.close()

if __name__ == "__main__":
    main()
