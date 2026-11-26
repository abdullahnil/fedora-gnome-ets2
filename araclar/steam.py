#!/usr/bin/env python3
"""Steam ayarlarını okuyup yazan küçük yardımcı (yalnızca Python standart kütüphanesi).

Steam'in KeyValues (.vdf) dosyalarını ayrıştırır ve aynı biçimde geri yazar.
Komut satırından fedora-gnome-ets2 tarafından çağrılır:

    steam.py kok                         Steam klasörü
    steam.py oyun APPID                  Oyunun kurulu olduğu klasör (yoksa boş)
    steam.py kutuphane                   Varsayılan kütüphanenin steamapps klasörü
    steam.py uyumluluk-oku APPID         Zorlanan Proton (yoksa boş)
    steam.py uyumluluk-yaz APPID AD      Oyunu bir Proton sürümüne zorla
    steam.py baslatma-oku APPID          Başlatma seçenekleri
    steam.py baslatma-yaz APPID METIN    Başlatma seçeneklerini yaz
    steam.py proton AD                   Proton klasörü (ör. "Proton - Experimental")
    steam.py runtime PROTON_KLASORU      Bu Proton'un istediği Steam Linux Runtime klasörü

Yazan komutlar Steam kapalıyken çalıştırılmalıdır (Steam açıkken dosyaların üstüne yazar)
ve değiştirmeden önce dosyanın tarihli bir yedeğini alır.
"""

import os
import shutil
import sys
import time
from pathlib import Path


# ---------- VDF (KeyValues) ----------
def _belirtecler(metin: str):
    i, n = 0, len(metin)
    while i < n:
        c = metin[i]
        if c in " \t\r\n":
            i += 1
        elif metin.startswith("//", i):
            while i < n and metin[i] != "\n":
                i += 1
        elif c in "{}":
            yield c
            i += 1
        elif c == '"':
            j = i + 1
            parca = []
            while j < n and metin[j] != '"':
                if metin[j] == "\\" and j + 1 < n:      # kaçışları olduğu gibi koru
                    parca.append(metin[j:j + 2])
                    j += 2
                else:
                    parca.append(metin[j])
                    j += 1
            yield ("s", "".join(parca))
            i = j + 1
        else:                                           # tırnaksız değer
            j = i
            while j < n and metin[j] not in " \t\r\n{}\"":
                j += 1
            yield ("s", metin[i:j])
            i = j


def vdf_oku(metin: str) -> dict:
    belirtecler = list(_belirtecler(metin))
    konum = 0

    def blok():
        nonlocal konum
        d = {}
        while konum < len(belirtecler):
            b = belirtecler[konum]
            if b == "}":
                konum += 1
                return d
            anahtar = b[1]
            konum += 1
            sonraki = belirtecler[konum]
            if sonraki == "{":
                konum += 1
                d[anahtar] = blok()
            else:
                d[anahtar] = sonraki[1]
                konum += 1
        return d

    return blok()


def vdf_yaz(d: dict, girinti: int = 0) -> str:
    satirlar = []
    t = "\t" * girinti
    for k, v in d.items():
        if isinstance(v, dict):
            satirlar.append(f'{t}"{k}"\n{t}{{\n{vdf_yaz(v, girinti + 1)}{t}}}\n')
        else:
            satirlar.append(f'{t}"{k}"\t\t"{v}"\n')
    return "".join(satirlar)


def _alt(d: dict, *yol: str, olustur: bool = False) -> dict | None:
    """Büyük/küçük harfe duyarsız olarak iç içe bir bloğa iner (Steam ikisini de kullanıyor)."""
    for parca in yol:
        anahtar = next((k for k in d if k.lower() == parca.lower()), None)
        if anahtar is None:
            if not olustur:
                return None
            d[parca] = {}
            anahtar = parca
        d = d[anahtar]
    return d


