"""
pdf_writer.py — мінімальний генератор PDF на стандартній бібліотеці Python:
одна сторінка, текст TrueType-шрифтом з кирилицею, лінії, прямокутники.

Шрифт вбудовується підмножиною (лише використані гліфи, разом зі складовими
частинами складених гліфів), тож файл важить десятки КБ, а не мегабайти.
Текст у PDF доступний для пошуку й копіювання (є ToUnicode).
"""

import struct
import zlib

A4 = (595.28, 841.89)


# ---------- TrueType ----------

class TrueTypeFont:
    def __init__(self, path: str):
        with open(path, "rb") as f:
            self.data = f.read()
        num = struct.unpack(">H", self.data[4:6])[0]
        self.tables = {}
        for i in range(num):
            tag, _, off, length = struct.unpack(">4sIII", self.data[12 + 16 * i:28 + 16 * i])
            self.tables[tag.decode("latin-1")] = (off, length)
        head = self.table("head")
        self.units = struct.unpack(">H", head[18:20])[0]
        self.bbox = struct.unpack(">hhhh", head[36:44])
        self.long_loca = struct.unpack(">h", head[50:52])[0] == 1
        hhea = self.table("hhea")
        self.ascent, self.descent = struct.unpack(">hh", hhea[4:8])
        n_metrics = struct.unpack(">H", hhea[34:36])[0]
        self.num_glyphs = struct.unpack(">H", self.table("maxp")[4:6])[0]
        hmtx = self.table("hmtx")
        adv = [struct.unpack(">H", hmtx[4 * i:4 * i + 2])[0] for i in range(n_metrics)]
        self.advances = adv + [adv[-1]] * (self.num_glyphs - n_metrics)
        os2 = self.table("OS/2")
        self.cap_height = struct.unpack(">h", os2[88:90])[0] if len(os2) >= 90 else self.ascent
        self.cmap = self._read_cmap()
        name = self.table("name")
        self.ps_name = self._ps_name(name) or "Font"

    def table(self, tag: str) -> bytes:
        off, length = self.tables[tag]
        return self.data[off:off + length]

    def _read_cmap(self) -> dict:
        cmap = self.table("cmap")
        n = struct.unpack(">H", cmap[2:4])[0]
        subtables = {}
        for i in range(n):
            pid, eid, off = struct.unpack(">HHI", cmap[4 + 8 * i:12 + 8 * i])
            subtables[(pid, eid)] = off
        off = subtables.get((3, 1), subtables.get((0, 3)))
        if off is None:
            raise ValueError("шрифт без таблиці cmap формату 4 (Unicode BMP)")
        seg2 = struct.unpack(">H", cmap[off + 6:off + 8])[0]
        seg = seg2 // 2
        ends = struct.unpack(f">{seg}H", cmap[off + 14:off + 14 + seg2])
        starts = struct.unpack(f">{seg}H", cmap[off + 16 + seg2:off + 16 + 2 * seg2])
        deltas = struct.unpack(f">{seg}h", cmap[off + 16 + 2 * seg2:off + 16 + 3 * seg2])
        ro_pos = off + 16 + 3 * seg2
        ranges = struct.unpack(f">{seg}H", cmap[ro_pos:ro_pos + seg2])
        out = {}
        for i in range(seg):
            for c in range(starts[i], ends[i] + 1):
                if c == 0xFFFF:
                    continue
                if ranges[i] == 0:
                    g = (c + deltas[i]) & 0xFFFF
                else:
                    pos = ro_pos + 2 * i + ranges[i] + 2 * (c - starts[i])
                    g = struct.unpack(">H", cmap[pos:pos + 2])[0]
                    if g:
                        g = (g + deltas[i]) & 0xFFFF
                if g:
                    out[c] = g
        return out

    def _ps_name(self, name: bytes):
        count, str_off = struct.unpack(">HH", name[2:6])
        for i in range(count):
            pid, eid, _, nid, length, off = struct.unpack(">HHHHHH", name[6 + 12 * i:18 + 12 * i])
            if nid == 6:
                raw = name[str_off + off:str_off + off + length]
                return raw.decode("utf-16-be" if pid == 3 else "latin-1", "ignore")
        return None

    def glyph(self, ch: str) -> int:
        return self.cmap.get(ord(ch), 0)

    def supports(self, text: str) -> bool:
        return all(ord(c) in self.cmap for c in text)

    def width(self, text: str, size: float) -> float:
        return sum(self.advances[self.glyph(c)] for c in text) * size / self.units

    def _glyph_range(self, gid: int) -> tuple:
        loca = self.table("loca")
        if self.long_loca:
            a, b = struct.unpack(">II", loca[4 * gid:4 * gid + 8])
        else:
            a, b = (x * 2 for x in struct.unpack(">HH", loca[2 * gid:2 * gid + 4]))
        return a, b

    def subset(self, gids: set) -> bytes:
        """Той самий шрифт, але glyf містить лише потрібні гліфи (номери гліфів не змінюються)."""
        glyf = self.table("glyf")
        need, stack = {0}, list(gids)
        while stack:  # складені гліфи (напр. «й» = «и» + бреве) тягнуть свої частини
            g = stack.pop()
            if g in need or g >= self.num_glyphs:
                continue
            need.add(g)
            a, b = self._glyph_range(g)
            if b - a >= 10 and struct.unpack(">h", glyf[a:a + 2])[0] < 0:
                pos = a + 10
                while True:
                    flags, comp = struct.unpack(">HH", glyf[pos:pos + 4])
                    stack.append(comp)
                    pos += 4 + (4 if flags & 0x1 else 2)
                    pos += 8 if flags & 0x80 else 4 if flags & 0x40 else 2 if flags & 0x8 else 0
                    if not flags & 0x20:
                        break
        new_glyf, offsets = bytearray(), []
        for g in range(self.num_glyphs):
            offsets.append(len(new_glyf))
            if g in need:
                a, b = self._glyph_range(g)
                new_glyf += glyf[a:b]
                new_glyf += b"\0" * (-len(new_glyf) % 4)
        offsets.append(len(new_glyf))
        head = bytearray(self.table("head"))
        head[8:12] = b"\0\0\0\0"
        head[50:52] = struct.pack(">h", 1)
        post = self.table("post")[:32]
        tables = {"head": bytes(head), "hhea": self.table("hhea"), "maxp": self.table("maxp"),
                  "hmtx": self.table("hmtx"), "loca": struct.pack(f">{len(offsets)}I", *offsets),
                  "glyf": bytes(new_glyf), "post": b"\x00\x03\x00\x00" + post[4:32], "OS/2": self.table("OS/2")}
        for tag in ("cvt ", "fpgm", "prep"):
            if tag in self.tables:
                tables[tag] = self.table(tag)
        return _pack_font(tables)


