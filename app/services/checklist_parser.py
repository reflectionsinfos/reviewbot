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
    
    def parse_delivery_checklist(self) -> List[Dict[str, Any]]:
        """Parse delivery checklist items"""
        if "Delivery Check List V 1.0" not in self.data:
            raise ValueError("Delivery Check List sheet not found")
        
        df = self.data["Delivery Check List V 1.0"]
        items = []
        
        current_area = None
        
        for idx, row in df.iterrows():
            # Handle merged cells - area column may be NaN
            area = row.get('Area')
            if pd.notna(area) and str(area).strip():
                current_area = str(area).strip()
            elif current_area is None:
                current_area = "General"
            
            question = row.get('Key Review Question')
            if pd.isna(question) or not str(question).strip():
                continue
            
            # Extract item code (e.g., "1.1", "1.2")
            item_code = str(row.get('SNO', '')) if pd.notna(row.get('SNO')) else f"{idx + 1}"
            
            # Extract expected evidence
            expected_evidence = None
            if 'Expected Evidence' in df.columns:
                evidence = row.get('Expected Evidence')
                if pd.notna(evidence):
                    expected_evidence = str(evidence).strip()

            items.append({
                "item_code": item_code,
                "area": current_area,
                "question": str(question).strip(),
                "category": "delivery",
                "weight": 1.0,
                "is_review_mandatory": True,
                "expected_evidence": expected_evidence
            })
        
        return items
    
    def parse_technical_checklist(self) -> List[Dict[str, Any]]:
        """Parse technical checklist items"""
        if "Technical Check List V 1.0" not in self.data:
            raise ValueError("Technical Check List sheet not found")
        
        df = self.data["Technical Check List V 1.0"]
        items = []
        
        current_area = None
        
        for idx, row in df.iterrows():
            # Handle technical area column
            area = row.get('Technical Area')
            if pd.notna(area) and str(area).strip():
                current_area = str(area).strip()
            elif current_area is None:
                current_area = "General"
            
            question = row.get('Key Review Question')
            if pd.isna(question) or not str(question).strip():
                continue
            
            # Extract item code (e.g., "1.10", "1.20")
            item_code = str(row.get('#', '')) if pd.notna(row.get('#')) else f"{idx + 1}"
            
            # Extract expected evidence
            expected_evidence = None
            if 'Expected Evidence' in df.columns:
                evidence = row.get('Expected Evidence')
                if pd.notna(evidence):
                    expected_evidence = str(evidence).strip()
            
            items.append({
                "item_code": item_code,
                "area": current_area,
                "question": str(question).strip(),
                "category": "technical",
                "weight": 1.0,
                "is_review_mandatory": True,
                "expected_evidence": expected_evidence
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