# ---------- Steam'i bulma ----------
def kok() -> Path | None:
    for aday in (Path.home() / ".local/share/Steam", Path.home() / ".steam/steam",
                 Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam"):
        if (aday / "steamapps").is_dir():
            return aday.resolve()
    return None


def kutuphaneler() -> list[Path]:
    k = kok()
    if not k:
        return []
    yollar = [k / "steamapps"]
    dosya = k / "steamapps/libraryfolders.vdf"
    if dosya.exists():
        for v in vdf_oku(dosya.read_text(encoding="utf-8", errors="replace")).get("libraryfolders", {}).values():
            if isinstance(v, dict) and v.get("path"):
                p = Path(v["path"].replace("\\\\", "\\")) / "steamapps"
                if p.is_dir() and p.resolve() not in [y.resolve() for y in yollar]:
                    yollar.append(p)
    return yollar


def oyun(appid: str) -> Path | None:
    for lib in kutuphaneler():
        m = lib / f"appmanifest_{appid}.acf"
        if m.exists():
            kur = vdf_oku(m.read_text(encoding="utf-8", errors="replace")).get("AppState", {}).get("installdir")
            if kur and (lib / "common" / kur).is_dir():
                return lib / "common" / kur
    return None


def _localconfig() -> Path | None:
    k = kok()
    adaylar = sorted((k / "userdata").glob("*/config/localconfig.vdf"), key=lambda p: p.stat().st_mtime,
                     reverse=True) if k else []
    return adaylar[0] if adaylar else None


def _yedekle(dosya: Path) -> None:
    shutil.copy2(dosya, dosya.with_name(dosya.name + time.strftime(".yedek-%Y%m%d-%H%M%S")))


def _yaz(dosya: Path, veri: dict) -> None:
    _yedekle(dosya)
    gecici = dosya.with_name(dosya.name + ".yeni")
    gecici.write_text(vdf_yaz(veri), encoding="utf-8")
    os.replace(gecici, dosya)


def uyumluluk(appid: str, ad: str | None = None) -> str:
    dosya = kok() / "config/config.vdf"
    veri = vdf_oku(dosya.read_text(encoding="utf-8"))
    steam = _alt(veri, "InstallConfigStore", "Software", "Valve", "Steam")
    if ad is None:
        es = _alt(steam, "CompatToolMapping", appid) if steam else None
        return (es or {}).get("name", "")
    es = _alt(steam, "CompatToolMapping", appid, olustur=True)
    es.clear()
    es.update({"name": ad, "config": "", "priority": "250"})
    _yaz(dosya, veri)
    return ad


def baslatma(appid: str, metin: str | None = None) -> str:
    dosya = _localconfig()
    if not dosya:
        raise SystemExit("Steam kullanıcı ayarları (localconfig.vdf) bulunamadı. Steam'e bir kez giriş yap.")
    veri = vdf_oku(dosya.read_text(encoding="utf-8"))
    uygulamalar = _alt(veri, "UserLocalConfigStore", "Software", "Valve", "Steam", "apps", olustur=metin is not None)
    if metin is None:
        return (_alt(uygulamalar, appid) or {}).get("LaunchOptions", "") if uygulamalar else ""
    _alt(uygulamalar, appid, olustur=True)["LaunchOptions"] = metin.replace("\\", "\\\\").replace('"', '\\"')
    _yaz(dosya, veri)
    return metin


def proton(ad: str) -> Path | None:
    for lib in kutuphaneler():
        if (lib / "common" / ad / "proton").exists():
            return lib / "common" / ad
    p = kok() / "compatibilitytools.d" / ad
    return p if (p / "proton").exists() else None


def runtime(proton_klasoru: str) -> Path | None:
    """Proton'un toolmanifest.vdf'indeki require_tool_appid'den Steam Linux Runtime klasörünü bulur."""
    manifest = Path(proton_klasoru) / "toolmanifest.vdf"
    if manifest.exists():
        appid = vdf_oku(manifest.read_text(encoding="utf-8")).get("manifest", {}).get("require_tool_appid")
        if appid:
            yer = oyun(appid)
            if yer and (yer / "run").exists():
                return yer
    for lib in kutuphaneler():                         # yedek: en yeni SteamLinuxRuntime_*
        for aday in sorted((lib / "common").glob("SteamLinuxRuntime*"), reverse=True):
            if (aday / "run").exists():
                return aday
    return None


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    k, *a = argv
    if kok() is None:
        raise SystemExit("Steam bulunamadı. Steam'i kurup bir kez aç.")
    sonuc = {
        "kok": lambda: kok(),
        "kutuphane": lambda: kutuphaneler()[0],
        "oyun": lambda: oyun(a[0]),
        "uyumluluk-oku": lambda: uyumluluk(a[0]),
        "uyumluluk-yaz": lambda: uyumluluk(a[0], a[1]),
        "baslatma-oku": lambda: baslatma(a[0]),
        "baslatma-yaz": lambda: baslatma(a[0], a[1]),
        "proton": lambda: proton(a[0]),
        "runtime": lambda: runtime(a[0]),
    }.get(k)
    if sonuc is None:
        print(__doc__)
        return 1
    deger = sonuc()
    print(deger if deger is not None else "")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
