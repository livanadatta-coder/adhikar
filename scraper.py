"""
scraper.py — Phase 1, Week 1
Fetches Police/FIR legal content from NYAAYA.org and saves as JSON.

If a URL fails (rate-limit, network), falls back to seeded legal text
so your pipeline always has something to work with from day one.

Run: python scraper.py
Output: corpus/raw/*.json
"""

import json
import time
import requests
import trafilatura
from pathlib import Path
from datetime import date

RAW_DIR = Path("corpus/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── URLs to scrape ─────────────────────────────────────────────────────────────
# NYAAYA has plain-language summaries — ideal for our use case.
# IndianKanoon has primary source text — use for section citations.
SOURCES = [
    {
        "url": "https://nyaaya.org/legal-explainer/what-are-my-rights-when-arrested/",
        "domain": "police_fir",
        "act": "CrPC",
        "section": "41",
        "title": "Rights when arrested - NYAAYA",
        "filename": "nyaaya_arrest_rights.json"
    },
    {
        "url": "https://nyaaya.org/legal-explainer/what-is-an-fir/",
        "domain": "police_fir",
        "act": "CrPC",
        "section": "154",
        "title": "What is an FIR - NYAAYA",
        "filename": "nyaaya_fir.json"
    },
    {
        "url": "https://nyaaya.org/legal-explainer/police-powers-of-arrest/",
        "domain": "police_fir",
        "act": "CrPC",
        "section": "41A",
        "title": "Police powers of arrest - NYAAYA",
        "filename": "nyaaya_police_powers.json"
    },
]

# ── Fallback seed data (used if scraping fails) ────────────────────────────────
# This is real legal content based on CrPC and D.K. Basu guidelines.
# It gives you a working corpus even before scraping succeeds.
SEED_DATA = [
    {
        "domain": "police_fir",
        "act": "CrPC",
        "section": "41",
        "title": "When police may arrest without warrant",
        "text": (
            "Under Section 41 of the Code of Criminal Procedure (CrPC), a police officer may arrest "
            "a person without a warrant only in specific circumstances. These include: when the person "
            "has committed a cognisable offence, when a reasonable complaint has been made or credible "
            "information has been received, or when the person is found in possession of an implement "
            "for housebreaking. The police officer must have a reasonable satisfaction that the arrest "
            "is necessary to prevent the person from committing further offences, for proper investigation, "
            "to prevent the person from tampering with evidence, or to ensure their presence in court. "
            "Importantly, the officer must record reasons in writing before making an arrest. If you are "
            "arrested without a warrant, you have the right to ask the officer to state and record the "
            "specific reason for your arrest."
        ),
        "source": "CrPC Section 41 / NYAAYA",
        "filename": "seed_crpc_41.json"
    },
    {
        "domain": "police_fir",
        "act": "CrPC",
        "section": "41A",
        "title": "Notice of appearance before police officer",
        "text": (
            "Section 41A CrPC requires the police to issue a notice to appear before them instead of "
            "making an arrest, in cases where arrest is not required under Section 41. If you receive "
            "a Section 41A notice, you are not under arrest. You are legally required to appear before "
            "the officer on the specified date. Failure to comply with a 41A notice can lead to arrest. "
            "This provision was introduced to reduce unnecessary arrests. If police arrive at your home "
            "and want to take you to the station for questioning but do not have a warrant, they should "
            "issue a 41A notice rather than arrest you. You can comply with the notice voluntarily. "
            "If they attempt an arrest without following Section 41 conditions, this is an illegal arrest."
        ),
        "source": "CrPC Section 41A / NYAAYA",
        "filename": "seed_crpc_41a.json"
    },
    {
        "domain": "police_fir",
        "act": "CrPC",
        "section": "50",
        "title": "Right to be informed of grounds of arrest",
        "text": (
            "Section 50 CrPC states that every person arrested without warrant must be informed "
            "immediately of the full particulars of the offence for which they are arrested, or other "
            "grounds for the arrest. This is a fundamental right. The police cannot refuse to tell you "
            "why you are being arrested. If they refuse, the arrest may be challenged in court as illegal. "
            "Additionally, if you are arrested for a bailable offence, the police must inform you of "
            "your right to bail immediately. You do not have to wait in custody while police decide "
            "whether to grant bail for a bailable offence — it is your right."
        ),
        "source": "CrPC Section 50",
        "filename": "seed_crpc_50.json"
    },
    {
        "domain": "police_fir",
        "act": "Constitution of India",
        "section": "Article 22",
        "title": "Constitutional rights on arrest and detention",
        "text": (
            "Article 22 of the Constitution of India guarantees fundamental rights to every arrested "
            "person. These rights are: (1) The right to be informed of the grounds of arrest as soon "
            "as possible. (2) The right to consult and be defended by a legal practitioner of your choice. "
            "This means you can call a lawyer immediately after arrest — the police cannot deny this. "
            "(3) The right to be produced before the nearest magistrate within 24 hours of arrest, "
            "excluding travel time. The police cannot hold you beyond 24 hours without a magistrate's "
            "order. (4) The right not to be detained beyond 24 hours without a magistrate's authority. "
            "These are constitutional rights — they cannot be waived away even by a senior police officer. "
            "If any of these rights are violated, you can file a habeas corpus petition in the High Court."
        ),
        "source": "Constitution of India, Article 22",
        "filename": "seed_constitution_22.json"
    },
    {
        "domain": "police_fir",
        "act": "D.K. Basu Guidelines",
        "section": "Supreme Court Guidelines",
        "title": "D.K. Basu guidelines on custodial rights",
        "text": (
            "In D.K. Basu v. State of West Bengal (1997), the Supreme Court of India laid down mandatory "
            "guidelines for all arrests. These guidelines have the force of law. Key requirements: "
            "(1) The arresting officer must carry an accurate, visible and clear identification with name "
            "and designation. (2) A memo of arrest must be prepared at the time of arrest, witnessed by "
            "a family member or a respectable person from the locality, and countersigned by the arrested "
            "person. (3) The person arrested must be allowed to inform a friend, relative, or well-wisher "
            "of their arrest and the place of detention as soon as possible. (4) An entry must be made in "
            "the diary at the place of detention regarding the arrest and the name of the person who has "
            "been informed. (5) The arrested person may, if they so request, be examined at the time of "
            "arrest and any injuries noted in the register. (6) The arrested person must be produced before "
            "the magistrate within 24 hours."
        ),
        "source": "D.K. Basu v. State of West Bengal, AIR 1997 SC 610",
        "filename": "seed_dk_basu.json"
    },
    {
        "domain": "police_fir",
        "act": "CrPC",
        "section": "154",
        "title": "First Information Report (FIR) - your right to file one",
        "text": (
            "Section 154 CrPC governs the First Information Report (FIR). An FIR is the document that "
            "sets the criminal justice process in motion. Key rights: (1) Every person has the right to "
            "file an FIR for a cognisable offence. The police cannot refuse to register an FIR for a "
            "cognisable offence. (2) If the police refuse to register your FIR, you can send the "
            "information in writing and by post to the Superintendent of Police under Section 154(3). "
            "The SP can then investigate or direct a subordinate officer to investigate. (3) You can also "
            "file a complaint directly before a magistrate under Section 156(3), who can order the police "
            "to register an FIR. (4) The FIR must be read to you before you sign it. You have the right "
            "to receive a free copy of the FIR. If police deny you a copy, this is a violation of your rights. "
            "Common cognisable offences include: theft, robbery, murder, rape, kidnapping, dacoity."
        ),
        "source": "CrPC Section 154",
        "filename": "seed_crpc_154.json"
    },
    {
        "domain": "police_fir",
        "act": "CrPC",
        "section": "167",
        "title": "Custody and bail — police remand limits",
        "text": (
            "Section 167 CrPC governs how long police can hold you in custody during investigation. "
            "The police can seek remand (custody) from a magistrate for up to 15 days total in police "
            "custody. After 15 days, you must be in judicial custody (jail), not police custody. "
            "The total maximum period of detention during investigation is 60 days for offences "
            "punishable with death, life imprisonment, or imprisonment for 10+ years. For other offences, "
            "the limit is 90 days. If the charge sheet is not filed within these periods, you are entitled "
            "to bail as a matter of right under Section 167(2) — this is called 'default bail' or "
            "'statutory bail'. You must apply for it; the court will grant it. This is an important "
            "protection against indefinite detention without trial."
        ),
        "source": "CrPC Section 167",
        "filename": "seed_crpc_167.json"
    },
    {
        "domain": "police_fir",
        "act": "CrPC",
        "section": "436-437",
        "title": "Bail rights — bailable and non-bailable offences",
        "text": (
            "Bail is the temporary release of an accused person in exchange for a security. There are "
            "two types: (1) Bailable offences (Section 436 CrPC): If you are arrested for a bailable "
            "offence, bail is your right. The police cannot refuse bail for a bailable offence. You "
            "simply provide a surety (someone who vouches for you) or a personal bond. A list of "
            "bailable offences is in the First Schedule of CrPC. (2) Non-bailable offences (Section 437): "
            "Bail is at the court's discretion. The court considers factors like flight risk, evidence "
            "tampering risk, and gravity of the offence. You have the right to apply for bail before "
            "any court. The police cannot permanently deny bail — even in serious cases, you can apply "
            "to the Sessions Court or High Court. For juveniles and women accused of non-bailable offences, "
            "bail must be given unless there are reasonable grounds to believe they are guilty of an offence "
            "punishable with death or life imprisonment."
        ),
        "source": "CrPC Sections 436-437",
        "filename": "seed_crpc_bail.json"
    },
]


def scrape_url(url: str) -> str | None:
    """Attempt to scrape text from a URL using trafilatura."""
    try:
        print(f"  Scraping: {url}")
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_tables=True)
            return text
    except Exception as e:
        print(f"  Failed to scrape {url}: {e}")
    return None


