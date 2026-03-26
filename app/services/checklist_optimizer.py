"""
Checklist Optimizer
AI-powered checklist enhancement recommendations based on project domain
"""
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings


class ChecklistOptimizer:
    """Generate AI recommendations for checklist improvements"""
    
    def __init__(self):
        self.llm = None
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY
            )
    
    # Domain-specific checklist additions
    DOMAIN_CHECKLIST_ADDITIONS = {
        "fintech": {
            "delivery": [
                {
                    "area": "Compliance & Regulatory",
                    "question": "Are PCI-DSS compliance requirements identified and tracked?",
                    "category": "compliance",
                    "priority": "high"
                },
                {
                    "area": "Compliance & Regulatory",
                    "question": "Is SOX compliance addressed for financial reporting systems?",
                    "category": "compliance",
                    "priority": "high"
                },
                {
                    "area": "Security",
                    "question": "Are fraud detection and prevention mechanisms in place?",
                    "category": "security",
                    "priority": "high"
                }
            ],
            "technical": [
                {
                    "area": "Security Architecture",
                    "question": "Is transaction integrity ensured with proper audit trails?",
                    "category": "security",
                    "priority": "high"
                },
                {
                    "area": "Data & Storage Design",
                    "question": "Are financial data retention policies compliant with regulatory requirements?",
                    "category": "compliance",
                    "priority": "high"
                },
                {
                    "area": "Integration Design",
                    "question": "Are payment gateway integrations secure and PCI-compliant?",
                    "category": "security",
                    "priority": "high"
                }
            ]
        },
        "healthcare": {
            "delivery": [
                {
                    "area": "Compliance & Regulatory",
                    "question": "Is HIPAA compliance validated and documented?",
                    "category": "compliance",
                    "priority": "critical"
                },
                {
                    "area": "Risk Management",
                    "question": "Are patient safety risks identified and mitigated?",
                    "category": "risk",
                    "priority": "critical"
                }
            ],
            "technical": [
                {
                    "area": "Security Architecture",
                    "question": "Is PHI (Protected Health Information) properly encrypted and access-controlled?",
                    "category": "security",
                    "priority": "critical"
                },
                {
                    "area": "Audit & Compliance",
                    "question": "Are audit logs comprehensive for HIPAA compliance (who accessed what when)?",
                    "category": "compliance",
                    "priority": "critical"
                },
                {
                    "area": "Integration Design",
                    "question": "Are healthcare integrations (HL7, FHIR) implemented correctly?",
                    "category": "integration",
                    "priority": "high"
                }
            ]
        },
        "ecommerce": {
            "delivery": [
                {
                    "area": "Performance & Scalability",
                    "question": "Is the system tested for peak load (Black Friday scenarios)?",
                    "category": "performance",
                    "priority": "high"
                },
                {
                    "area": "Customer Experience",
                    "question": "Is the checkout flow optimized and tested for abandonment?",
                    "category": "ux",
                    "priority": "high"
                }
            ],
            "technical": [
                {
                    "area": "Scalability Design",
                    "question": "Can the system handle 10x normal load during sales events?",
                    "category": "scalability",
                    "priority": "high"
                },
                {
                    "area": "Inventory Management",
                    "question": "Is inventory consistency ensured across channels (no overselling)?",
                    "category": "data_integrity",
                    "priority": "high"
                }
            ]
        },
        "data_migration": {
            "delivery": [
                {
                    "area": "Migration Planning",
                    "question": "Is there a detailed cutover plan with rollback strategy?",
                    "category": "planning",
                    "priority": "critical"
                },
                {
                    "area": "Data Validation",
                    "question": "Are reconciliation processes defined for post-migration validation?",
                    "category": "validation",
                    "priority": "critical"
                }
            ],
            "technical": [
                {
                    "area": "Migration Strategy",
                    "question": "Is the migration approach (big bang vs phased) documented and justified?",
                    "category": "architecture",
                    "priority": "high"
                },
                {
                    "area": "Data Quality",
                    "question": "Are data cleansing and transformation rules documented and tested?",
                    "category": "data_quality",
                    "priority": "high"
                },
                {
                    "area": "Rollback Design",
                    "question": "Is rollback tested and validated for failure scenarios?",
                    "category": "resilience",
                    "priority": "critical"
                }
            ]
        },
        "ai_ml": {
            "delivery": [
                {
                    "area": "Model Governance",
                    "question": "Is there a model validation and approval process?",
                    "category": "governance",
                    "priority": "high"
                },
                {
                    "area": "Ethics & Bias",
                    "question": "Are bias testing and fairness assessments conducted?",
                    "category": "ethics",
                    "priority": "high"
                }
            ],
            "technical": [
                {
                    "area": "Model Architecture",
                    "question": "Is model versioning and lineage tracking implemented?",
                    "category": "mlops",
                    "priority": "high"
                },
                {
                    "area": "Monitoring",
                    "question": "Is model drift detection and retraining automated?",
                    "category": "monitoring",
                    "priority": "high"
                }
            ]
        }
    }
    
    async def analyze_and_recommend(
        self,
        project_domain: str,
        current_checklist: Dict[str, List[Dict[str, Any]]],
        project_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze current checklist and generate AI-powered recommendations
        """
        recommendations = []
        
        # Add domain-specific items
        domain_additions = self.DOMAIN_CHECKLIST_ADDITIONS.get(project_domain.lower(), {})
        
        for checklist_type in ['delivery', 'technical']:
            if checklist_type in domain_additions:
                for item in domain_additions[checklist_type]:
                    recommendations.append({
                        "type": "add_item",
                        "checklist_type": checklist_type,
                        "item": item,
                        "rationale": f"Critical for {project_domain} domain",
                        "priority": item.get('priority', 'medium'),
                        "confidence": 0.9
                    })
        
        # Use LLM for additional contextual recommendations
        if self.llm and current_checklist:
            llm_recommendations = await self._get_llm_recommendations(
                project_domain,
                current_checklist,
                project_context
            )
            recommendations.extend(llm_recommendations)
        
        return recommendations
    
    async def _get_llm_recommendations(
        self,
        project_domain: str,
        current_checklist: Dict[str, List[Dict[str, Any]]],
        project_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get AI-powered recommendations using LLM"""
        
        system_message = SystemMessage(content="""
You are an expert project reviewer specializing in technical and delivery checklists.
Your task is to recommend additional checklist items based on the project domain and context.

Focus on:
1. Domain-specific risks and requirements
2. Industry best practices
3. Common pitfalls to avoid
4. Compliance and regulatory needs

Be concise and practical in your recommendations.
""")
        
        checklist_summary = self._summarize_checklist(current_checklist)
        
        user_message = HumanMessage(content=f"""
Project Domain: {project_domain}

Current Checklist Summary:
{checklist_summary}

Project Context: {project_context or 'Not provided'}

Please recommend 3-5 additional checklist items that would be valuable for this 
{project_domain} project but are missing from the current checklist.

For each recommendation, provide:
1. The checklist question
2. Which category (delivery or technical)
3. Why it's important for this domain
4. Priority level (critical, high, medium, low)

Format as JSON array.
""")
        
        try:
            response = await self.llm.ainvoke([system_message, user_message])
            # Parse response (assuming it returns JSON-like structure)
            # In production, add proper JSON parsing with error handling
            return self._parse_llm_recommendations(response.content)
        except Exception as e:
            print(f"LLM recommendation error: {e}")
            return []
    
    def _summarize_checklist(self, checklist: Dict[str, List[Dict[str, Any]]]) -> str:
        """Create a summary of current checklist for LLM context"""
        summary_parts = []
        
        for checklist_type, items in checklist.items():
            areas = set(item.get('area', 'General') for item in items)
            summary_parts.append(f"- {checklist_type.title()}: {len(items)} items covering {', '.join(areas)}")
        
        return "\n".join(summary_parts)
    
    def _parse_llm_recommendations(self, content: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured recommendations"""
        # Simple parsing - in production use proper JSON parsing
        recommendations = []
        
        # This is a simplified parser - enhance for production
        lines = content.strip().split('\n')
        current_rec = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if any(keyword in line.lower() for keyword in ['question:', 'category:', 'why:', 'priority:']):
                if current_rec:
                    recommendations.append(current_rec)
                current_rec = {"raw_text": line}
            elif current_rec:
                current_rec["raw_text"] = current_rec.get("raw_text", "") + " " + line
        
        if current_rec:
            recommendations.append(current_rec)
        
        return [
            {
                "type": "add_item",
                "item": rec,
                "rationale": "AI-suggested based on domain analysis",
                "priority": "medium",
                "confidence": 0.7
            }
            for rec in recommendations
        ]
    
    def identify_redundant_items(
        self,
        checklist_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify potentially redundant or overlapping checklist items"""
        # Simple similarity-based detection
        redundant = []
        
        for i, item1 in enumerate(checklist_items):
            for j, item2 in enumerate(checklist_items[i+1:], i+1):
                similarity = self._calculate_question_similarity(
                    item1.get('question', ''),
                    item2.get('question', '')
                )
                
                if similarity > 0.85:  # High similarity threshold
                    redundant.append({
                        "type": "merge_items",
                        "items": [item1, item2],
                        "similarity_score": similarity,
                        "rationale": "These questions appear to overlap significantly"
                    })
        
        return redundant
    
    def _calculate_question_similarity(self, q1: str, q2: str) -> float:
        """Calculate similarity between two questions"""
        # Simple Jaccard similarity for now
        # In production, use embeddings-based similarity
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def suggest_checklist_for_new_project(
        self,
        project_domain: str,
        project_type: str = "standard"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Suggest a complete checklist for a new project based on domain
        """
        base_checklist = {
            "delivery": self._get_base_delivery_checklist(),
            "technical": self._get_base_technical_checklist()
        }
        
        # Add domain-specific items
        domain_additions = self.DOMAIN_CHECKLIST_ADDITIONS.get(project_domain.lower(), {})
        
        for checklist_type in ['delivery', 'technical']:
            if checklist_type in domain_additions:
                base_checklist[checklist_type].extend(domain_additions[checklist_type])
        
        return base_checklist
    
    def _get_base_delivery_checklist(self) -> List[Dict[str, Any]]:
        """Get base delivery checklist items"""
        return [
            {"area": "Scope, Planning & Governance", "question": "Is scope clearly defined and signed off?", "category": "delivery"},
            {"area": "Delivery Health", "question": "Are milestones on track against plan?", "category": "delivery"},
            {"area": "Requirements & Customer Alignment", "question": "Are requirements clear and prioritized?", "category": "delivery"},
            {"area": "Risks, Issues & Escalations", "question": "Are risks logged and mitigations defined?", "category": "delivery"},
            {"area": "Resource & Team Management", "question": "Do we have the right skills and capacity?", "category": "delivery"},
            {"area": "Quality & Testing", "question": "Are tests executed with required coverage?", "category": "delivery"},
        ]
    
    def _get_base_technical_checklist(self) -> List[Dict[str, Any]]:
        """Get base technical checklist items"""
        return [
            {"area": "Architecture & Design", "question": "Is architecture documented and up to date?", "category": "technical"},
            {"area": "Technical Documentation", "question": "Is system design documentation complete?", "category": "technical"},
            {"area": "Data & Storage Design", "question": "Are data models appropriate for the workload?", "category": "technical"},
            {"area": "Security Architecture", "question": "Is sensitive data encrypted in transit and at rest?", "category": "technical"},
            {"area": "Code Quality", "question": "Are code reviews and static analysis in place?", "category": "technical"},
            {"area": "Testing Strategy", "question": "Is test automation leveraged appropriately?", "category": "technical"},
        ]


# Global instance
_optimizer: Optional[ChecklistOptimizer] = None


def get_checklist_optimizer() -> ChecklistOptimizer:
    """Get or create checklist optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = ChecklistOptimizer()
    return _optimizer
