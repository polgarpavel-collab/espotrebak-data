#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Účel:   ilustrační obrázky podle typu zboží pro produkty bez fotky (varianta B auditu, bod 4) – verze 2 „kreativnější“
Web:    espotrebak.cz (Eshop-rychle, šablona New York)
Datum:  26. 11. 2026
Výstup: SVG + PNG 800×800 v ./out (PNG přes rsvg-convert)
Styl:   paleta „Včelí vosk“ (#F99502 oranžová, krémové pozadí, kakaová #5A4636), přechody, stíny,
        dekorativní pozadí (tečky, jiskry), předmět s malým „příběhem“, štítek jako bílá karta.
"""
import os, subprocess

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

ACC, ACC2, SOFT, DARK, INK, MUTED = "#F99502", "#E07A00", "#FDE7BF", "#5A4636", "#2E1D0E", "#8A4B08"
FONT = "'Nunito Sans 12pt ExtraLight 12pt', 'Nunito Sans', sans-serif"
LINE = f'stroke="{DARK}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'

# ---------- společné definice: přechody, stín, vzor teček ----------
DEFS = f'''<defs>
  <radialGradient id="bg" cx="50%" cy="38%" r="75%">
    <stop offset="0" stop-color="#FFFCF5"/><stop offset=".6" stop-color="#FFF1D6"/><stop offset="1" stop-color="#FBDFAE"/>
  </radialGradient>
  <linearGradient id="or" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFB23A"/><stop offset="1" stop-color="{ACC2}"/></linearGradient>
  <linearGradient id="orH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFB23A"/><stop offset="1" stop-color="{ACC2}"/></linearGradient>
  <linearGradient id="wh" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#F3E9D8"/></linearGradient>
  <linearGradient id="dk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4A3A2C"/><stop offset="1" stop-color="#241812"/></linearGradient>
  <linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9AA3A8"/><stop offset=".5" stop-color="#E3E7EA"/><stop offset="1" stop-color="#7C858B"/></linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFE08A"/><stop offset="1" stop-color="#C99A2E"/></linearGradient>
  <filter id="sh" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#5A4636" flood-opacity=".28"/>
  </filter>
  <filter id="shs" x="-30%" y="-30%" width="160%" height="160%">
    <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#5A4636" flood-opacity=".22"/>
  </filter>
  <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="4" r="2.6" fill="{ACC}" opacity=".16"/>
  </pattern>
</defs>'''


def spark(x, y, s=1.0, c=ACC):
    # čtyřcípá jiskra (dekorace)
    return (f'<path transform="translate({x} {y}) scale({s})" d="M0 -22 C3 -6 6 -3 22 0 C6 3 3 6 0 22 C-3 6 -6 3 -22 0 C-6 -3 -3 -6 0 -22Z" fill="{c}"/>')


# ---------- piktogramy (prostor cca 140–660 × 110–560) ----------
PIKTO = {
# --- laserový toner: kazeta v perspektivě, válec, madlo, prášek se sype ---
"toner": f'''
<g filter="url(#sh)">
  <path d="M170 300 L520 250 L640 300 L290 352 Z" fill="#FFFFFF" {LINE}/>
  <path d="M170 300 L290 352 L290 450 L170 398 Z" fill="#EADBC4" {LINE}/>
  <path d="M290 352 L640 300 L640 398 L290 450 Z" fill="url(#wh)" {LINE}/>
  <path d="M290 400 L640 348 L640 398 L290 450 Z" fill="url(#orH)"/>
  <path d="M290 352 L640 300 L640 398 L290 450 Z" fill="none" {LINE}/>
  <path d="M360 300 L360 262 Q360 248 374 246 L500 228 Q514 226 514 240 L514 276" fill="none" stroke="{DARK}" stroke-width="16" stroke-linecap="round"/>
  <ellipse cx="226" cy="372" rx="22" ry="30" fill="url(#gr)" {LINE}/>
  <path d="M320 380 L600 340" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" opacity=".7"/>
</g>
<g fill="{INK}" opacity=".75">
  <circle cx="610" cy="430" r="7"/><circle cx="632" cy="452" r="5"/><circle cx="598" cy="462" r="4"/>
  <circle cx="646" cy="478" r="6"/><circle cx="618" cy="490" r="3.5"/><circle cx="660" cy="504" r="3"/>
</g>''',
# --- inkoustová cartridge: čip, okénko hladiny, barevné kapky CMYK ---
"inkoust": f'''
<g filter="url(#sh)">
  <rect x="270" y="150" width="230" height="300" rx="30" fill="url(#wh)" {LINE}/>
  <rect x="270" y="310" width="230" height="90" fill="url(#or)"/>
  <rect x="270" y="150" width="230" height="300" rx="30" fill="none" {LINE}/>
  <rect x="300" y="186" width="58" height="86" rx="10" fill="#EAF6FB" {LINE}/>
  <rect x="300" y="236" width="58" height="36" fill="#2F9BD6"/>
  <rect x="300" y="186" width="58" height="86" rx="10" fill="none" {LINE}/>
  <rect x="390" y="196" width="80" height="60" rx="8" fill="url(#gold)" {LINE}/>
  <path d="M404 212 h52 M404 226 h52 M404 240 h52" stroke="#8A6A18" stroke-width="4"/>
  <rect x="345" y="450" width="80" height="34" rx="8" fill="#E8DCC8" {LINE}/>
</g>
<path d="M385 500 c-16 24 -24 38 -24 50 a24 24 0 0 0 48 0 c0 -12 -8 -26 -24 -50z" fill="#2F9BD6" {LINE}/>
<path d="M560 230 c-20 30 -30 48 -30 62 a30 30 0 0 0 60 0 c0 -14 -10 -32 -30 -62z" fill="#E6007E" {LINE}/>
<path d="M600 370 c-14 22 -22 34 -22 44 a22 22 0 0 0 44 0 c0 -10 -8 -22 -22 -44z" fill="#FFD400" {LINE}/>
<path d="M210 320 c-14 22 -22 34 -22 44 a22 22 0 0 0 44 0 c0 -10 -8 -22 -22 -44z" fill="#1A1A1A" {LINE}/>''',
# --- TTR páska: role s odvíjenou páskou, pod ní vytištěný štítek s čárovým kódem ---
"ttr": f'''
<g filter="url(#sh)">
  <rect x="300" y="380" width="330" height="140" rx="16" fill="#FFFFFF" {LINE}/>
  <g fill="{INK}">
    <rect x="330" y="410" width="8" height="70"/><rect x="346" y="410" width="4" height="70"/><rect x="358" y="410" width="12" height="70"/>
    <rect x="378" y="410" width="4" height="70"/><rect x="390" y="410" width="8" height="70"/><rect x="406" y="410" width="4" height="70"/>
    <rect x="418" y="410" width="12" height="70"/><rect x="438" y="410" width="6" height="70"/><rect x="452" y="410" width="4" height="70"/>
    <rect x="464" y="410" width="10" height="70"/><rect x="482" y="410" width="4" height="70"/><rect x="494" y="410" width="8" height="70"/>
  </g>
  <rect x="520" y="414" width="84" height="14" rx="7" fill="{SOFT}"/><rect x="520" y="440" width="60" height="14" rx="7" fill="{SOFT}"/>
  <rect x="520" y="466" width="72" height="14" rx="7" fill="{ACC}"/>
</g>
<path d="M300 300 C 420 300, 470 330, 560 392" fill="none" stroke="url(#dk)" stroke-width="46"/>
<g filter="url(#sh)">
  <circle cx="250" cy="250" r="120" fill="url(#dk)" {LINE}/>
  <circle cx="250" cy="250" r="92" fill="none" stroke="#5B4838" stroke-width="3"/>
  <circle cx="250" cy="250" r="66" fill="none" stroke="#5B4838" stroke-width="3"/>
  <circle cx="250" cy="250" r="42" fill="url(#or)" {LINE}/>
  <circle cx="250" cy="250" r="16" fill="#FFF7E6" {LINE}/>
  <path d="M200 175 a95 95 0 0 1 80 -22" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" opacity=".35" fill="none"/>
</g>''',
# --- servisní díl: silueta tiskárny, ozubené kolo a klíč přes ni ---
"servis": f'''
<g filter="url(#sh)">
  <rect x="190" y="270" width="420" height="170" rx="30" fill="url(#wh)" {LINE}/>
  <path d="M260 270 L280 190 L520 190 L540 270" fill="#FFFFFF" {LINE}/>
  <rect x="260" y="380" width="280" height="30" rx="8" fill="#EADBC4" {LINE}/>
  <circle cx="560" cy="310" r="10" fill="#4CAF50"/>
  <path d="M290 440 L300 500 L500 500 L510 440" fill="#FFFFFF" {LINE}/>
  <path d="M330 470 h140" stroke="{SOFT}" stroke-width="8" stroke-linecap="round"/>
</g>
<g transform="translate(250 230) scale(.95)" filter="url(#shs)">
  <path d="M-16 -98 h32 l7 26 a75 75 0 0 1 22 9 l23 -14 l23 23 l-14 23 a75 75 0 0 1 9 22 l26 7 v32 l-26 7 a75 75 0 0 1 -9 22 l14 23 l-23 23 l-23 -14 a75 75 0 0 1 -22 9 l-7 26 h-32 l-7 -26 a75 75 0 0 1 -22 -9 l-23 14 l-23 -23 l14 -23 a75 75 0 0 1 -9 -22 l-26 -7 v-32 l26 -7 a75 75 0 0 1 9 -22 l-14 -23 l23 -23 l23 14 a75 75 0 0 1 22 -9z" fill="url(#or)" {LINE}/>
  <circle r="30" fill="#FFF7E6" {LINE}/>
</g>
<g filter="url(#shs)">
  <path d="M640 170 a58 58 0 0 0 -78 70 l-150 150 a24 24 0 0 0 34 34 l150 -150 a58 58 0 0 0 70 -78 l-36 36 l-30 -6 l-6 -30z" fill="url(#gr)" {LINE}/>
</g>''',
# --- velkoformát: velká role, odvinutý plakát s krajinou ---
"role": f'''
<g filter="url(#sh)">
  <path d="M190 200 h420 v300 q-40 -14 -80 0 t-80 0 t-80 0 t-80 0 t-100 0 z" fill="#FFFFFF" {LINE}/>
  <rect x="220" y="230" width="360" height="230" rx="10" fill="#BEE3F8"/>
  <circle cx="510" cy="280" r="28" fill="#FFD23F"/>
  <path d="M220 460 L310 330 L370 400 L440 300 L580 460 Z" fill="#5A8F3C"/>
  <path d="M310 330 L330 358 L292 358 Z M440 300 L462 332 L420 332 Z" fill="#FFFFFF"/>
  <rect x="220" y="230" width="360" height="230" rx="10" fill="none" {LINE}/>
</g>
<g filter="url(#sh)">
  <rect x="150" y="140" width="500" height="88" rx="44" fill="url(#or)" {LINE}/>
  <path d="M190 160 h380" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" opacity=".45"/>
  <ellipse cx="650" cy="184" rx="26" ry="44" fill="#FFE2B0" {LINE}/>
  <ellipse cx="650" cy="184" rx="12" ry="20" fill="{DARK}"/>
</g>''',
# --- barvicí páska: kazeta, smyčka pásky, vytištěné ABC ---
"barvici": f'''
<g filter="url(#sh)">
  <rect x="150" y="170" width="500" height="230" rx="34" fill="url(#wh)" {LINE}/>
  <circle cx="280" cy="285" r="70" fill="url(#dk)" {LINE}/>
  <circle cx="520" cy="285" r="52" fill="url(#dk)" {LINE}/>
  <circle cx="280" cy="285" r="22" fill="url(#or)" {LINE}/>
  <circle cx="520" cy="285" r="22" fill="url(#or)" {LINE}/>
  <path d="M350 285 h100" stroke="{SOFT}" stroke-width="10" stroke-linecap="round"/>
  <path d="M200 400 v46 h400 v-46" fill="url(#dk)" {LINE}/>
</g>
<g filter="url(#shs)">
  <rect x="230" y="470" width="340" height="66" rx="10" fill="#FFFFFF" {LINE}/>
  <text x="400" y="518" text-anchor="middle" font-family="DejaVu Sans Mono, monospace" font-weight="700" font-size="38" fill="{INK}" letter-spacing="6">ABC 123</text>
</g>''',
# --- kancelář: pořadač, lepicí lístky, kancelářská sponka, pero ---
"kancelar": f'''
<g filter="url(#sh)">
  <rect x="200" y="140" width="190" height="330" rx="18" fill="url(#or)" {LINE}/>
  <rect x="236" y="190" width="118" height="80" rx="10" fill="#FFFFFF" {LINE}/>
  <path d="M256 216 h78 M256 242 h54" stroke="{SOFT}" stroke-width="8" stroke-linecap="round"/>
  <circle cx="295" cy="390" r="28" fill="#FFF7E6" {LINE}/>
</g>
<g filter="url(#shs)">
  <g transform="rotate(-8 495 265)">
    <rect x="420" y="190" width="150" height="150" rx="8" fill="#FFE45C" {LINE}/>
    <path d="M446 238 h88 M446 266 h70 M446 294 h80" stroke="#C9A800" stroke-width="7" stroke-linecap="round"/>
  </g>
  <rect x="455" y="320" width="130" height="130" rx="8" fill="#7FD1AE" transform="rotate(6 520 385)" {LINE}/>
</g>
<g filter="url(#shs)">
  <path d="M600 160 l40 14 l-130 330 l-46 26 l6 -54z" fill="#FFFFFF" {LINE}/>
  <path d="M600 160 l40 14 l-14 36 l-40 -14z" fill="url(#or)" {LINE}/>
</g>
<path d="M180 520 h40 a12 12 0 0 0 0 -24 h-46 a20 20 0 0 0 0 40 h52" fill="none" stroke="url(#gr)" stroke-width="7" stroke-linecap="round"/>''',
# --- obecný: balík s páskou, „letí“ k zákazníkovi ---
"obecny": f'''
<path d="M120 300 h80 M100 350 h90 M130 400 h60" stroke="{ACC}" stroke-width="10" stroke-linecap="round" opacity=".6"/>
<g filter="url(#sh)">
  <path d="M420 150 l210 84 v220 l-210 84 l-210 -84 v-220z" fill="#F2C98A" {LINE}/>
  <path d="M210 234 l210 84 v220 l-210 -84z" fill="#E7B36A" {LINE}/>
  <path d="M420 318 l210 -84 v220 l-210 84z" fill="#F6D7A6" {LINE}/>
  <path d="M315 192 l210 84 v66 l-40 16 v-66 l-210 -84z" fill="url(#or)" {LINE}/>
  <path d="M420 318 v220" fill="none" {LINE}/>
  <path d="M470 400 l110 -44 v64 l-110 44z" fill="#FFFFFF" {LINE}/>
  <path d="M486 412 l74 -30 M486 432 l50 -20" stroke="{SOFT}" stroke-width="7" stroke-linecap="round"/>
</g>''',
}

TYPY = {
    "esp-ilustrace-toner":    ("toner",    "Toner"),
    "esp-ilustrace-inkoust":  ("inkoust",  "Inkoustová cartridge"),
    "esp-ilustrace-ttr":      ("ttr",      "TTR páska"),
    "esp-ilustrace-servis":   ("servis",   "Servisní díl tiskárny"),
    "esp-ilustrace-role":     ("role",     "Velkoformátové médium"),
    "esp-ilustrace-barvici":  ("barvici",  "Barvicí páska"),
    "esp-ilustrace-kancelar": ("kancelar", "Kancelářské potřeby"),
    "esp-ilustrace-obecny":   ("obecny",   "Zboží eSpotřebák"),
}


def svg(pikto, titulek):
    fs = 50 if len(titulek) <= 14 else 42 if len(titulek) <= 20 else 38
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
{DEFS}
  <!-- pozadí: teplý přechod, tečky, velké měkké tvary -->
  <rect width="800" height="800" fill="url(#bg)"/>
  <rect width="800" height="800" fill="url(#dots)"/>
  <circle cx="700" cy="110" r="150" fill="{ACC}" opacity=".10"/>
  <circle cx="90" cy="560" r="120" fill="{ACC}" opacity=".08"/>
  <ellipse cx="400" cy="570" rx="250" ry="24" fill="{DARK}" opacity=".10"/>
  {spark(668, 540, .9)}{spark(120, 200, .7, "#FFB23A")}{spark(712, 260, .5, DARK)}
  <!-- předmět -->
  {PIKTO[pikto]}
  <!-- štítek: bílá karta s oranžovým proužkem -->
  <g filter="url(#shs)">
    <rect x="120" y="610" width="560" height="140" rx="28" fill="#FFFFFF"/>
    <rect x="120" y="610" width="14" height="140" rx="7" fill="url(#or)"/>
  </g>
  <text x="408" y="672" text-anchor="middle" font-family="{FONT}" font-weight="800" font-size="{fs}" fill="{INK}">{titulek}</text>
  <text x="408" y="718" text-anchor="middle" font-family="{FONT}" font-weight="400" font-size="23" fill="{MUTED}">Ilustrační obrázek · skutečný vzhled se může lišit</text>
  <!-- logo v pilulce -->
  <g filter="url(#shs)"><rect x="28" y="26" width="236" height="58" rx="29" fill="#FFFFFF"/></g>
  <text x="52" y="66" font-family="{FONT}" font-weight="800" font-size="30" fill="{ACC}">eSpotřebák<tspan fill="{DARK}" font-size="22">.cz</tspan></text>
</svg>'''


for soubor, (p, t) in TYPY.items():
    sp = os.path.join(OUT, soubor + ".svg")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(svg(p, t))
    subprocess.run(["rsvg-convert", "-w", "800", "-h", "800", "-o", os.path.join(OUT, soubor + ".png"), sp], check=True)
print("hotovo:", len(TYPY), "obrázků v", OUT)
