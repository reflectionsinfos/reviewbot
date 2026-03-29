"""
Backfill script to populate summary metrics for existing autonomous review jobs.
Scan all completed jobs where summary counts are 0, and recalculate them from results.
"""
import asyncio
import os
import sys

# Add the project root to sys.path to allow importing from 'app'
sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models import AutonomousReviewJob, AutonomousReviewResult, AutonomousReviewOverride

async def backfill():
    async with AsyncSessionLocal() as db:
        # Get all completed jobs that have 0 or None for summary counts
        # We check green_count, amber_count, red_count together.
        query = (
            select(AutonomousReviewJob)
            .where(AutonomousReviewJob.status == "completed")
            .options(
                selectinload(AutonomousReviewJob.results).selectinload(AutonomousReviewResult.overrides)
            )
        )
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        print(f"Found {len(jobs)} completed jobs to evaluate.")
        updated_count = 0
        
        for job in jobs:
            # Only update if they are actually 0/None or if we want a full refresh
            # For this script we update if any count is 0, since many existing jobs
            # might hit this. Or we can just refresh all.
            
            green = 0
            amber = 0
            red = 0
            skipped = 0
            na = 0
            
            if not job.results:
                print(f"  Job {job.id}: No results found, skipping.")
                continue

            for r in job.results:
                # Determine effective RAG status (accounting for overrides)
                status = r.rag_status
                if r.overrides:
                    # Get the most recent override
                    latest_override = sorted(r.overrides, key=lambda o: o.overridden_at)[-1]
                    status = latest_override.new_rag_status
                
                if status == "green": green += 1
                elif status == "amber": amber += 1
                elif status == "red": red += 1
                elif status == "skipped": skipped += 1
                elif status == "na": na += 1
                else:
                    # Fallback for unknown statuses
                    na += 1
            
            auto_total = green + amber + red
            compliance = round(green / auto_total * 100, 1) if auto_total else 0.0
            
            # Print diff if changing
            if job.green_count != green or job.compliance_score != compliance:
                print(f"  Job {job.id}: {job.green_count}G/{job.amber_count}A/{job.red_count}R -> {green}G/{amber}A/{red}R (Score: {compliance}%)")
                
                job.green_count = green
                job.amber_count = amber
                job.red_count = red
                job.skipped_count = skipped
                job.na_count = na
                job.compliance_score = compliance
                updated_count += 1
        
        if updated_count > 0:
            await db.commit()
            print(f"Successfully backfilled {updated_count} jobs.")
        else:
            print("No jobs required recalculation.")

if __name__ == "__main__":
    asyncio.run(backfill())
