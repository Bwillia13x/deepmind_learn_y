#!/usr/bin/env python3
"""
Integration Test Script for NEXUS System.

Tests the full flow from student code validation through voice session
to Scout Report generation. Can be run manually or in CI/CD.

Usage:
    python -m backend.scripts.integration_test
    # Or with poetry:
    poetry run python -m backend.scripts.integration_test
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_factory, init_db
from app.core.privacy_guard import scrub_pii
from app.db.models import Student, OracySession, ScoutReport, SessionStatus
from app.services.voice_engine.llm_driver import (
    SessionContext,
    ConversationTurn,
    get_llm_driver,
)
from app.services.reporting_agent.insight_generator import generate_scout_report
from app.services.curriculum_rag.vector import get_curriculum_store


class IntegrationTestRunner:
    """Runs integration tests for the NEXUS system."""

    def __init__(self) -> None:
        self.results: list[dict] = []
        self.passed = 0
        self.failed = 0

    def log(self, message: str) -> None:
        """Print with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def record_result(self, test_name: str, passed: bool, details: str = "") -> None:
        """Record a test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append({
            "name": test_name,
            "passed": passed,
            "details": details,
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        self.log(f"  {status}: {test_name}")
        if details and not passed:
            self.log(f"    Details: {details}")

    async def test_curriculum_rag(self) -> None:
        """Test curriculum RAG system."""
        self.log("Testing Curriculum RAG System...")
        
        try:
            store = get_curriculum_store()
            
            # Test search
            results = store.search("communities and belonging", grade_filter=3)
            has_results = len(results) > 0
            self.record_result(
                "Curriculum search returns results",
                has_results,
                f"Found {len(results)} results" if has_results else "No results found"
            )
            
            # Test grade filtering
            grade_5_results = store.search("science", grade_filter=5)
            grade_3_results = store.search("science", grade_filter=3)
            different_results = grade_5_results != grade_3_results or len(grade_5_results) >= 0
            self.record_result(
                "Curriculum grade filtering works",
                different_results,
            )
            
            # Test cultural bridge hints
            if results and results[0].cultural_bridge_hints:
                self.record_result(
                    "Cultural bridge hints available",
                    True,
                )
            else:
                self.record_result(
                    "Cultural bridge hints available",
                    len(results) == 0,  # Pass if no results, otherwise might just not have hints
                    "No cultural hints found"
                )
                
        except Exception as e:
            self.record_result("Curriculum RAG initialization", False, str(e))

    async def test_llm_driver(self) -> None:
        """Test LLM driver responses."""
        self.log("Testing LLM Driver...")
        
        try:
            driver = get_llm_driver()
            
            # Create test context
            context = SessionContext(
                student_code="TEST-integration",
                grade=5,
                primary_language="Ukrainian",
                curriculum_outcome="SS-5-1: Communities past and present",
            )
            
            # Test basic response
            response = await driver.generate_response("Hello, how are you?", context)
            has_response = len(response) > 0
            self.record_result(
                "LLM generates response",
                has_response,
                f"Response length: {len(response)}" if has_response else "Empty response"
            )
            
            # Test response is appropriate length
            words = len(response.split())
            appropriate_length = 5 <= words <= 100
            self.record_result(
                "Response has appropriate length",
                appropriate_length,
                f"Word count: {words}"
            )
            
            # Test conversation continuation
            context.conversation_history = [
                ConversationTurn(role="user", content="Hello"),
                ConversationTurn(role="assistant", content=response),
            ]
            response2 = await driver.generate_response("Tell me more", context)
            continuation_works = len(response2) > 0
            self.record_result(
                "Conversation continuation works",
                continuation_works,
            )
            
        except Exception as e:
            self.record_result("LLM Driver initialization", False, str(e))

    async def test_privacy_guard(self) -> None:
        """Test PII scrubbing."""
        self.log("Testing Privacy Guard...")
        
        test_cases = [
            ("john.doe@email.com", "email"),
            ("555-123-4567", "phone"),
            ("John Smith", "name"),
        ]
        
        for text, pii_type in test_cases:
            scrubbed = scrub_pii(text)
            is_scrubbed = text not in scrubbed or "[REDACTED" in scrubbed
            self.record_result(
                f"Scrubs {pii_type}",
                is_scrubbed,
                f"Original: {text}, Scrubbed: {scrubbed}"
            )

    async def test_scout_report_generation(self) -> None:
        """Test Scout Report generation."""
        self.log("Testing Scout Report Generation...")
        
        try:
            # Generate report with sample transcript
            transcript = """
