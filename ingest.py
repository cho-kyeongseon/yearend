"""연말정산 자료(PDF·HWP·ZIP)를 읽어 검색용 청크(index/chunks.json)로 만든다.

사용법:  .venv\\Scripts\\python.exe ingest.py
폴더에 자료를 추가하면 다시 실행하면 된다.
"""
from __future__ import annotations

import json
import re
import struct
import zipfile
import zlib
from pathlib import Path

import fitz  # PyMuPDF
import olefile

ROOT = Path(__file__).resolve().parent
EXTRACT_DIR = ROOT / "data" / "extracted"
INDEX_FILE = ROOT / "index" / "chunks.json"
CHUNK_CHARS = 1200
OVERLAP = 200


# ---------------------------------------------------------------- ZIP
def _zip_name(info: zipfile.ZipInfo) -> str:
    """한국어 zip 파일명(cp949) 복원."""
    if info.flag_bits & 0x800:  # UTF-8 플래그
        return info.filename
    try:
        return info.filename.encode("cp437").decode("cp949")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return info.filename


def extract_zips() -> None:
    for zp in ROOT.glob("*.zip"):
        dest = EXTRACT_DIR / zp.stem
        if dest.exists():
            continue
        with zipfile.ZipFile(zp) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = _zip_name(info)
                target = (dest / name).resolve()
                if not target.is_relative_to(dest.resolve()):  # 경로 탈출 방지
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(info))
        print(f"[zip] {zp.name} -> {dest.relative_to(ROOT)}")


# ---------------------------------------------------------------- HWP (5.0 바이너리)
def _decode_para_text(b: bytes) -> str:
    chars = struct.unpack(f"<{len(b) // 2}H", b[: len(b) // 2 * 2])
    out, i = [], 0
    while i < len(chars):
        c = chars[i]
        if c < 32:
            if c in (10, 13):
                out.append("\n")
            elif c == 9:
                out.append(" ")
            # 문자 컨트롤(1칸): 0,10,13,24~31 / 인라인·확장 컨트롤(8칸): 나머지
            i += 1 if (c in (0, 10, 13) or 24 <= c <= 31) else 8
            continue
        out.append(chr(c))
        i += 1
    return "".join(out)


def hwp_text(path: Path) -> str:
    with olefile.OleFileIO(str(path)) as ole:
        flags = ole.openstream("FileHeader").read()[36]
        compressed, encrypted, distributed = flags & 1, flags & 2, flags & 4
        if encrypted or distributed:
            raise ValueError("암호화/배포용 문서라 본문을 읽을 수 없음")
        sections = sorted(
            (e for e in ole.listdir() if e[0] == "BodyText"),
            key=lambda e: int(re.sub(r"\D", "", e[1]) or 0),
        )
        paras: list[str] = []
        for sec in sections:
            data = ole.openstream(sec).read()
            if compressed:
                data = zlib.decompress(data, -15)
            i = 0
            while i + 4 <= len(data):
                header = struct.unpack_from("<I", data, i)[0]
                i += 4
                tag, size = header & 0x3FF, (header >> 20) & 0xFFF
                if size == 0xFFF:
                    size = struct.unpack_from("<I", data, i)[0]
                    i += 4
                if tag == 67:  # HWPTAG_PARA_TEXT
                    paras.append(_decode_para_text(data[i : i + size]))
                i += size
    return "\n".join(p.strip() for p in paras if p.strip())


# ---------------------------------------------------------------- 청크
def _clean(text: str) -> str:
    text = re.sub(r"[ \t　]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def _split(text: str) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    parts, start = [], 0
    while start < len(text):
        parts.append(text[start : start + CHUNK_CHARS])
        start += CHUNK_CHARS - OVERLAP
    return parts


def pdf_chunks(path: Path, source: str) -> list[dict]:
    chunks = []
    with fitz.open(path) as doc:
        for pno, page in enumerate(doc, start=1):
            text = _clean(page.get_text())
            if len(text) < 30:
                continue
            for part in _split(text):
                chunks.append({"source": source, "loc": f"{pno}쪽", "text": part})
    return chunks


def hwp_chunks(path: Path, source: str) -> list[dict]:
    text = _clean(hwp_text(path))
    return [
        {"source": source, "loc": f"부분 {i}", "text": part}
        for i, part in enumerate(_split(text), start=1)
        if len(part) >= 30
    ]


def main() -> None:
    extract_zips()
    # 프로젝트 폴더 최상위 + zip을 푼 폴더만 대상으로 한다
    candidates = list(ROOT.glob("*")) + list(EXTRACT_DIR.rglob("*"))
    files = sorted(p for p in candidates if p.is_file() and p.suffix.lower() in (".pdf", ".hwp"))
    chunks: list[dict] = []
    for p in files:
        source = p.stem
        try:
            new = pdf_chunks(p, source) if p.suffix.lower() == ".pdf" else hwp_chunks(p, source)
        except Exception as e:  # 한 파일이 실패해도 계속
            print(f"[skip] {p.name}: {e}")
            continue
        print(f"[ok]  {p.name}: {len(new)}개 청크")
        chunks.extend(new)

    for i, c in enumerate(chunks):
        c["id"] = i
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    print(f"\n총 {len(files)}개 파일, {len(chunks)}개 청크 -> {INDEX_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
