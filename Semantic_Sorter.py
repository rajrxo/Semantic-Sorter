#Installing Dependencies if the user does not have
import sys
import subprocess
import importlib

REQUIRED_PACKAGES = {
    "sentence_transformers": "sentence-transformers",
    "sklearn": "scikit-learn",
    "numpy": "numpy",
    "PIL": "pillow",
    "pytesseract": "pytesseract",
    "pypdf": "pypdf",
    # clip stack
    "torch": "torch",
    "open_clip": "open_clip_torch",
    "transformers": "transformers",
    "accelerate": "accelerate",
}

def ensure_dependencies():
    missing = []

    for import_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    print(f"[Setup] Installing missing packages: {missing}")

    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            *missing
        ])
    except Exception as e:
        print(f"[Setup] Failed to install dependencies: {e}")
        sys.exit(1)

ensure_dependencies()


#import clip
import open_clip
import torch

print("loading clip model...")

CLIP_MODEL, _, CLIP_PREPROCESS = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained="openai"
)

CLIP_TOKENIZER = open_clip.get_tokenizer("ViT-B-32")

CLIP_MODEL.eval()




#import clip
from transformers import BlipProcessor, BlipForConditionalGeneration

print("loading blip caption model...")

BLIP_PROCESSOR = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

BLIP_MODEL = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

BLIP_MODEL.eval()



#shuts up the log unless something is really broken
import logging
logging.getLogger("pypdf").setLevel(logging.ERROR)






#ignores the script file if the user is dumb and did not move it to a separate folder

def should_ignore_file(filename):
    name = filename.lower()

    ignore_exact = {
        "semantic_sorter.py",
        "requirements.txt",
        "readme.md",
    }

    ignore_prefix = (
        ".semantic_sort_log_",
        ".",
    )

    ignore_suffix = (
        ".json",
        ".log",
    )

    # exact matches
    if name in ignore_exact:
        return True

    # hidden/system/log files
    if name.startswith(ignore_prefix):
        return True

    if name.endswith(ignore_suffix) and name.startswith(".semantic_sort"):
        return True

    return False






#this might take longer first time it runs so bear with it










# Check if OCR library is present if not then OCR will not work and absurd names will remain absurd

def check_tesseract():
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        print("[OCR] Tesseract engine not found. OCR features will be limited.")
        return False

TESSERACT_AVAILABLE = check_tesseract()









#Main Program begins here



#standard libraries to control files
import os
import sys
import shutil
#libraries to edit text and parsing
import re
import json
from datetime import datetime
from collections import Counter, defaultdict
import open_clip
import torch
# for runtime behavior
import warnings




try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity
    from PIL import Image
    import pytesseract
    from pypdf import PdfReader
    import numpy as np
except ImportError:
    print("Missing libs. Install:")
    print("pip install sentence-transformers scikit-learn numpy pillow pytesseract pypdf")
    sys.exit(1)

print("Loading NLP model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

DRY_RUN = "--dry-run" in sys.argv
UNDO_MODE = "--undo" in sys.argv
MOVE_LOG = []
LOG_FILENAME = None






#Tuning

MIN_PROJECT_FILES = 3
PROJECT_CONF_THRESHOLD = 0.35
ABSURD_RENAME_MINLEN = 6






#File Family..... add more extensions if necessary ,though ive tried to add more than youll ever need
IMAGE_EXTS = {
    '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp',
    '.heic', '.heif', '.tiff', '.tif', '.ico', '.avif'
}

DOCUMENT_EXTS = {
    '.pdf', '.txt', '.doc', '.docx', '.rtf', '.odt',
    '.ppt', '.pptx', '.key',
    '.xls', '.xlsx', '.csv',
    '.md', '.markdown',
    '.tex'
}

CAD_EXTS = {
    '.stl', '.step', '.stp', '.f3d', '.svg',
    '.obj', '.3mf', '.iges', '.igs',
    '.dwg', '.dxf'
}

CODE_EXTS = {
    '.py', '.cpp', '.c', '.h', '.hpp',
    '.js', '.ts', '.jsx', '.tsx',
    '.java', '.kt', '.go', '.rs',
    '.json', '.yaml', '.yml',
    '.html', '.css', '.scss',
    '.ipynb', '.sh', '.bash'
}

ARCHIVE_EXTS = {
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'
}

MEDIA_EXTS = {
    '.mp4', '.mov', '.mkv', '.avi', '.webm',
    '.mp3', '.wav', '.flac', '.aac', '.m4a'
}
def get_file_family(filename):
    ext = os.path.splitext(filename)[1].lower()

    if ext in IMAGE_EXTS:
        return "Images"
    if ext in DOCUMENT_EXTS:
        return "Documents"
    if ext in CAD_EXTS:
        return "CAD"
    if ext in CODE_EXTS:
        return "Code"
    if ext in ARCHIVE_EXTS:
        return "Archives"
    if ext in MEDIA_EXTS:
        return "Media"

    return "Other"









#Absurd name detector- it checks if the file names are not understandable
def semantic_name_strength(name):
    """
    Estimate how linguistically meaningful a filename is
    using the MiniLM embedding magnitude.

    Higher → more likely real human language
    Lower → more likely random / autogenerated
    """
    try:
        cleaned = re.sub(r'[_\-]', ' ', name.lower())
        cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned).strip()

        if not cleaned:
            return 0.0

        emb = model.encode([cleaned])[0]
        magnitude = float((emb ** 2).sum() ** 0.5)
        return magnitude

    except Exception:
        return 0.0