def _checksum(data: bytes) -> int:
    data += b"\0" * (-len(data) % 4)
    return sum(struct.unpack(f">{len(data) // 4}I", data)) & 0xFFFFFFFF


def _pack_font(tables: dict) -> bytes:
    tags = sorted(tables)
    n = len(tags)
    es = n.bit_length() - 1
    header = struct.pack(">IHHHH", 0x00010000, n, 16 * 2 ** es, es, 16 * n - 16 * 2 ** es)
    offset = 12 + 16 * n
    records, body = b"", b""
    for tag in tags:
        data = tables[tag]
        records += struct.pack(">4sIII", tag.encode("latin-1"), _checksum(data), offset + len(body), len(data))
        body += data + b"\0" * (-len(data) % 4)
    font = bytearray(header + records + body)
    head_off = offset + sum(len(tables[t]) + (-len(tables[t]) % 4) for t in tags[:tags.index("head")])
    font[head_off + 8:head_off + 12] = struct.pack(">I", (0xB1B0AFBA - _checksum(bytes(font))) & 0xFFFFFFFF)
    return bytes(font)


# ---------- сторінка ----------

def _num(x: float) -> str:
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def _hex_color(color: str) -> str:
    color = color.lstrip("#")
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return f"{_num(r)} {_num(g)} {_num(b)}"