def save_doc(data: dict, filename: str):
    path = RAW_DIR / filename
    data["scraped_at"] = str(date.today())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ Saved: {filename}")


def run():
    print("\n=== ADHIKAR SCRAPER — Phase 1 ===\n")

    # Step 1: Write seed data first (guaranteed to work)
    print("Writing seed legal data (always works offline)...")
    for doc in SEED_DATA:
        filename = doc.pop("filename")
        save_doc(doc, filename)

    print(f"\n✓ {len(SEED_DATA)} seed documents written to corpus/raw/\n")

    # Step 2: Try live scraping (best-effort)
    print("Attempting live scrape from NYAAYA (may fail — that's OK)...")
    scraped = 0
    for source in SOURCES:
        time.sleep(2)  # Be polite to NYAAYA's servers
        text = scrape_url(source["url"])
        if text and len(text) > 200:
            doc = {
                "domain": source["domain"],
                "act": source["act"],
                "section": source["section"],
                "title": source["title"],
                "text": text,
                "source": source["url"],
            }
            save_doc(doc, source["filename"])
            scraped += 1
        else:
            print(f"  Skipped (no content): {source['filename']}")

    print(f"\n✓ Scraped {scraped}/{len(SOURCES)} live documents")
    print(f"\nTotal corpus: {len(list(RAW_DIR.glob('*.json')))} documents in corpus/raw/")
    print("\nNext step: run  python build_db.py")


if __name__ == "__main__":
    run()
