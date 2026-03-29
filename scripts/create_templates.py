"""
Create Global Templates from Excel Files
Run this script to load your existing Excel checklists as global templates
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Base, Checklist, ChecklistItem
from app.services.checklist_parser import ChecklistParser


async def create_global_templates():
    """Create global checklist templates from Excel files"""
    
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create async session
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Excel files to load as templates
    data_dir = Path(__file__).parent.parent / "data" / "templates"
    excel_files = [
        {
            "path": str(data_dir / "standard-delivery.xlsx"),
            "name": "Standard Delivery Template"
        },
        {
            "path": str(data_dir / "standard-technical.xlsx"),
            "name": "Standard Technical Template"
        },
    ]
    
    async with AsyncSessionLocal() as session:
        for excel_info in excel_files:
            excel_path = Path(excel_info["path"])
            
            if not excel_path.exists():
                print(f"⚠️  File not found: {excel_path}")
                print(f"   Please place the file in: {Path.cwd()}")
                continue
            
            print(f"\n📄 Processing: {excel_path.name}")
            
            try:
                # Parse Excel file
                parser = ChecklistParser(str(excel_path))
                data = parser.parse_all()
                
                # Create checklists for each type
                for checklist_type, items in data.get("checklists", {}).items():
                    if not items:
                        print(f"   ⚠️  No items found for {checklist_type}")
                        continue
                    
                    # Create global checklist
                    checklist = Checklist(
                        name=f"{checklist_type.title()} Check List V 1.0",
                        type=checklist_type,
                        version="1.0",
                        project_id=None,  # Global template
                        is_global=True
                    )
                    
                    session.add(checklist)
                    await session.flush()  # Get ID
                    
                    # Add items
                    for idx, item_data in enumerate(items):
                        item = ChecklistItem(
                            checklist_id=checklist.id,
                            item_code=item_data.get("item_code", str(idx + 1)),
                            area=item_data.get("area", "General"),
                            question=item_data.get("question"),
                            category=item_data.get("category", checklist_type),
                            weight=item_data.get("weight", 1.0),
                            is_review_mandatory=item_data.get("is_review_mandatory", True),
                            expected_evidence=item_data.get("expected_evidence"),
                            order=idx
                        )
                        session.add(item)
                    
                    print(f"   ✅ Created {checklist_type} checklist with {len(items)} items")
                
                await session.commit()
                print(f"✅ Successfully created templates from {excel_path.name}")
                
            except Exception as e:
                await session.rollback()
                print(f"❌ Error processing {excel_path.name}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ Template creation complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start the server: uvicorn main:app --reload")
    print("2. View templates: GET /api/projects/templates")
    print("3. Apply to project: POST /api/projects/{id}/use-template/{template_id}")


if __name__ == "__main__":
    print("="*60)
    print("📋 AI Review Agent - Global Template Creator")
    print("="*60)
    print("\nThis script will create global checklist templates from your")
    print("existing Excel files and store them in the database.\n")
    
    asyncio.run(create_global_templates())

