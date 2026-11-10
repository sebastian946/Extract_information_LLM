"""Genera archivos de prueba en la carpeta files/: sample.txt, sample.png y sample.pdf."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FILES = Path(__file__).resolve().parent.parent / "files"
FILES.mkdir(exist_ok=True)

TXT_CONTENT = """ACTA DE REUNION - COMITE DE PROYECTO ALFA

Fecha: 15 de marzo de 2026
Lugar: Sala 3, oficina principal
Autor: Maria Gonzalez (Gerente de Proyecto)

Asistentes:
- Maria Gonzalez
- Carlos Ramirez
- Ana Torres
- Luis Fernandez

Resumen:
Se reviso el avance del Proyecto Alfa, que esta en un 70% de ejecucion.
Se aprobo extender el plazo de entrega hasta el 30 de abril de 2026.
Carlos Ramirez coordina las pruebas finales y Ana Torres la documentacion.

Presupuesto aprobado: 45.000 USD
Proxima reunion: 29 de marzo de 2026
"""

PNG_LINES = [
    "INVOICE #2026-0042",
    "Date: 2026-02-10",
    "Vendor: Acme Supplies Inc.",
    "Customer: John Smith",
    "Item: Office chairs x 12",
    "Total: 3,600 USD",
    "Due date: 2026-03-10",
]

PDF_LINES = [
    "TECHNICAL REPORT: SOLAR PANEL EFFICIENCY STUDY",
    "Date: 2026-01-22",
    "Authors: Laura Perez, Daniel Ortiz",
    "Organization: GreenTech Research Lab",
    "Summary: This report evaluates the efficiency of three solar panel",
    "models under real conditions during a six-month period.",
    "Average efficiency measured: 21.4 percent",
    "Budget: 120,000 USD",
]


def make_txt():
    (FILES / "sample.txt").write_text(TXT_CONTENT, encoding="utf-8")


def make_png():
    img = Image.new("RGB", (900, 420), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default(size=32)
    y = 30
    for line in PNG_LINES:
        draw.text((40, y), line, fill="black", font=font)
        y += 52
    img.save(FILES / "sample.png")


def make_pdf():
    """Escribe un PDF minimo de dos paginas con texto real (extraible), sin dependencias extra."""
    def page_stream(lines):
        content = ["BT", "/F1 12 Tf", "50 750 Td", "16 TL"]
        for line in lines:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content.append(f"({safe}) Tj T*")
        content.append("ET")
        return "\n".join(content).encode("latin-1")

    pages = [PDF_LINES[:4], PDF_LINES[4:]]
    objects = []  # cada entrada es bytes del cuerpo del objeto, sin cabecera

    # 1: catalog, 2: pages, 3: font, luego pares (page, content)
    kids = " ".join(f"{4 + i * 2} 0 R" for i in range(len(pages)))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i, lines in enumerate(pages):
        page_num = 4 + i * 2
        stream = page_stream(lines)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {page_num + 1} 0 R >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    (FILES / "sample.pdf").write_bytes(out)


if __name__ == "__main__":
    make_txt()
    make_png()
    make_pdf()
    for f in sorted(FILES.iterdir()):
        print(f"created {f} ({f.stat().st_size} bytes)")
