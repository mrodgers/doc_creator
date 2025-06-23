#!/usr/bin/env python3
"""
Feedback and Gap Analysis Demo

Demonstrates the new user feedback and gap analysis capabilities
for the AI documentation generation system.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_doc_gen.ui.gap_dashboard import GapDashboard, GapStatus
from ai_doc_gen.feedback.feedback_collector import FeedbackCollector, DocumentFeedback, FeedbackType, FeedbackRating


def demo_gap_analysis():
    """Demonstrate gap analysis functionality."""
    print("🔍 GAP ANALYSIS DEMO")
    print("=" * 50)
    
    # Initialize gap dashboard
    dashboard = GapDashboard("outputs")
    
    # Get feedback summary
    summary = dashboard.get_feedback_summary()
    print(f"📊 Gap Analysis Summary:")
    print(f"   Total Gaps: {summary['total_gaps']}")
    print(f"   Resolved: {summary['resolved_gaps']}")
    print(f"   Resolution Rate: {summary['resolution_rate']:.1f}%")
    print(f"   Average Rating: {summary['average_rating']:.1f}")
    
    # Export learning data
    learning_data = dashboard.export_learning_data()
    print(f"\n📈 Learning Data:")
    print(f"   Feedback Insights: {len(learning_data['feedback_insights'])}")
    
    if learning_data['feedback_insights']:
        print("   Recent Feedback:")
        for insight in learning_data['feedback_insights'][:3]:
            print(f"     - {insight.get('feedback', 'No feedback')[:50]}...")
    
    print("\n✅ Gap analysis demo completed!")


def demo_feedback_collection():
    """Demonstrate feedback collection functionality."""
    print("\n📝 FEEDBACK COLLECTION DEMO")
    print("=" * 50)
    
    # Initialize feedback collector
    collector = FeedbackCollector()
    
    # Add some sample feedback
    sample_feedback = DocumentFeedback(
        document_id="demo_doc_001",
        document_name="Cisco Nexus 9000 Installation Guide",
        feedback_type=FeedbackType.QUALITY,
        rating=FeedbackRating.VERY_GOOD,
        comments="The documentation is comprehensive and well-structured. Could use more diagrams."
    )
    
    collector.add_document_feedback(sample_feedback)
    
    # Add accuracy feedback
    accuracy_feedback = DocumentFeedback(
        document_id="demo_doc_001",
        document_name="Cisco Nexus 9000 Installation Guide",
        feedback_type=FeedbackType.ACCURACY,
        rating=FeedbackRating.EXCELLENT,
        comments="All technical details are accurate and up-to-date."
    )
    
    collector.add_document_feedback(accuracy_feedback)
    
    # Get feedback summary
    summary = collector.get_feedback_summary()
    print(f"📊 Feedback Summary:")
    print(f"   Total Feedback: {summary['total_feedback']}")
    print(f"   Average Rating: {summary['average_rating']:.1f}")
    print(f"   Feedback Types: {list(summary['feedback_by_type'].keys())}")
    
    # Get learning insights
    insights = collector.get_learning_insights()
    print(f"\n🧠 Learning Insights:")
    print(f"   Document Performance: {len(insights['document_performance'])} documents")
    print(f"   Common Issues: {len(insights['common_issues'])}")
    print(f"   Improvement Areas: {len(insights['improvement_areas'])}")
    print(f"   Success Patterns: {len(insights['success_patterns'])}")
    
    # Generate feedback HTML
    feedback_html = collector.generate_feedback_html("demo_doc_001", "Cisco Nexus 9000 Installation Guide")
    print(f"\n🌐 Generated Feedback Widget HTML: {len(feedback_html)} characters")
    
    print("\n✅ Feedback collection demo completed!")


def demo_integration():
    """Demonstrate integration between gap analysis and feedback."""
    print("\n🔗 INTEGRATION DEMO")
    print("=" * 50)
    
    # Initialize both systems
    gap_dashboard = GapDashboard("outputs")
    feedback_collector = FeedbackCollector()
    
    # Simulate a workflow
    print("🔄 Simulating user workflow:")
    print("   1. User processes a document")
    print("   2. System identifies gaps")
    print("   3. User provides feedback on gaps")
    print("   4. System learns from feedback")
    
    # Update a gap status with feedback
    gap_dashboard.update_gap_status(
        gap_id="demo_gap_001",
        status=GapStatus.RESOLVED,
        feedback="This gap was resolved by adding missing installation steps",
        rating=5
    )
    
    # Add document feedback
    doc_feedback = DocumentFeedback(
        document_id="demo_doc_002",
        document_name="Demo Document",
        feedback_type=FeedbackType.COMPLETENESS,
        rating=FeedbackRating.GOOD,
        comments="The document covers most requirements but could be more detailed in the troubleshooting section."
    )
    
    feedback_collector.add_document_feedback(doc_feedback)
    
    # Show combined insights
    gap_summary = gap_dashboard.get_feedback_summary()
    feedback_summary = feedback_collector.get_feedback_summary()
    
    print(f"\n📊 Combined Insights:")
    print(f"   Gap Resolution Rate: {gap_summary['resolution_rate']:.1f}%")
    print(f"   Document Feedback Count: {feedback_summary['total_feedback']}")
    print(f"   Overall System Rating: {feedback_summary['average_rating']:.1f}")
    
    print("\n✅ Integration demo completed!")


def main():
    """Run all demos."""
    print("🚀 AI DOCUMENTATION GENERATION - FEEDBACK & GAP ANALYSIS DEMO")
    print("=" * 70)
    print("This demo showcases the new user feedback and gap analysis capabilities")
    print("that help improve the system through user input and learning retention.\n")
    
    try:
        demo_gap_analysis()
        demo_feedback_collection()
        demo_integration()
        
        print("\n🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("\n📋 Next Steps:")
        print("   1. Access the web UI at http://localhost:5476")
        print("   2. Navigate to 'Gap Analysis' to see interactive gap dashboard")
        print("   3. Upload documents and provide feedback")
        print("   4. Export learning data for system improvement")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 