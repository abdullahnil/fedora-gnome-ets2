#!/usr/bin/env python3
"""GNOME Shell'in ana döngüsünün donup donmadığını ölçer.

Oyunun görüntüsünü ekrana GNOME Shell basar. Shell bir anlığına donarsa oyun da o an
takılır, ama masaüstünde bu genelde fark edilmez. Bu araç Shell'e D-Bus üzerinden
sürekli küçük bir soru sorar ve cevabın ne zaman geciktiğini kaydeder. Donmalar
düzenli aralıklarla geliyorsa (ör. her 30 sn) aralığı da hesaplar.

    shell_yokla.py [SÜRE_SN=70] [--esik MS=40] [--json]
"""

import json
import statistics
import sys
import time
from datetime import datetime

from gi.repository import Gio, GLib


def yokla(sure: float, esik_ms: float):
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    soru = GLib.Variant("(ss)", ("org.gnome.Shell", "ShellVersion"))
    t0 = time.monotonic()
    donmalar = []
    while time.monotonic() - t0 < sure:
        a = time.monotonic()
        bus.call_sync("org.gnome.Shell", "/org/gnome/Shell", "org.freedesktop.DBus.Properties", "Get",
                      soru, None, 0, 5000, None)
        gecikme = (time.monotonic() - a) * 1000
        if gecikme >= esik_ms:
            donmalar.append({"saat": datetime.now().strftime("%H:%M:%S.%f")[:-4],
                             "an": round(a - t0, 2), "ms": round(gecikme)})
        time.sleep(0.01)
    return donmalar


def periyot(donmalar: list[dict]) -> float | None:
    """Donmalar düzenli aralıklarla geliyorsa o aralığı (sn) döndürür."""
    if len(donmalar) < 3:
        return None
    # birbirine 2 sn'den yakın donmaları tek olay say
    olaylar = [donmalar[0]["an"]]
    for d in donmalar[1:]:
        if d["an"] - olaylar[-1] > 2:
            olaylar.append(d["an"])
    if len(olaylar) < 3:
        return None
    aralik = [b - a for a, b in zip(olaylar, olaylar[1:])]
    orta = statistics.median(aralik)
    if orta > 3 and all(abs(x - orta) < 1.0 for x in aralik):
        return round(orta, 1)
    return None


def main(argv):
    sure, esik, js = 70.0, 40.0, False
    i = 0
    while i < len(argv):
        if argv[i] == "--esik":
            esik = float(argv[i + 1]); i += 1
        elif argv[i] == "--json":
            js = True
        else:
            sure = float(argv[i])
        i += 1
    donmalar = yokla(sure, esik)
    p = periyot(donmalar)
    if js:
        print(json.dumps({"donmalar": donmalar, "periyot": p}))
        return 0
    if not donmalar:
        print(f"    ✓ {sure:.0f} saniyede {esik:.0f} ms'den uzun Shell donması yok.")
        return 0
    print(f"    {len(donmalar)} donma (≥ {esik:.0f} ms):")
    for d in donmalar:
        print(f"      {d['saat']}   {d['ms']:4d} ms")
    if p:
        print(f"    ⚠ Donmalar düzenli: yaklaşık her {p:g} saniyede bir. Bu, zamanlayıcılı bir eklentiye işaret eder.")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
