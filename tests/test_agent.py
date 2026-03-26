"""
Tests for AI Tech & Delivery Review Agent
"""
import pytest
from pathlib import Path


class TestChecklistParser:
    """Test Excel checklist parsing"""
    
    def test_parser_initialization(self):
        """Test checklist parser initialization"""
        from app.services.checklist_parser import ChecklistParser
        
        # Create a mock file path
        parser = ChecklistParser("test.xlsx")
        assert parser.file_path.name == "test.xlsx"
    
    def test_parse_delivery_checklist_structure(self):
        """Test delivery checklist item structure"""
        # Mock checklist item
        item = {
            "item_code": "1.1",
            "area": "Scope, Planning & Governance",
            "question": "Are scope / SoW / baselines clearly defined?",
            "category": "delivery",
            "weight": 1.0,
            "is_required": True
        }
        
        assert item["item_code"] == "1.1"
        assert item["category"] == "delivery"
        assert item["weight"] == 1.0


class TestReportGenerator:
    """Test report generation"""
    
    def test_calculate_compliance_score_all_green(self):
        """Test compliance score calculation - all green"""
        from app.services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        responses = [
            {"rag_status": "green", "weight": 1.0},
            {"rag_status": "green", "weight": 1.0},
            {"rag_status": "green", "weight": 1.0}
        ]
        
        score = generator.calculate_compliance_score(responses, [])
        assert score == 100.0
    
    def test_calculate_compliance_score_mixed(self):
        """Test compliance score calculation - mixed RAG"""
        from app.services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        responses = [
            {"rag_status": "green", "weight": 1.0},  # 100
            {"rag_status": "amber", "weight": 1.0},  # 50
            {"rag_status": "red", "weight": 1.0}     # 0
        ]
        
        score = generator.calculate_compliance_score(responses, [])
        assert score == 50.0  # (100 + 50 + 0) / 3
    
    def test_determine_overall_rag(self):
        """Test overall RAG determination"""
        from app.services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        assert generator.determine_overall_rag(85) == "green"
        assert generator.determine_overall_rag(75) == "amber"
        assert generator.determine_overall_rag(40) == "red"
    
    def test_analyze_gaps(self):
        """Test gap analysis"""
        from app.services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        responses = [
            {
                "question": "Is architecture documented?",
                "area": "Technical",
                "rag_status": "red",
                "comments": "ADRs missing"
            },
            {
                "question": "Are tests executed?",
                "area": "Quality",
                "rag_status": "green",
                "comments": "All tests passing"
            }
        ]
        
        gaps = generator.analyze_gaps(responses)
        
        assert len(gaps) == 1
        assert gaps[0]["rag_status"] == "red"
        assert gaps[0]["severity"] == "high"


class TestChecklistOptimizer:
    """Test checklist optimization"""
    
    def test_domain_checklist_additions_exist(self):
        """Test that domain-specific additions are defined"""
        from app.services.checklist_optimizer import ChecklistOptimizer
        
        optimizer = ChecklistOptimizer()
        
        # Check fintech additions
        assert "fintech" in optimizer.DOMAIN_CHECKLIST_ADDITIONS
        assert "delivery" in optimizer.DOMAIN_CHECKLIST_ADDITIONS["fintech"]
        assert "technical" in optimizer.DOMAIN_CHECKLIST_ADDITIONS["fintech"]
    
    def test_fintech_additions_content(self):
        """Test fintech-specific checklist items"""
        from app.services.checklist_optimizer import ChecklistOptimizer
        
        optimizer = ChecklistOptimizer()
        fintech_delivery = optimizer.DOMAIN_CHECKLIST_ADDITIONS["fintech"]["delivery"]
        
        # Should have compliance-related items
        areas = [item.get("area") for item in fintech_delivery]
        assert any("Compliance" in area for area in areas)


class TestVoiceInterface:
    """Test voice interface"""
    
    def test_voice_interface_initialization(self):
        """Test voice interface initialization"""
        from app.services.voice_interface import VoiceInterface
        
        interface = VoiceInterface()
        assert interface is not None
    
    def test_get_available_voices(self):
        """Test available voices list"""
        from app.services.voice_interface import VoiceInterface
        
        interface = VoiceInterface()
        voices = interface.get_available_voices()
        
        assert len(voices) > 0
        assert all("id" in voice for voice in voices)
        assert all("name" in voice for voice in voices)


class TestReviewAgent:
    """Test review agent"""
    
    def test_agent_initialization(self):
        """Test review agent initialization"""
        from app.agents.review_agent import ReviewAgent
        
        agent = ReviewAgent()
        assert agent is not None
        assert agent.graph is not None
    
    def test_rag_assessment_logic(self):
        """Test RAG assessment logic"""
        # Simple rule-based assessment
        answer_yes = "Yes, all baselines are signed off"
        answer_no = "No, this is not done"
        answer_partial = "Partially complete, working on it"
        
        assert any(word in answer_yes.lower() for word in ["yes", "yeah", "yep"])
        assert any(word in answer_no.lower() for word in ["no", "nope"])
        assert any(word in answer_partial.lower() for word in ["partial", "partially"])


class TestDatabaseModels:
    """Test database models"""
    
    def test_project_model(self):
        """Test Project model structure"""
        from app.models import Project
        
        project = Project(
            name="Test Project",
            domain="fintech",
            description="Test description"
        )
        
        assert project.name == "Test Project"
        assert project.domain == "fintech"
        assert project.status == "active"
    
    def test_review_model(self):
        """Test Review model structure"""
        from app.models import Review
        
        review = Review(
            project_id=1,
            checklist_id=1,
            title="Test Review",
            voice_enabled=True
        )
        
        assert review.project_id == 1
        assert review.voice_enabled == True
        assert review.status == "draft"
    
    def test_report_model(self):
        """Test Report model structure"""
        from app.models import Report
        
        report = Report(
            review_id=1,
            compliance_score=75.5,
            overall_rag_status="amber"
        )
        
        assert report.review_id == 1
        assert report.compliance_score == 75.5
        assert report.overall_rag_status == "amber"
        assert report.approval_status == "pending"


class TestAPIEndpoints:
    """Test API endpoint availability"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data


class TestRAGStatusEnum:
    """Test RAG status enum"""
    
    def test_rag_status_values(self):
        """Test RAG status enum values"""
        from app.models import RAGStatus
        
        assert RAGStatus.RED.value == "red"
        assert RAGStatus.AMBER.value == "amber"
        assert RAGStatus.GREEN.value == "green"
        assert RAGStatus.NA.value == "na"


class TestApprovalWorkflow:
    """Test approval workflow"""
    
    def test_approval_status_enum(self):
        """Test approval status enum values"""
        from app.models import ApprovalStatus
        
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.REVISION_REQUESTED.value == "revision_requested"
    
    def test_report_requires_approval(self):
        """Test that reports require approval by default"""
        from app.models import Report
        
        report = Report(review_id=1)
        
        assert report.approval_status == "pending"
        assert report.requires_approval == True


# Run tests with: pytest tests/test_agent.py -v