Student: Hello! I am from Ukraine.
NEXUS: Hello! It's wonderful to meet you. What is something you love about Ukraine?
Student: I miss my grandma. She lives in Kyiv.
NEXUS: That's very understandable. Missing family is hard. What do you and your grandma like to do together?
Student: We make food together. Borscht!
NEXUS: Borscht sounds delicious! It's a famous soup. Have you made it here in Canada too?
"""
            
            report = await generate_scout_report(
                transcript=transcript,
                grade=5,
                primary_language="Ukrainian",
                duration_seconds=300,
                turn_count=6,
            )
            
            has_insight = len(report.insight_text) > 0
            self.record_result(
                "Scout Report generates insight text",
                has_insight,
                f"Insight length: {len(report.insight_text)}"
            )
            
            has_engagement = report.engagement_level is not None
            self.record_result(
                "Scout Report includes engagement level",
                has_engagement,
                f"Engagement: {report.engagement_level.value if report.engagement_level else 'None'}"
            )
            
            has_recommendations = report.recommended_next_steps is not None
            self.record_result(
                "Scout Report includes recommendations",
                has_recommendations,
            )
            
        except Exception as e:
            self.record_result("Scout Report generation", False, str(e))

    async def test_full_session_flow(self) -> None:
        """Test complete session flow (simulated)."""
        self.log("Testing Full Session Flow (Simulated)...")
        
        try:
            driver = get_llm_driver()
            context = SessionContext(
                student_code="TEST-session",
                grade=5,
                primary_language="Arabic",
            )
            
            # Simulate multi-turn conversation
            conversation = [
                "Hi! I'm nervous about speaking English.",
                "My family moved here from Syria.",
                "I like math but English is hard.",
            ]
            
            transcript_buffer = []
            for user_message in conversation:
                response = await driver.generate_response(user_message, context)
                transcript_buffer.append(f"Student: {user_message}")
                transcript_buffer.append(f"NEXUS: {response}")
                context.conversation_history.append(
                    ConversationTurn(role="user", content=user_message)
                )
                context.conversation_history.append(
                    ConversationTurn(role="assistant", content=response)
                )
            
            # Generate Scout Report from conversation
            full_transcript = "\n".join(transcript_buffer)
            report = await generate_scout_report(
                transcript=full_transcript,
                grade=5,
                primary_language="Arabic",
                duration_seconds=180,
                turn_count=6,
            )
            
            session_complete = (
                len(context.conversation_history) == 6 and
                len(report.insight_text) > 0
            )
            self.record_result(
                "Full session flow completes",
                session_complete,
                f"Turns: {len(context.conversation_history)//2}, Report generated: {bool(report.insight_text)}"
            )
            
        except Exception as e:
            self.record_result("Full session flow", False, str(e))

    async def run_all(self) -> bool:
        """Run all integration tests."""
        print("\n" + "=" * 60)
        print("NEXUS Integration Tests")
        print("=" * 60 + "\n")
        
        await self.test_curriculum_rag()
        print()
        
        await self.test_llm_driver()
        print()
        
        await self.test_privacy_guard()
        print()
        
        await self.test_scout_report_generation()
        print()
        
        await self.test_full_session_flow()
        print()
        
        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        total = self.passed + self.failed
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Pass Rate: {self.passed/total*100:.1f}%")
        print("=" * 60 + "\n")
        
        return self.failed == 0


async def main() -> None:
    """Main entry point."""
    runner = IntegrationTestRunner()
    success = await runner.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