def is_filename_absurd(name):
    """
    Decide whether a filename is likely junk.

    Strategy:
    1) Catch obvious generator patterns (fast regex)
    2) Catch ultra-short garbage
    3) Use semantic strength as a soft AI signal
    """

    name = name.lower().strip()

    # Obvious junk
    patterns = [
        # screenshots & captures
        r'^screenshot',
        r'^screen[\s\-_]?shot',

        # common camera dumps
        r'^img[_\-]?\d+',
        r'^dsc[_\-]?\d+',
        r'^pxl[_\-]?\d+',
        r'^vid[_\-]?\d+',

        # whatsapp spam
        r'^whatsapp\s?image',
        r'^whatsapp\s?video',

        # generic garbage names
        r'^image$',
        r'^untitled',
        r'^scan[_\-]?\d*',
        r'^document[_\-]?\d*',
        r'^file[_\-]?\d*',

        # mostly numeric
        r'^\d{4,}$',
        r'^[a-z]*\d{6,}$',
    ]

    if any(re.search(p, name) for p in patterns):
        return True

    #very weak structure
    cleaned = re.sub(r'[^a-z0-9]', '', name)

    #very short names
    if len(cleaned) <= 3:
        return True

    #AI semantic sanity check
    strength = semantic_name_strength(name)

    # Conservative threshold, tinker if needed
    if strength < 3.2:
        return True

    #safe default
    return False








# OCR

def try_ocr_extract(filepath):
    # check if Tesseract is available
    if not TESSERACT_AVAILABLE:
        return ""

    try:
        with Image.open(filepath) as img:

            # quick size guard
            if img.width < 200 or img.height < 200:
                return ""

            #normalize image
            img = img.convert("L")  # grayscale improves OCR

            #  run OCR
            text = pytesseract.image_to_string(
                img,
                config="--psm 6"
            )

            #  clean output
            text = re.sub(r'\s+', ' ', text).strip()

            # ignore very weak OCR
            if len(text) < 10:
                return ""

            return text[:200]

    except Exception:
        return ""








#extract clip tags
def extract_clip_tags(filepath):
    try:
        img = Image.open(filepath).convert("RGB")
        image = CLIP_PREPROCESS(img).unsqueeze(0)

        labels = [
            "desktop ui screenshot",
            "mobile app screenshot",
            "computer software window",
            "cad model",
            "3d render",
            "robot",
            "circuit board",
            "electronic hardware",
            "diagram",
            "chart or graph",
            "document page",
            "text screenshot",
            "person photo",
            "device photo",
            "dark image",
            "bright image"
        ]

        text_tokens = CLIP_TOKENIZER(labels)

        with torch.no_grad():
            image_features = CLIP_MODEL.encode_image(image)
            text_features = CLIP_MODEL.encode_text(text_tokens)

            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            similarity = (image_features @ text_features.T).softmax(dim=-1)
            best_idx = similarity.argmax().item()

        return labels[best_idx]

    except Exception as e:
        print(f"[clip error] {e}")
        return ""






#extract blip tags
def extract_blip_caption(filepath):
    try:
        image = Image.open(filepath).convert("RGB")

        inputs = BLIP_PROCESSOR(images=image, return_tensors="pt")

        with torch.no_grad():
            out = BLIP_MODEL.generate(**inputs, max_new_tokens=30)

        caption = BLIP_PROCESSOR.decode(out[0], skip_special_tokens=True)
        return caption.lower()

    except Exception as e:
        print(f"[blip error] {e}")
        return ""







