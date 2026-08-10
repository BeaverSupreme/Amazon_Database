#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_cloud_site.py — Skrypt do ZDALNEGO ODŚWIEŻANIA TWOJEJ STRONY NA RENDER.COM
==================================================================================
Pozwala jednym kliknięciem z Windowsa wymusić na chmurze Render.com wygenerowanie
nowej, świeżej bazy produktów wraz ze zaktualizowanymi danymi o sprzedaży (30 dni)!

Jak to działa?
1. Na Render.com wchodzisz w projekt -> Settings -> Deploy Hook i kopiujesz URL.
2. Uruchamiasz ten skrypt z adresem Twojego hooka:
     python refresh_cloud_site.py --hook "https://api.render.com/deploy/srv-xxxx"
3. Render.com natychmiast uruchamia skrypt import_all_amazon_markets.py, przelicza
   nową sprzedaż miesięczną i odświeża Twoją stronę https://amazon-database.onrender.com!

Użycie:
  python refresh_cloud_site.py --demo
  python refresh_cloud_site.py --hook "https://api.render.com/deploy/srv-xxxx"
"""

import sys
import time
import argparse
import urllib.request
import urllib.error

def trigger_render_deploy(hook_url):
    print("====================================================================")
    print("  WYMUSZANIE ODŚWIEŻANIA PRODUKTÓW I SPRZEDAŻY (30 DNI) NA RENDER.COM ")
    print("====================================================================")
    print(f"[1/2] Wysyłanie sygnału odświeżania do chmury Render...")
    try:
        req = urllib.request.Request(hook_url, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            content = response.read().decode('utf-8', errors='ignore')
            print(f"[2/2] Odpowiedź serwera Render: HTTP {status}")
            print(f"      Komunikat: {content or 'Deploy zalecony pomyślnie!'}")
            print("====================================================================")
            print("  [SUKCES] Chmura Render.com rozpoczęła generowanie świeżych danych!")
            print("  Za ok. 30-40 sekund Twoja strona będzie mieć zaktualizowane")
            print("  ceny i statystyki 'Sprzedaż (30 dni)' dla 21 rynków!\n")
            return True
    except Exception as e:
        print(f"[BŁĄD] Nie udało się wysłać sygnału do Render: {e}")
        return False

def run_demo_mode():
    print("====================================================================")
    print("  TRYB DEMONSTRACYJNY SKRYPTU ODŚWIEŻAJĄCEGO (DEMO OFFLINE)        ")
    print("====================================================================")
    print("[1/2] Symulowanie wysłania żądania POST do serwera Render.com...")
    time.sleep(0.5)
    print("[2/2] Odpowiedź serwera Render: HTTP 200 OK")
    print("      Komunikat: {'job': {'id': 'deploy-srv-abc12345', 'status': 'created'}}")
    print("====================================================================")
    print("  [DEMO OK] Skrypt jest gotowy! Aby odświeżać prawdziwą stronę,")
    print("  użyj parametru: python refresh_cloud_site.py --hook <TWÓJ-URL>\n")

def main():
    parser = argparse.ArgumentParser(description="Zdalny wyzwalacz odświeżania bazy i sprzedaży na Render.com")
    parser.add_argument("--demo", action="store_true", help="Uruchom w bezpiecznym trybie demonstracyjnym")
    parser.add_argument("--hook", type=str, help="Adres Deploy Hook URL skopiowany z Render.com -> Settings -> Deploy Hook")

    args = parser.parse_args()

    if args.demo:
        run_demo_mode()
    elif args.hook:
        trigger_render_deploy(args.hook)
    else:
        print("[INFO] Podaj adres swojego Deploy Hook z Render.com lub użyj flagi --demo:")
        print("       python refresh_cloud_site.py --hook 'https://api.render.com/deploy/srv-xxxx'")

if __name__ == "__main__":
    main()
