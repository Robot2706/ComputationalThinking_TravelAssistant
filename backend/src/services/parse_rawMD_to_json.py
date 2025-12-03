# File: C:\Users\Admin\source\repos\ComputationalThinking_TravelAssistant\backend\src\services\parse_raw_to_json.py
"""
Script để parse file markdown raw hotels_list.md và xuất ra JSON các object theo dataclass Hotel.
Usage (from repository root or adjust paths):
python src\services\parse_raw_to_json.py \
    --input "C:\\Users\\Admin\\source\\repos\\ComputationalThinking_TravelAssistant\\backend\\data\\raw\\hotels_list.md" \
    --output "C:\\Users\\Admin\\source\\repos\\ComputationalThinking_TravelAssistant\\backend\\data\\processed\\hotels_parsed.json"

Ghi chú:
- Heuristics được dùng để trích xuất district, rating, price, và một số amenities phổ biến.
- Nếu cần mở rộng hoặc tinh chỉnh, chỉnh danh sách AMENITIES_KEYWORDS hoặc regex tương ứng.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import List
import re
import json
import argparse
import os
from pathlib import Path


@dataclass
class Hotel:
    id: int
    name: str
    district: str
    price: float
    rating: float
    capacity: int = 1
    amenities: List[str] = field(default_factory=list)
    details: str = ""


# Các từ khóa tiện nghi phổ biến (có thể mở rộng)
AMENITIES_KEYWORDS = [
    'wi-fi', 'wi fi', 'wifi', 'wifi miễn phí', 'dịch vụ phòng', 'room service',
    'nhà hàng', 'restaurant', 'quầy lễ tân 24 giờ', 'reception', 'bar',
    'bể bơi', 'pool', 'phòng chờ', 'lobby', 'máy sấy tóc', 'tủ lạnh',
    'minibar', 'máy pha trà', 'máy pha cà phê', 'máy pha trà/cà phê', 'két an toàn',
    'đổi ngoại tệ', 'dịch vụ thu đổi ngoại tệ', 'điều hòa', 'air conditioning',
    'wifi miễn', 'bữa sáng', 'buffet', 'phục vụ bữa sáng', 'dọn phòng',
]


def normalize_text(s: str) -> str:
    return s.strip().replace('\r', '\n')


def parse_price(price_str: str) -> float:
    """Parse price string like '499.329,00 VND' or '3.033.640,00 VND' to float.
    Assumes Vietnamese format where '.' is thousand separator and ',' is decimal separator.
    """
    if not price_str:
        return 0.0
    # keep only digits, '.' and ','
    txt = price_str.strip()
    # remove currency words
    txt = re.sub(r'[A-Za-z\s]+', '', txt)
    # remove any trailing non-digit but keep separators
    # convert: remove dots, replace comma with dot
    txt = txt.replace('.', '')
    txt = txt.replace(',', '.')
    try:
        return float(txt)
    except Exception:
        # fallback: extract digits
        digits = re.sub(r'[^0-9]', '', price_str)
        return float(digits) if digits else 0.0


def parse_rating(line: str) -> float:
    m = re.search(r'Đánh giá:\s*([0-9]+(?:\.[0-9])?)', line)
    if not m:
        m = re.search(r'Rating:\s*([0-9]+(?:\.[0-9])?)', line)
    if m:
        try:
            return float(m.group(1))
        except:
            return 0.0
    # try to find first number that looks like 0-10
    m = re.search(r'([0-9]+\.[0-9]+)', line)
    if m:
        try:
            v = float(m.group(1))
            if 0 <= v <= 10:
                return v
        except:
            pass
    return 0.0


def extract_district(text: str) -> str:
    # Try to locate the 'Địa chỉ:' line
    m = re.search(r'Địa chỉ:\s*(.+)', text)
    if m:
        addr = m.group(1)
        # find 'Quận X' or 'Quận X,'
        mq = re.search(r'(Quận\s+[^,\n]+)', addr, flags=re.IGNORECASE)
        if mq:
            return mq.group(1).strip()
        # sometimes 'District' in English
        md = re.search(r'(District\s+[^,\n]+)', addr, flags=re.IGNORECASE)
        if md:
            return md.group(1).strip()
        # fallback: return whole address
        return addr.strip()
    # fallback: try to find 'Quận' anywhere in text
    mq = re.search(r'Quận\s+[^,\n]+', text)
    if mq:
        return mq.group(0).strip()
    return ''


def extract_amenities(block: str) -> List[str]:
    found = []
    low = block.lower()
    for kw in AMENITIES_KEYWORDS:
        if kw in low and kw not in found:
            # unify some keywords for nicer output
            pretty = kw
            if 'wifi' in kw:
                pretty = 'Wi-Fi'
            elif 'dịch vụ phòng' in kw or 'room service' in kw:
                pretty = 'Room service'
            elif 'quầy lễ tân' in kw or 'reception' in kw:
                pretty = '24-hour front desk'
            elif 'bể bơi' in kw or 'pool' in kw:
                pretty = 'Swimming pool'
            elif 'nhà hàng' in kw or 'restaurant' in kw:
                pretty = 'Restaurant'
            elif 'minibar' in kw:
                pretty = 'Minibar'
            elif 'tủ lạnh' in kw:
                pretty = 'Refrigerator'
            elif 'máy pha' in kw:
                pretty = 'Coffee/Tea maker'
            elif 'két an toàn' in kw:
                pretty = 'Safe'
            elif 'đổi ngoại tệ' in kw:
                pretty = 'Currency exchange'
            elif 'điều hòa' in kw:
                pretty = 'Air conditioning'
            elif 'bữa sáng' in kw:
                pretty = 'Breakfast'
            found.append(pretty)
    return found


def split_entries(md: str) -> List[str]:
    # Split entries by lines that start with '---' alone
    parts = re.split(r'\n\s*---\s*\n', md)
    # trim
    return [p.strip() for p in parts if p.strip()]


def parse_entry(entry: str) -> Hotel | None:
    # Expect entry starts with '1. Hotel Name' or '1)'
    lines = [l for l in entry.splitlines() if l.strip()]
    if not lines:
        return None
    # first non-empty line should contain id and name
    first = lines[0].strip()
    m = re.match(r'\s*(\d+)\s*[\.|)]\s*(.+)', first)
    if m:
        hid = int(m.group(1))
        name = m.group(2).strip()
    else:
        # fallback: try to parse leading number
        m2 = re.match(r'\s*(\d+)\s*(.+)', first)
        if m2:
            hid = int(m2.group(1))
            name = m2.group(2).strip()
        else:
            # if no id, skip
            return None

    # join entire entry for easier searching
    whole = '\n'.join(lines)

    # price line: look for 'Giá:'
    price = 0.0
    mprice = re.search(r'Giá:\s*([^\n]+)', whole)
    if mprice:
        price = parse_price(mprice.group(1))
    else:
        # try to find VND token
        mprice2 = re.search(r'([0-9\.,]+)\s*VND', whole, flags=re.IGNORECASE)
        if mprice2:
            price = parse_price(mprice2.group(1))

    # rating
    rating = parse_rating(whole)

    # district
    district = extract_district(whole)

    # details: capture the full 'Mô tả' section (if any) using simple string search
    details = ''
    if 'Mô tả:' in whole:
        start = whole.find('Mô tả:') + len('Mô tả:')
        # find nearest marker after the description
        markers = ['Địa chỉ:', 'Đánh giá:', 'Giá:']
        end_positions = [whole.find(m, start) for m in markers]
        end_candidates = [p for p in end_positions if p != -1]
        if end_candidates:
            end = min(end_candidates)
            details = whole[start:end].strip()
        else:
            details = whole[start:].strip()

    # amenities
    amenities = extract_amenities(whole)

    return Hotel(id=hid, name=name, district=district, price=price, rating=rating, amenities=amenities, details=details)


def parse_markdown_file(path: Path) -> List[Hotel]:
    txt = path.read_text(encoding='utf-8')
    entries = split_entries(txt)
    hotels = []
    for e in entries:
        h = parse_entry(e)
        if h:
            hotels.append(h)
    return hotels


def main():
    parser = argparse.ArgumentParser()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder where this script is
    INPUT_FILE = os.path.join(BASE_DIR, '../../data/raw/hotels_list.md')
    OUTPUT_FILE = os.path.join(BASE_DIR, '../../data/processed/hotels_parsed.json')

    parser.add_argument('--input', '-i', type=str, default=INPUT_FILE)
    parser.add_argument('--output', '-o', type=str, default=OUTPUT_FILE)

    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        print(f"Input file not found: {in_path}")
        return

    hotels = parse_markdown_file(in_path)
    # convert to list of dicts
    hotels_data = [asdict(h) for h in hotels]

    out_path.write_text(json.dumps(hotels_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Parsed {len(hotels)} hotels -> {out_path}")


if __name__ == '__main__':
    main()