#extract image hints
def extract_image_hints(filepath):
    try:
        img = Image.open(filepath)
        w, h = img.size

        hints = []

        ratio = w / h if h != 0 else 0
        if 1.6 < ratio < 1.9:
            hints.append("widescreen")
        if w >= 1900 and h >= 1000:
            hints.append("highres")

        if h > w * 1.3:
            hints.append("mobile")

        gray = img.convert("L")
        avg = np.array(gray).mean()
        if avg < 60:
            hints.append("dark")
        elif avg > 190:
            hints.append("bright")

        return " ".join(hints)

    except Exception:
        return ""











# PDF Extractor
def try_pdf_extract(filepath):
    try:
        # tolerant reader for messy real-world PDFs
        reader = PdfReader(filepath, strict=False)

        text_chunks = []
        char_count = 0
        MAX_CHARS = 800  # soft cap for embedding usefulness

        # read up to first few pages safely
        max_pages = min(6, len(reader.pages))

        for i in range(max_pages):
            try:
                page = reader.pages[i]
                t = page.extract_text()
            except Exception:
                t = None

            if not t:
                continue

            t = re.sub(r'\s+', ' ', t).strip()

            # ignore weak garbage text
            if len(t) < 20:
                continue

            text_chunks.append(t)
            char_count += len(t)

            # early exit when enough signal collected
            if char_count >= MAX_CHARS:
                break

        if not text_chunks:
            return ""

        text = " ".join(text_chunks).strip()
        return text[:800]

    except Exception:
        return ""











# Build semantic text
def build_semantic_text(filename, full_path):
    try:
        base = os.path.splitext(filename)[0].lower()
        ext = os.path.splitext(filename)[1].lower()

        # stronger filename normalization
        base = re.sub(r'[_\-]', ' ', base)
        base = re.sub(r'\d{4}[-_]\d{2}[-_]\d{2}', ' ', base)  # dates
        base = re.sub(r'\bwa\d+\b', ' ', base)                # WA0001 junk
        base = re.sub(r'\bimg\d+\b', ' ', base)
        base = re.sub(r'\s+', ' ', base).strip()

        extra_text = ""

        #  PDF enrichment
        if ext == ".pdf":
            pdf_text = try_pdf_extract(full_path)
            if isinstance(pdf_text, str) and pdf_text.strip():
                extra_text = pdf_text.lower()

        #  smart OCR trigger
        elif ext in {'.png', '.jpg', '.jpeg', '.webp'}:

            base_clean = re.sub(r'[^a-z0-9]', '', base)

            hints = extract_image_hints(full_path) or "image content"
            clip_tags = extract_clip_tags(full_path)
            blip_caption = extract_blip_caption(full_path)

            print(f"[debug] {filename} -> hints: {hints} | clip: {clip_tags} | blip: {blip_caption}")

            extra_parts = []

            #tags from blip
            if blip_caption:
                extra_parts.append(blip_caption)

            # always add hints (cheap signal)
            if hints:
                extra_parts.append(hints)

            # add clip understanding (main visual brain)
            if clip_tags:
                extra_parts.append(clip_tags)

            # OCR only when needed
            if is_filename_absurd(base) or len(base_clean) < 8:
                ocr = try_ocr_extract(full_path)
                if isinstance(ocr, str) and len(ocr.strip()) > 10:
                    extra_parts.append(ocr.lower())

            extra_text = " ".join(extra_parts).strip()

        #  semantic hint boost
        if any(w in base for w in ["screenshot", "screen", "capture"]):
            base += " captured screen content"

        combined = (base + " " + extra_text).strip()

        if not isinstance(combined, str) or not combined:
            return base if base else filename.lower()

        return combined[:2000]

    except Exception:
        return os.path.splitext(filename)[0].lower()












# Safe Rename
def build_safe_filename(original_file, semantic_text):
    ext = os.path.splitext(original_file)[1].lower()

    if not semantic_text:
        return original_file

    text = semantic_text.lower()

    # remove very common junk tokens
    stop_words = {
        "the","a","an","this","that","with","and","for",
        "image","photo","picture","screenshot","captured",
        "screen","content"
    }

    words = re.findall(r'[a-z0-9]+', text)

    # filter meaningful words
    good_words = [
        w for w in words
        if w not in stop_words
        and len(w) >= 3
        and not w.isdigit()
    ]

    # fallback if filtering too aggressive
    if len(good_words) < 2:
        good_words = [w for w in words if len(w) >= 3]

    if not good_words:
        return original_file

    candidate = "_".join(good_words[:6]).strip("_")

    # final safety
    if len(candidate) < ABSURD_RENAME_MINLEN:
        return original_file

    return candidate + ext








