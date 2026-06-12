import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models import AutonomousReviewJob, AutonomousReviewResult, AutonomousReviewOverride
from app.services.compliance_score import calculate_compliance_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill")

async def backfill_job_scores():
    async with AsyncSessionLocal() as db:
        # Load all completed jobs to process existing results
        result = await db.execute(
            select(AutonomousReviewJob)
            .options(
                selectinload(AutonomousReviewJob.results).selectinload(
                    AutonomousReviewResult.overrides
                ),
                selectinload(AutonomousReviewJob.results).selectinload(
                    AutonomousReviewResult.checklist_item
                ),
            )
            .where(AutonomousReviewJob.status == "completed")
        )
        jobs = result.scalars().all()
        
        logger.info(f"Found {len(jobs)} completed jobs to process for summary backfill.")
        
        for job in jobs:
            def get_effective_status(r) -> str:
                if r.overrides:
                    # Use the latest override
                    return sorted(r.overrides, key=lambda o: o.overridden_at)[-1].new_rag_status
                return r.rag_status

            results = job.results
            
            # Counts
            green   = sum(1 for r in results if get_effective_status(r) == "green")
            amber   = sum(1 for r in results if get_effective_status(r) == "amber")
            red     = sum(1 for r in results if get_effective_status(r) == "red")
            
            # Unified: "Human Required" includes skipped, na, and human_required
            skipped = sum(1 for r in results if get_effective_status(r) in ("skipped", "na", "human_required"))
            na_orig = sum(1 for r in results if get_effective_status(r) == "na")
            
            # Score (weighted compliance)
            rag_entries = [
                (get_effective_status(r), r.checklist_item.weight if r.checklist_item else 1.0)
                for r in results
                if get_effective_status(r) in ("green", "amber", "red")
            ]
            score, _, _ = calculate_compliance_score(rag_entries)
            score = round(score, 1)
            
            # Update job record
            job.green_count = green
            job.amber_count = amber
            job.red_count = red
            job.skipped_count = skipped
            job.na_count = na_orig  # Keep original NA count if needed for forensics
            job.compliance_score = score
            
            logger.info(f"Updated job {job.id}: Compliant:{green}, Amber:{amber}, Red:{red}, Human:{skipped}, Score:{score}%")
        
        await db.commit()
        logger.info("Database backfill of summary scores completed successfully.")

if __name__ == "__main__":
    asyncio.run(backfill_job_scores())
