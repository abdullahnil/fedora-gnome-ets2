#!/usr/bin/env python3
"""MangoHud kayıtlarını (CSV) karşılaştırmalı bir tabloyla özetler.

Ortalama FPS'ten çok akıcılığı belirleyen değerlere bakar: en kötü anlar (%1 ve %0,1
en düşük), uzun kareler, kare süresi sapması ve ardışık kareler arasındaki fark. Büyük
takılmalar düzenli aralıklarla geliyorsa aralığı da yazar.

    kayit_analiz.py KAYIT.csv [KAYIT2.csv ...]
    kayit_analiz.py KLASÖR            (klasördeki bütün kayıtlar, eskiden yeniye)
"""

import csv
import statistics
import sys
from pathlib import Path


def oku(dosya: Path) -> dict:
    satirlar = dosya.read_text(encoding="utf-8", errors="replace").splitlines()
    bas = next(i for i, s in enumerate(satirlar) if s.startswith("fps,"))
    r = list(csv.DictReader(satirlar[bas:]))
    ft = [float(x["frametime"]) for x in r if x.get("frametime")]
    t = [float(x["elapsed"]) / 1e9 for x in r if x.get("elapsed")]
    sirali = sorted(ft)

    def en_dusuk(yuzde):
        k = max(1, int(len(sirali) * yuzde / 100))
        return 1000 / statistics.mean(sirali[-k:])

    orta = statistics.median(ft)
    buyuk = [t[i] for i, x in enumerate(ft) if x > max(50, orta * 3)]
    olaylar = buyuk[:1]
    for a in buyuk[1:]:
        if a - olaylar[-1] > 2:
            olaylar.append(a)
    aralik = [b - a for a, b in zip(olaylar, olaylar[1:])]
    duzenli = None
    if len(aralik) >= 2 and all(abs(x - statistics.median(aralik)) < 1 for x in aralik):
        duzenli = statistics.median(aralik)

    def ort(alan):
        v = [float(x[alan]) for x in r if x.get(alan) not in (None, "", "-")]
        return statistics.mean(v) if v else 0

    return {
        "ad": dosya.stem.split("_", 1)[-1], "sure": t[-1] - t[0] if t else 0,
        "ort": 1000 / statistics.mean(ft), "d1": en_dusuk(1), "d01": en_dusuk(0.1),
        "b25": sum(x > 25 for x in ft), "b50": sum(x > 50 for x in ft), "enb": max(ft),
        "sapma": statistics.pstdev(ft), "fark": statistics.mean(abs(a - b) for a, b in zip(ft, ft[1:])),
        "gpu": ort("gpu_load"), "duzenli": duzenli,
    }


def main(argv):
    dosyalar = []
    for a in argv:
        p = Path(a).expanduser()
        dosyalar += sorted(x for x in p.glob("*.csv") if not x.name.endswith("_summary.csv")) if p.is_dir() else [p]
    if not dosyalar:
        print(__doc__)
        return 1
    print(f"    {'kayıt':<22}{'süre':>6}{'ort FPS':>9}{'%1 düşük':>10}{'%0,1 düşük':>12}{'>25ms':>7}{'>50ms':>7}"
          f"{'en uzun':>9}{'sapma':>8}{'kare farkı':>12}{'GPU':>6}")
    for f in dosyalar:
        try:
            d = oku(f)
        except (StopIteration, KeyError, ValueError, statistics.StatisticsError):
            print(f"    {f.name}: okunamadı")
            continue
        print(f"    {d['ad'][:21]:<22}{d['sure']:5.0f}s{d['ort']:9.1f}{d['d1']:10.1f}{d['d01']:12.1f}{d['b25']:7}"
              f"{d['b50']:7}{d['enb']:7.0f}ms{d['sapma']:6.1f}ms{d['fark']:10.2f}ms{d['gpu']:5.0f}%")
        if d["duzenli"]:
            print(f"      ⚠ büyük takılmalar düzenli: her ~{d['duzenli']:.0f} sn'de bir → 'fedora-gnome-ets2 teshis' çalıştır")
    print("\n    Akıcılık için en önemlisi 'kare farkı' ve '%0,1 düşük': kare farkı küçüldükçe, %0,1 düşük büyüdükçe iyi.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
