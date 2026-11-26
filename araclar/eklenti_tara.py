#!/usr/bin/env python3
"""Etkin GNOME eklentilerinde düzenli aralıkla çalışan zamanlayıcıları arar.

Kaynak kodda sabit sayılı zamanlayıcıları (timeout_add_seconds(…, 30, …), setInterval)
ve ayarlarındaki "refresh/interval/update" türü değerleri listeler. Bilinen sorunlu
eklentileri ayrıca işaretler. Bir periyot verilirse ona uyanları öne çıkarır.

    eklenti_tara.py [PERİYOT_SN]
"""

import re
import subprocess
import sys
from pathlib import Path

BILINEN = {
    "public-ip-address@theophilediot.github.io":
        "Genel IP adresini en kısa 30 sn'de bir sorgular; her sorguda Shell ~100 ms donabiliyor. "
        "ETS2'deki 30 sn'lik takılmaların sebebi buydu.",
}

ZAMANLAYICI = re.compile(r"(timeout_add_seconds\s*\([^,]*,\s*|timeout_add\s*\([^,]*,\s*|setInterval\s*\([^,]*,\s*)"
                         r"([A-Za-z_][\w.]*|\d+)")
AYAR = re.compile(r"(refresh|interval|update-time|poll|period|frequency)", re.I)


def etkin_eklentiler() -> list[str]:
    r = subprocess.run(["gnome-extensions", "list", "--enabled"], capture_output=True, text=True)
    return r.stdout.split()


def klasor(uuid: str) -> Path | None:
    for kok in (Path.home() / ".local/share/gnome-shell/extensions", Path("/usr/share/gnome-shell/extensions")):
        if (kok / uuid).is_dir():
            return kok / uuid
    return None


def sabitler(kaynak: str) -> dict[str, str]:
    return dict(re.findall(r"(?:const|let|var)\s+([A-Z_][A-Z0-9_]*)\s*=\s*(\d+)\s*;", kaynak))


def zamanlayicilar(d: Path) -> list[tuple[str, float]]:
    """(dosya:satır, saniye) listesi; değeri bulunamayanlar atlanır."""
    sonuc = []
    for js in d.rglob("*.js"):
        try:
            kaynak = js.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        sab = sabitler(kaynak)
        for m in ZAMANLAYICI.finditer(kaynak):
            deger = m.group(2)
            deger = sab.get(deger, deger)
            if not deger.isdigit():
                continue
            sn = float(deger) if "seconds" in m.group(1) else float(deger) / 1000
            if sn >= 1:
                satir = kaynak.count("\n", 0, m.start()) + 1
                sonuc.append((f"{js.relative_to(d)}:{satir}", sn))
    return sonuc


def ayarlar(uuid: str, d: Path) -> list[tuple[str, str]]:
    sema_klasoru = d / "schemas"
    if not sema_klasoru.is_dir():
        return []
    semalar = [p.name.removesuffix(".gschema.xml") for p in sema_klasoru.glob("*.gschema.xml")]
    sonuc = []
    for sema in semalar:
        r = subprocess.run(["gsettings", "--schemadir", str(sema_klasoru), "list-recursively", sema],
                           capture_output=True, text=True)
        for satir in r.stdout.splitlines():
            parca = satir.split(" ", 2)
            if len(parca) == 3 and AYAR.search(parca[1]) and re.fullmatch(r"(u?int\d+ )?\d+", parca[2]):
                sonuc.append((parca[1], parca[2].split()[-1]))
    return sonuc


def main(argv):
    periyot = float(argv[0]) if argv else None
    print("    Etkin eklentilerdeki düzenli zamanlayıcılar:")
    supheli = []
    for uuid in etkin_eklentiler():
        d = klasor(uuid)
        if not d:
            continue
        z = zamanlayicilar(d)
        a = ayarlar(uuid, d)
        uyan = periyot is not None and (any(abs(sn - periyot) < 1 for _, sn in z)
                                        or any(abs(float(v) - periyot) < 1 for _, v in a))
        if uyan or uuid in BILINEN:
            supheli.append(uuid)
        if not (z or a or uuid in BILINEN):
            continue
        isaret = "⚠" if uyan or uuid in BILINEN else " "
        print(f"    {isaret} {uuid}")
        for yer, sn in sorted(set(z), key=lambda x: x[1])[:6]:
            print(f"        {sn:g} sn   {yer}")
        for k, v in a:
            print(f"        ayar {k} = {v}")
        if uuid in BILINEN:
            print(f"        bilinen sorun: {BILINEN[uuid]}")
    if supheli:
        print("\n    Şüpheliler: " + ", ".join(supheli))
        print("    Doğrulamak için: fedora-gnome-ets2 teshis --dene " + supheli[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
