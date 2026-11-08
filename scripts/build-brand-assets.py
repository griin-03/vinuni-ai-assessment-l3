"""Create editable SVG brand and school assessment illustrations."""
from pathlib import Path
from html import escape
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BRAND = '#792F3A'
COLORS = json.loads((ROOT / 'content/ocean-palette.json').read_text())['colors']


def svg(name, width, height, body, title):
    body = re.sub(r'#[0-9a-fA-F]{6}\b', lambda match: COLORS.get(match[0].upper(), match[0]), body)
    destination = ROOT / 'assets' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}"><title>{escape(title)}</title><g font-family="Arial, sans-serif">{body}</g></svg>')


def text(x, y, value, size=26, color=BRAND, weight=400, extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" {extra}>{escape(value)}</text>'


mark = '<rect x="12" y="48" width="94" height="94" rx="24" fill="#792F3A"/><path d="m34 96 17 18 34-40" fill="none" stroke="#FFF4F5" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>'
svg('brand/vinassess-logo.svg', 600, 202, mark + text(124, 119, 'VinAssess', 81, weight=700, extra='letter-spacing="-4"'), 'VinAssess')
svg('brand/vinassess-logo-light.svg', 600, 202, mark + text(124, 119, 'VinAssess', 81, '#FFF5F8', 700, extra='letter-spacing="-4"'), 'VinAssess')
svg('brand/vinassess-icon.svg', 64, 64, '<rect width="64" height="64" rx="17" fill="#792F3A"/><path d="m16 32 11 12 23-27" fill="none" stroke="#FFF4F5" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>', 'VinAssess')
svg('brand/learning-badge.svg', 420, 110, '<rect x="1" y="1" width="418" height="108" rx="20" fill="#FFF5F6" stroke="#EDD2D6"/><circle cx="50" cy="55" r="26" fill="#792F3A"/><path d="m36 55 10 10 18-22" fill="none" stroke="white" stroke-width="5" stroke-linecap="round"/>' + text(94, 48, 'KIỂM TRA & ÔN TẬP THCS, THPT', 17, weight=700) + text(94, 77, 'Soạn đề · Làm bài · Ôn tập', 17), 'Soạn đề · Làm bài · Ôn tập')

body = '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#FFF8F9"/><stop offset="1" stop-color="#F0DDE0"/></linearGradient></defs><rect width="1600" height="900" fill="url(#bg)"/><circle cx="1450" cy="80" r="300" fill="#EACDD3" opacity=".5"/>'
body += text(100, 125, 'VinAssess', 54, weight=700)
body += text(100, 185, 'KIỂM TRA & ÔN TẬP THCS, THPT', 20, weight=700, extra='letter-spacing="4"')
body += text(100, 290, 'Học đúng trọng tâm.', 66, '#342329', 700)
body += text(100, 374, 'Hiểu bài từ lỗi sai.', 66, '#342329', 700)
body += text(100, 435, 'Kiểm tra & Ôn tập THCS, THPT', 31, '#795B63')
cards = [('01', 'Ôn tập', 'Ôn kiến thức nền'), ('02', 'Khảo thí', 'Làm bài có thời gian'), ('03', 'Xem lời giải', 'Củng cố đúng trọng tâm'), ('04', 'Năng lực', 'Theo dõi sự phát triển')]
for i, (number, title, subtitle) in enumerate(cards):
    x = 100 + i * 358
    body += f'<rect x="{x}" y="525" width="330" height="210" rx="28" fill="white" stroke="#EACCD2"/>'
    body += text(x + 25, 578, number, 25, '#AD7581', 700) + text(x + 25, 636, title, 34, weight=700) + text(x + 25, 682, subtitle, 21, '#7A666C')
svg('illustrations/training-overview.svg', 1600, 900, body, 'VinAssess – Kiểm tra & Ôn tập THCS, THPT')

body = '<rect width="1440" height="1000" rx="24" fill="#FAF7F8"/><path d="M0 70h1440" stroke="#E8DDE0"/><rect x="0" y="0" width="244" height="1000" fill="#4B1420"/>'
body += text(32, 51, 'VinAssess', 31, '#FFF8FA', 700) + text(280, 47, 'Không gian dạy và học', 23, '#5A3A43', 700)
body += '<rect x="1250" y="20" width="150" height="32" rx="16" fill="#F5E4E8"/>' + text(1268, 42, 'BẢN MINH HỌA', 13, weight=700)
for i, label in enumerate(['Tổng quan', 'Chương trình', 'Khảo thí', 'Học liệu', 'Khung năng lực', 'Báo cáo']):
    y = 130 + i * 72
    if i == 0:
        body += f'<rect x="18" y="{y - 32}" width="208" height="52" rx="12" fill="#833746"/>'
    body += text(39, y, label, 20, '#FFF0F3' if i == 0 else '#D8B9C0', 700 if i == 0 else 400)
body += text(285, 132, 'Từ bài kiểm tra đến nội dung cần ôn lại', 35, '#342329', 700)
body += text(285, 177, 'Giáo viên soạn đề, giao phòng thi và xem lại kết quả của học sinh.', 18, '#846D74')
for i, (title, value, subtitle) in enumerate([('Chương trình', '04', 'Theo mục tiêu bài kiểm tra'), ('Chủ đề mẫu', '11', 'Theo môn và khối lớp'), ('Chu trình học', '04 bước', 'Học tập và đánh giá liên tục')]):
    x = 285 + i * 365
    body += f'<rect x="{x}" y="215" width="340" height="180" rx="18" fill="white" stroke="#EEE4E7"/>'
    body += text(x + 24, 255, title, 18, '#846D74') + text(x + 24, 322, value, 45, weight=700) + text(x + 24, 365, subtitle, 15, '#846D74')
body += '<rect x="285" y="430" width="1070" height="495" rx="20" fill="white" stroke="#EEE4E7"/>' + text(315, 478, 'Tiến độ theo nhóm đào tạo', 25, '#342329', 700) + text(315, 512, 'Dữ liệu tổng hợp minh họa, không phải kết quả học sinh thật', 16, '#927F85')
for i, (title, percent) in enumerate([('Toán 9 · Phương trình', 82), ('Toán 12 · Hàm số', 64), ('Tiếng Anh 9 · Ngữ pháp', 91), ('Vật lý 12 · Dao động', 58)]):
    y = 575 + i * 84
    body += text(315, y, title, 20, '#5D434B') + f'<rect x="780" y="{y - 19}" width="430" height="12" rx="6" fill="#F5E9EC"/><rect x="780" y="{y - 19}" width="{430 * percent / 100}" height="12" rx="6" fill="#A95A6C"/>' + text(1250, y, f'{percent}%', 18, weight=700)
svg('illustrations/workspace.svg', 1440, 1000, body, 'VinAssess – Minh họa không gian giáo viên và học sinh')

for i, (name, label, number) in enumerate([('onboarding', 'ÔN TẬP THCS', '01'), ('assessment', 'KIỂM TRA', '02'), ('skills', 'ÔN TẬP THPT', '03'), ('compliance', 'TỰ LUYỆN', '04')]):
    backgrounds = ['#792F3A', '#5A2531', '#A95A6C', '#40202A']
    body = f'<rect width="750" height="245" rx="24" fill="{backgrounds[i]}"/><circle cx="665" cy="55" r="140" fill="white" opacity=".06"/><circle cx="90" cy="225" r="150" fill="white" opacity=".04"/>'
    body += text(44, 76, number, 34, '#E7B9C5', 700) + text(44, 164, label, 61, '#FFF8FA', 700)
    body += '<path d="m615 130 25 25 47-58" fill="none" stroke="#E8C1CB" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>'
    svg(f'illustrations/{name}.svg', 750, 245, body, label)

articles = [('ÔN TẬP THCS', ['Thiết kế hành trình', 'cho học sinh lớp 9']), ('KHUNG KIỂM TRA', ['Đúng tiêu chí.', 'Rõ mục tiêu.']), ('HỌC LIỆU THEO MÔN', ['Đúng nội dung.', 'Đúng khối lớp.']), ('KHẢO THÍ', ['Từ kiến thức', 'đến năng lực']), ('XEM LẠI LỖI SAI', ['Đánh giá theo', 'bộ tiêu chí']), ('ĐO LƯỜNG', ['Theo dõi tiến bộ', 'sau mỗi bài kiểm tra'])]
for i, (category, lines) in enumerate(articles):
    light = i % 2 == 0
    background, foreground = ('#F9E8EC', '#6D2937') if light else ('#642332', '#FFF3F6')
    body = f'<rect width="1200" height="675" fill="{background}"/><circle cx="1100" cy="120" r="280" fill="white" opacity=".09"/><path d="M880 200v280m-100-140h200" stroke="{foreground}" opacity=".12" stroke-width="32"/>'
    body += text(70, 85, 'VINASSESS', 24, foreground, 700, 'letter-spacing="3"') + text(70, 220, category, 27, foreground, 700)
    for j, line in enumerate(lines):
        body += text(70, 340 + j * 88, line, 66, foreground, 700)
    body += text(70, 595, 'KIỂM TRA & ÔN TẬP THCS, THPT', 22, foreground, 400, 'letter-spacing="3"')
    svg(f'illustrations/article-{i + 1}.svg', 1200, 675, body, ' · '.join(lines))

print('Created VinAssess wordmark, favicon, badges and school SVG illustrations.')