class Page:
    """Координати — в пунктах, початок у лівому верхньому куті (y униз), як в SVG."""

    def __init__(self, fonts: dict, size=A4):
        self.fonts = fonts  # {"regular": TrueTypeFont, "bold": TrueTypeFont}
        self.width, self.height = size
        self.ops = []
        self.used = {name: set() for name in fonts}

    def _y(self, y: float) -> float:
        return self.height - y

    def text(self, x: float, y: float, text: str, size=10, font="regular", color="#000000"):
        f = self.fonts[font]
        gids = [f.glyph(c) for c in text]
        self.used[font].update((g, c) for g, c in zip(gids, text) if g)
        hexs = "".join(f"{g:04X}" for g in gids)
        key = "F1" if font == "regular" else "F2"
        self.ops.append(f"BT {_hex_color(color)} rg /{key} {_num(size)} Tf {_num(x)} {_num(self._y(y))} Td "
                        f"<{hexs}> Tj ET")

    def text_width(self, text: str, size=10, font="regular") -> float:
        return self.fonts[font].width(text, size)

    def line(self, x1, y1, x2, y2, color="#000000", width=1.0, dash=None):
        d = f"[{' '.join(_num(v) for v in dash)}] 0 d " if dash else "[] 0 d "
        self.ops.append(f"{_hex_color(color)} RG {_num(width)} w {d}{_num(x1)} {_num(self._y(y1))} m "
                        f"{_num(x2)} {_num(self._y(y2))} l S")

    def polyline(self, points: list, color="#000000", width=1.5):
        if len(points) < 2:
            return
        path = f"{_num(points[0][0])} {_num(self._y(points[0][1]))} m " + " ".join(
            f"{_num(x)} {_num(self._y(y))} l" for x, y in points[1:])
        self.ops.append(f"{_hex_color(color)} RG {_num(width)} w [] 0 d 1 J 1 j {path} S")

    def rect(self, x, y, w, h, fill=None, stroke=None, width=0.5):
        op = "B" if fill and stroke else "f" if fill else "S"
        colors = (f"{_hex_color(fill)} rg " if fill else "") + (f"{_hex_color(stroke)} RG {_num(width)} w " if stroke else "")
        self.ops.append(f"{colors}[] 0 d {_num(x)} {_num(self._y(y + h))} {_num(w)} {_num(h)} re {op}")

    def circle(self, cx, cy, r, color="#000000", width=1.2):
        k = 0.5523 * r
        y = self._y(cy)
        self.ops.append(
            f"{_hex_color(color)} RG {_num(width)} w [] 0 d {_num(cx + r)} {_num(y)} m "
            f"{_num(cx + r)} {_num(y + k)} {_num(cx + k)} {_num(y + r)} {_num(cx)} {_num(y + r)} c "
            f"{_num(cx - k)} {_num(y + r)} {_num(cx - r)} {_num(y + k)} {_num(cx - r)} {_num(y)} c "
            f"{_num(cx - r)} {_num(y - k)} {_num(cx - k)} {_num(y - r)} {_num(cx)} {_num(y - r)} c "
            f"{_num(cx + k)} {_num(y - r)} {_num(cx + r)} {_num(y - k)} {_num(cx + r)} {_num(y)} c S")

    # ---------- збирання PDF ----------

    def to_pdf(self, title: str = "") -> bytes:
        objects = []

        def add(body) -> int:
            objects.append(body)
            return len(objects)

        font_refs = {}
        for key, name in (("F1", "regular"), ("F2", "bold")):
            f = self.fonts[name]
            used = dict(self.used[name])
            used.setdefault(f.glyph(" "), " ")
            scale = 1000 / f.units
            file_data = zlib.compress(f.subset(set(used)))
            ff = add(f"<< /Length {len(file_data)} /Filter /FlateDecode >>".encode() + b"\nstream\n" + file_data
                     + b"\nendstream")
            tag = "".join(chr(65 + (ord(c) + i) % 26) for i, c in enumerate((name + "subset")[:6]))
            base = f"{tag}+{f.ps_name}"
            desc = add(f"<< /Type /FontDescriptor /FontName /{base} /Flags 32 /FontBBox [{' '.join(_num(v * scale) for v in f.bbox)}] "
                       f"/ItalicAngle 0 /Ascent {_num(f.ascent * scale)} /Descent {_num(f.descent * scale)} "
                       f"/CapHeight {_num(f.cap_height * scale)} /StemV 80 /FontFile2 {ff} 0 R >>".encode())
            widths = " ".join(f"{g} [{_num(f.advances[g] * scale)}]" for g in sorted(used))
            cid = add(f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /{base} "
                      f"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
                      f"/FontDescriptor {desc} 0 R /CIDToGIDMap /Identity /DW 500 /W [{widths}] >>".encode())
            pairs = sorted(used.items())
            blocks = []
            for i in range(0, len(pairs), 100):
                chunk = pairs[i:i + 100]
                blocks.append(f"{len(chunk)} beginbfchar\n" + "\n".join(
                    f"<{g:04X}> <{''.join(f'{u:04X}' for u in _utf16(ch))}>" for g, ch in chunk) + "\nendbfchar")
            cmap = ("/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CIDSystemInfo << /Registry (Adobe) "
                    "/Ordering (UCS) /Supplement 0 >> def /CMapName /Adobe-Identity-UCS def /CMapType 2 def "
                    "1 begincodespacerange <0000> <FFFF> endcodespacerange\n" + "\n".join(blocks) +
                    "\nendcmap CMapName currentdict /CMap defineresource pop end end").encode()
            tu = add(f"<< /Length {len(cmap)} >>".encode() + b"\nstream\n" + cmap + b"\nendstream")
            font_refs[key] = add(f"<< /Type /Font /Subtype /Type0 /BaseFont /{base} /Encoding /Identity-H "
                                 f"/DescendantFonts [{cid} 0 R] /ToUnicode {tu} 0 R >>".encode())
        content = zlib.compress("\n".join(self.ops).encode("latin-1"))
        cont = add(f"<< /Length {len(content)} /Filter /FlateDecode >>".encode() + b"\nstream\n" + content
                   + b"\nendstream")
        pages_id = len(objects) + 2
        page = add(f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {_num(self.width)} {_num(self.height)}] "
                   f"/Resources << /Font << /F1 {font_refs['F1']} 0 R /F2 {font_refs['F2']} 0 R >> >> "
                   f"/Contents {cont} 0 R >>".encode())
        add(f"<< /Type /Pages /Kids [{page} 0 R] /Count 1 >>".encode())
        info = add(f"<< /Title <FEFF{''.join(f'{u:04X}' for ch in title for u in _utf16(ch))}> "
                   f"/Producer (wikipedia-interest-analysis) >>".encode())
        catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())

        out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objects, 1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
        out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
        out += (f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R /Info {info} 0 R >>\n"
                f"startxref\n{xref}\n%%EOF\n").encode()
        return bytes(out)


def _utf16(ch: str) -> list:
    data = ch.encode("utf-16-be")
    return [int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2)]
