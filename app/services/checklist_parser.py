"""
Excel Checklist Parser
Parses delivery and technical checklists from Excel files
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import re


class ChecklistParser:
    """Parse Excel checklist files into structured data"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data: Dict[str, pd.DataFrame] = {}
        
    def load(self) -> Dict[str, pd.DataFrame]:
        """Load all sheets from Excel file"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")
        
        excel_file = pd.ExcelFile(self.file_path)
        for sheet_name in excel_file.sheet_names:
            self.data[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        return self.data

    @staticmethod
    def _optional_text(row: pd.Series, columns: List[str]) -> Optional[str]:
        for column in columns:
            if column in row.index:
                value = row.get(column)
                if pd.notna(value) and str(value).strip():
                    return str(value).strip()
        return None

    @classmethod
    def _optional_tags(cls, row: pd.Series, columns: List[str]) -> Optional[List[str]]:
        raw = cls._optional_text(row, columns)
        if not raw:
            return None
        tags = [tag.strip() for tag in re.split(r"[;,]", raw) if tag and tag.strip()]
        return tags or None
    
    @staticmethod
    def _parse_weight(row: pd.Series) -> float:
        """Read Weight column; fall back to 1.0."""
        raw = row.get("Weight")
        if pd.notna(raw):
            try:
                return float(raw)
            except (ValueError, TypeError):
                pass
        return 1.0

    @staticmethod
    def _parse_mandatory(row: pd.Series) -> bool:
        """Read Review? column (Yes/No/True/False/1/0); fall back to True."""
        raw = row.get("Review?")
        if pd.notna(raw):
            val = str(raw).strip().lower()
            return val not in ("no", "false", "0", "n")
        return True

    def _is_new_format(self, df: pd.DataFrame) -> bool:
        """Detect unified column layout (new template format)."""
        return "Question" in df.columns

    def parse_delivery_checklist(self) -> List[Dict[str, Any]]:
        """Parse delivery checklist items — supports both old and new column layouts."""
        if "Delivery Check List V 1.0" not in self.data:
            raise ValueError("Delivery Check List sheet not found")

        df = self.data["Delivery Check List V 1.0"]
        items = []
        current_area = None

        if self._is_new_format(df):
            # ── New unified format ────────────────────────────────────────────
            for idx, row in df.iterrows():
                area = row.get("Area")
                if pd.notna(area) and str(area).strip():
                    current_area = str(area).strip()
                elif current_area is None:
                    current_area = "General"

                question = row.get("Question")
                if pd.isna(question) or not str(question).strip():
                    continue

                items.append({
                    "item_code": str(idx + 1),
                    "area": current_area,
                    "question": str(question).strip(),
                    "category": "delivery",
                    "weight": self._parse_weight(row),
                    "is_review_mandatory": self._parse_mandatory(row),
                    "expected_evidence": self._optional_text(row, ["Evidence", "Expected Evidence"]),
                    "team_category": self._optional_text(row, ["Team Category", "Owner Team"]),
                    "guidance": self._optional_text(row, ["Guidance", "Reviewer Guidance"]),
                    "applicability_tags": self._optional_tags(row, ["Applicability Tags", "Applicability", "Tags"]),
                })
        else:
            # ── Legacy format (SNO / Area / Key Review Question / …) ──────────
            for idx, row in df.iterrows():
                area = row.get("Area")
                if pd.notna(area) and str(area).strip():
                    current_area = str(area).strip()
                elif current_area is None:
                    current_area = "General"

                question = row.get("Key Review Question")
                if pd.isna(question) or not str(question).strip():
                    continue

                item_code = str(row.get("SNO", "")) if pd.notna(row.get("SNO")) else str(idx + 1)
                expected_evidence = None
                if "Expected Evidence" in df.columns:
                    ev = row.get("Expected Evidence")
                    if pd.notna(ev):
                        expected_evidence = str(ev).strip()

                items.append({
                    "item_code": item_code,
                    "area": current_area,
                    "question": str(question).strip(),
                    "category": "delivery",
                    "weight": self._parse_weight(row),
                    "is_review_mandatory": self._parse_mandatory(row),
                    "expected_evidence": expected_evidence,
                    "team_category": self._optional_text(row, ["Team Category", "Owner Team", "Owning Team"]),
                    "guidance": self._optional_text(row, ["Guidance", "Reviewer Guidance"]),
                    "applicability_tags": self._optional_tags(row, ["Applicability Tags", "Applicability", "Tags"]),
                })

        return items

    def parse_technical_checklist(self) -> List[Dict[str, Any]]:
        """Parse technical checklist items — supports both old and new column layouts."""
        if "Technical Check List V 1.0" not in self.data:
            raise ValueError("Technical Check List sheet not found")

        df = self.data["Technical Check List V 1.0"]
        items = []
        current_area = None

        if self._is_new_format(df):
            # ── New unified format ────────────────────────────────────────────
            for idx, row in df.iterrows():
                area = row.get("Area")
                if pd.notna(area) and str(area).strip():
                    current_area = str(area).strip()
                elif current_area is None:
                    current_area = "General"

                question = row.get("Question")
                if pd.isna(question) or not str(question).strip():
                    continue

                items.append({
                    "item_code": str(idx + 1),
                    "area": current_area,
                    "question": str(question).strip(),
                    "category": "technical",
                    "weight": self._parse_weight(row),
                    "is_review_mandatory": self._parse_mandatory(row),
                    "expected_evidence": self._optional_text(row, ["Evidence", "Expected Evidence"]),
                    "team_category": self._optional_text(row, ["Team Category", "Owner Team"]),
                    "guidance": self._optional_text(row, ["Guidance", "Reviewer Guidance"]),
                    "applicability_tags": self._optional_tags(row, ["Applicability Tags", "Applicability", "Tags"]),
                })
        else:
            # ── Legacy format (# / Technical Area / Key Review Question / …) ─
            for idx, row in df.iterrows():
                area = row.get("Technical Area")
                if pd.notna(area) and str(area).strip():
                    current_area = str(area).strip()
                elif current_area is None:
                    current_area = "General"

                question = row.get("Key Review Question")
                if pd.isna(question) or not str(question).strip():
                    continue

                item_code = str(row.get("#", "")) if pd.notna(row.get("#")) else str(idx + 1)
                expected_evidence = None
                if "Expected Evidence" in df.columns:
                    ev = row.get("Expected Evidence")
                    if pd.notna(ev):
                        expected_evidence = str(ev).strip()

                items.append({
                    "item_code": item_code,
                    "area": current_area,
                    "question": str(question).strip(),
                    "category": "technical",
                    "weight": self._parse_weight(row),
                    "is_review_mandatory": self._parse_mandatory(row),
                    "expected_evidence": expected_evidence,
                    "team_category": self._optional_text(row, ["Team Category", "Owner Team", "Owning Team"]),
                    "guidance": self._optional_text(row, ["Guidance", "Reviewer Guidance"]),
                    "applicability_tags": self._optional_tags(row, ["Applicability Tags", "Applicability", "Tags"]),
                })

        return items
    
    def parse_master_sheet(self) -> List[Dict[str, Any]]:
        """Parse items from a single-sheet master template (unified column format).

        Looks for a sheet named 'master template items' (case-insensitive).
        Falls back to the first sheet when no exact match is found.
        """
        target_df: Optional[pd.DataFrame] = None
        for sheet_name, df in self.data.items():
            if sheet_name.strip().lower() == "master template items":
                target_df = df
                break
        if target_df is None:
            target_df = next(iter(self.data.values()))

        items = []
        current_area = None

        for idx, row in target_df.iterrows():
            area = row.get("Area")
            if pd.notna(area) and str(area).strip():
                current_area = str(area).strip()
            elif current_area is None:
                current_area = "General"

            question = row.get("Question")
            if pd.isna(question) or not str(question).strip():
                continue

            raw_category = row.get("Category")
            category = str(raw_category).strip().lower() if pd.notna(raw_category) else "delivery"
            if category not in ("delivery", "technical"):
                category = "delivery"

            items.append({
                "item_code": str(idx + 1),
                "area": current_area,
                "question": str(question).strip(),
                "category": category,
                "weight": self._parse_weight(row),
                "is_review_mandatory": self._parse_mandatory(row),
                "expected_evidence": self._optional_text(row, ["Evidence", "Expected Evidence"]),
                "team_category": self._optional_text(row, ["Team Category", "Owner Team"]),
                "guidance": self._optional_text(row, ["Guidance", "Reviewer Guidance"]),
                "applicability_tags": self._optional_tags(row, ["Applicability Tags", "Applicability", "Tags"]),
            })

        return items

    def parse_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse all checklists from the file"""
        self.load()

        result = {}

        if "Delivery Check List V 1.0" in self.data:
            result["delivery"] = self.parse_delivery_checklist()

        if "Technical Check List V 1.0" in self.data:
            result["technical"] = self.parse_technical_checklist()

        has_master = any(
            s.strip().lower() == "master template items" for s in self.data
        )
        if has_master or (not result):
            result["master"] = self.parse_master_sheet()

        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the checklists"""
        stats = {
            "file_name": self.file_path.name,
            "sheets": list(self.data.keys()),
            "total_rows": {}
        }
        
        for sheet_name, df in self.data.items():
            stats["total_rows"][sheet_name] = len(df)
        
        return stats


async def parse_excel_checklist(file_path: str) -> Dict[str, Any]:
    """
    Async wrapper for parsing Excel checklist
    Returns structured checklist data
    """
    parser = ChecklistParser(file_path)
    data = parser.parse_all()
    stats = parser.get_statistics()
    
    return {
        "checklists": data,
        "statistics": stats
    }


def infer_domain_from_checklist_responses(
    delivery_responses: Dict[str, str],
    technical_responses: Dict[str, str]
) -> List[Dict[str, str]]:
    """
    Infer project domain based on checklist responses
    Returns list of possible domains with confidence scores
    """
    domain_indicators = {
        "fintech": {
            "keywords": ["payment", "financial", "transaction", "pci", "sox", "banking", "money"],
            "score": 0.0
        },
        "healthcare": {
            "keywords": ["hipaa", "patient", "medical", "health", "ehr", "phi"],
            "score": 0.0
        },
        "ecommerce": {
            "keywords": ["cart", "order", "product", "inventory", "shipping", "retail"],
            "score": 0.0
        },
        "data_migration": {
            "keywords": ["migration", "etl", "cutover", "legacy", "data transfer"],
            "score": 0.0
        },
        "enterprise": {
            "keywords": ["enterprise", "corporate", "internal", "erp", "crm"],
            "score": 0.0
        }
    }
    
    # Combine all responses
    all_text = " ".join([
        " ".join(delivery_responses.values()),
        " ".join(technical_responses.values())
    ]).lower()
    
    # Score each domain
    for domain, data in domain_indicators.items():
        for keyword in data["keywords"]:
            if keyword in all_text:
                data["score"] += 0.2
        
        data["score"] = min(data["score"], 1.0)  # Cap at 1.0
    
    # Return sorted by confidence
    results = [
        {"domain": domain, "confidence": data["score"]}
        for domain, data in domain_indicators.items()
        if data["score"] > 0.0
    ]
    
    return sorted(results, key=lambda x: x["confidence"], reverse=True)