# Folder naming
def generate_folder_name(filenames):
    words = []

    stop_words = {
        # common noise
        'the','a','in','and','for','to','of',
        'script','file','test','main','code','data',
        'captured','screen','photo','whatsapp',
        'image','img','copy','final','new','draft',
        'version','ver','v1','v2','v3'
    }

    for f in filenames:
        base = os.path.splitext(f)[0].lower()
        base = re.sub(r'[_\-]', ' ', base)

        tokens = [
            w for w in base.split()
            if w not in stop_words and len(w) > 2
        ]

        words.extend(tokens)

    if not words:
        return "Mixed_Files"

    counts = Counter(words)
    most_common = counts.most_common(3)

    #  confidence guard
    if most_common[0][1] < 2:
        return "Mixed_Files"

    #  choose 1 or 2 keywords intelligently
    top_words = [most_common[0][0]]

    if len(most_common) > 1 and most_common[1][1] >= 2:
        top_words.append(most_common[1][0])

    #  clean formatting
    name = "_".join(top_words)
    name = name[:40].strip("_")

    return f"{name.title()}_Project"








# measure how tight a cluster is based on average cosine similarity
def cluster_confidence(indices, embeddings):
    if len(indices) < 2:
        return 0.0

    vecs = embeddings[indices]
    sim_matrix = cosine_similarity(vecs)

    n = len(indices)

    # remove self similarity from the sum
    pairwise_sum = sim_matrix.sum() - n

    # number of unique pairs
    num_pairs = n * (n - 1)

    if num_pairs == 0:
        return 0.0

    score = pairwise_sum / num_pairs

    # clamp for numerical safety
    score = max(0.0, min(1.0, float(score)))

    return score





# undo the most recent sorting operation using the saved log
def undo_last_run(target_dir):
    try:
        logs = [
            f for f in os.listdir(target_dir)
            if f.startswith(".semantic_sort_log_") and f.endswith(".json")
        ]
    except Exception:
        print("could not read target directory for undo")
        return

    if not logs:
        print("no log files found to undo")
        print("make sure you previously ran without --dry-run")
        return

    logs.sort(reverse=True)
    log_path = os.path.join(target_dir, logs[0])

    print(f"reverting using: {logs[0]}")

    try:
        with open(log_path, "r") as f:
            moves = json.load(f)
    except Exception as e:
        print(f"failed to read log: {e}")
        return

    restored = 0
    skipped = 0

    # move files back in reverse order
    for entry in reversed(moves):
        src = entry.get("src")
        dst = entry.get("dst")

        if not src or not dst:
            skipped += 1
            continue

        if not os.path.exists(dst):
            skipped += 1
            continue

        try:
            os.makedirs(os.path.dirname(src), exist_ok=True)

            # avoid overwriting if something already exists there
            if os.path.exists(src):
                skipped += 1
                continue

            shutil.move(dst, src)
            restored += 1

        except Exception as e:
            print(f"[warn] failed to restore {dst}: {e}")
            skipped += 1

    # optional cleanup: remove empty folders created during sort
    try:
        for root, dirs, files in os.walk(target_dir, topdown=False):
            if root == target_dir:
                continue
            if not dirs and not files:
                try:
                    os.rmdir(root)
                except Exception:
                    pass
    except Exception:
        pass

    print(f"undo complete. restored {restored} files, skipped {skipped}")








