"""
Migration 009: Convert existing item_code from numeric (1.1, 2.1) to area code format (SEC-001, TECH-001)

This script:
1. Reads all existing checklist items grouped by checklist and area
2. Generates area codes for each unique area name
3. Updates item_code from "1.1" to "SEC-001", "2.1" to "TECH-001", etc.
4. Saves the area_codes mapping to each checklist

Run once after deploying the area_codes column and new validation logic.
"""
import asyncio
import os
import re
import sys
from pathlib import Path

# Override DEBUG before any imports
os.environ['DEBUG'] = 'True'

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

# Import settings after setting DEBUG
from app.core.config import settings

# Override DATABASE_URL for local execution (Docker uses 'db' hostname)
DATABASE_URL = os.environ.get('DATABASE_URL', settings.DATABASE_URL)

# Detect if running inside Docker container
IN_DOCKER = os.path.exists('/.dockerenv')

# Only replace hostname if NOT running in Docker
if not IN_DOCKER and 'db' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('@db:', '@localhost:')

from app.models import Checklist, ChecklistItem


def generate_area_code(area_name: str) -> str:
    """
    Generate a 3-4 letter area code from area name.
    Uses consonants and first letter, uppercase.
    
    Examples:
        "Security" - "SEC"
        "Technical Architecture" - "TECH"
        "Governance" - "GOV"
        "Scope & Planning" - "SCOP"
    """
    words = re.sub(r'[^a-zA-Z\s]', '', area_name).split()
    consonants = set('BCDFGHJKLMNPQRSTVWXYZ')
    code = ""
    
    for word in words:
        if len(code) >= 4:
            break
        if word:
            code += word[0].upper()
        for char in word[1:]:
            if char.upper() in consonants and len(code) < 4:
                code += char.upper()
    
    code = (code + "XXX")[:4]
    return code


async def migrate_item_codes():
    """Migrate all existing item codes to area code format."""
    
    # Create engine and session
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False)
    
    async with AsyncSessionLocal() as session:
        print("[MIGRATION] Starting item code migration...")
        
        # Get all checklists
        result = await session.execute(select(Checklist))
        checklists = result.scalars().all()
        
        total_checklists = len(checklists)
        print(f"[MIGRATION] Found {total_checklists} checklists to process")
        
        checklists_updated = 0
        items_updated = 0
        
        for checklist in checklists:
            print(f"\n  Processing checklist: {checklist.name} (ID: {checklist.id})")
            
            # Get all items for this checklist
            items_result = await session.execute(
                select(ChecklistItem)
                .where(ChecklistItem.checklist_id == checklist.id)
                .order_by(ChecklistItem.area, ChecklistItem.id)
            )
            items = items_result.scalars().all()
            
            if not items:
                print("    - No items, skipping")
                continue
            
            # Group items by area and track sequence numbers
            area_sequences: dict[str, int] = {}
            area_codes: dict[str, str] = {}
            items_to_update = []
            
            for item in items:
                area = item.area or "General"
                
                # Generate area code if not exists
                if area not in area_codes:
                    area_codes[area] = generate_area_code(area)
                    area_sequences[area] = 0
                    print(f"    - New area: '{area}' => {area_codes[area]}")
                
                # Get next sequence number for this area
                area_sequences[area] += 1
                seq = area_sequences[area]
                
                # Generate new item_code
                new_code = f"{area_codes[area]}-{str(seq).zfill(3)}"
                
                # Only update if code is different
                if item.item_code != new_code:
                    items_to_update.append((item, new_code))
            
            # Update items
            for item, new_code in items_to_update:
                old_code = item.item_code
                item.item_code = new_code
                print(f"    - Updated: {old_code} => {new_code}")
                items_updated += 1
            
            # Save area_codes to checklist
            if area_codes:
                checklist.area_codes = area_codes
                checklists_updated += 1
                print(f"    - Saved {len(area_codes)} area codes to checklist")
            
            # Commit after each checklist
            await session.commit()
        
        print("\n" + "="*60)
        print("MIGRATION COMPLETE!")
        print(f"  Checklists updated: {checklists_updated}")
        print(f"  Items updated: {items_updated}")
        print("="*60)
    
    await engine.dispose()
    return checklists_updated, items_updated


if __name__ == "__main__":
    print("="*60)
    print("Migration 009: Item Code Format Conversion")
    print("="*60)
    print()
    print("WARNING: This will modify existing item_code values.")
    print("WARNING: Make sure you have a database backup before proceeding.")
    print()
    
    # Accept --yes flag to skip confirmation
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        confirmed = True
    else:
        response = input("Continue? Type 'yes' to confirm: ").strip().lower()
        confirmed = response == "yes"
    
    if not confirmed:
        print("Migration cancelled.")
        sys.exit(0)
    
    print()
    
    try:
        checklists, items = asyncio.run(migrate_item_codes())
        print()
        print("Migration completed successfully!")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