#main sort
def sort_directory(target_dir):
    global LOG_FILENAME

    if not os.path.isdir(target_dir):
        print("invalid directory")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_FILENAME = os.path.join(
        target_dir,
        f".semantic_sort_log_{timestamp}.json"
    )

    all_files = [
        f for f in os.listdir(target_dir)
        if os.path.isfile(os.path.join(target_dir, f))
        and not should_ignore_file(f)
    ]

    print(f"found {len(all_files)} files")

    families = defaultdict(list)
    for f in all_files:
        families[get_file_family(f)].append(f)

    for family, files in families.items():
        if not files:
            continue

        print(f"\nprocessing {family} ({len(files)} files)")

        family_root = os.path.join(target_dir, family)

        if not DRY_RUN:
            os.makedirs(family_root, exist_ok=True)

        # fast path for very small families
        if len(files) <= 2:
            for file in files:
                src = os.path.join(target_dir, file)

                base_name = os.path.splitext(file)[0]
                new_name = file

                base_clean = re.sub(r'[^a-z0-9]', '', base_name.lower())

                should_rename = (
                        is_filename_absurd(base_name)
                        or "screenshot" in base_name.lower()
                        or "screen" in base_name.lower()
                        or base_name.lower().startswith("img")
                        or base_name.lower().startswith("wa")
                        or len(base_clean) < 8
                )

                if should_rename:
                    semantic_hint = build_semantic_text(file, src)
                    new_name = build_safe_filename(file, semantic_hint)

                dst = os.path.join(family_root, new_name)

                counter = 1
                base_dst, ext = os.path.splitext(dst)
                while os.path.exists(dst):
                    dst = f"{base_dst}_{counter}{ext}"
                    counter += 1

                if DRY_RUN:
                    print(f"[dry run] {file} -> {family_root}")
                else:
                    shutil.move(src, dst)
                    MOVE_LOG.append({"src": src, "dst": dst})

            continue

        semantic_texts = [
            build_semantic_text(f, os.path.join(target_dir, f))
            for f in files
        ]

        safe_texts = []
        for idx, t in enumerate(semantic_texts):
            try:
                if not isinstance(t, str):
                    t = str(t)

                t = t.replace("\x00", " ")
                t = re.sub(r'\s+', ' ', t).strip()

                if not t:
                    t = f"misc file {idx}"

                t = t[:1000]

            except Exception:
                t = f"misc file {idx}"

            safe_texts.append(t)

        semantic_texts = safe_texts

        try:
            embeddings = model.encode(semantic_texts, show_progress_bar=False)
        except Exception as e:
            print(f"[warn] batch encode failed, falling back per file: {e}")

            safe_embeddings = []
            for text in semantic_texts:
                try:
                    emb = model.encode([text])[0]
                except Exception:
                    emb = model.encode(["misc file"])[0]
                safe_embeddings.append(emb)

            embeddings = np.array(safe_embeddings)

        sim_matrix = cosine_similarity(embeddings)

        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric='precomputed',
            linkage='average',
            distance_threshold=0.35
        )

        labels = clustering.fit_predict(1 - sim_matrix)

        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            clusters[label].append(idx)

        for label, indices in clusters.items():
            conf = cluster_confidence(indices, embeddings)
            cluster_files = [files[i] for i in indices]

            make_project = (
                len(indices) >= MIN_PROJECT_FILES
                and conf >= PROJECT_CONF_THRESHOLD
            )

            if make_project:
                folder_name = generate_folder_name(cluster_files)
                dest_base = os.path.join(family_root, folder_name)
                if not DRY_RUN:
                    os.makedirs(dest_base, exist_ok=True)
            else:
                dest_base = family_root

            for i in indices:
                file = files[i]
                src = os.path.join(target_dir, file)

                base_name = os.path.splitext(file)[0]
                new_name = file

                if is_filename_absurd(base_name):
                    new_name = build_safe_filename(file, semantic_texts[i])

                dst = os.path.join(dest_base, new_name)

                counter = 1
                base_dst, ext = os.path.splitext(dst)
                while os.path.exists(dst):
                    dst = f"{base_dst}_{counter}{ext}"
                    counter += 1

                if DRY_RUN:
                    print(f"[dry run] {file} -> {dest_base}")
                else:
                    shutil.move(src, dst)
                    MOVE_LOG.append({"src": src, "dst": dst})

    if not DRY_RUN and MOVE_LOG:
        try:
            with open(LOG_FILENAME, "w") as f:
                json.dump(MOVE_LOG, f, indent=2)
            print(f"move log saved: {os.path.basename(LOG_FILENAME)}")
        except Exception as e:
            print(f"[warn] failed to save move log: {e}")

    print("\nsemantic sorting complete")








# entry point for command line usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage:")
        print("  python semantic_sorter.py <folder> [--dry-run]")
        print("  python semantic_sorter.py <folder> --undo")
        sys.exit(1)

    target = os.path.abspath(sys.argv[1])

    if not os.path.exists(target):
        print("target path does not exist")
        sys.exit(1)

    if not os.path.isdir(target):
        print("target must be a directory")
        sys.exit(1)

    # prevent weird user behavior
    if UNDO_MODE and DRY_RUN:
        print("cannot use --undo and --dry-run together")
        sys.exit(1)

    if UNDO_MODE:
        undo_last_run(target)
    else:
        sort_directory(target)
