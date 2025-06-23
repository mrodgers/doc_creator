#!/usr/bin/env python3
"""
UI Integration Test

Tests the Flask web UI integration with the AI pipeline using real documents.
"""

import json
from pathlib import Path
import os

from ai_doc_gen.ui.app import app, process_document


def test_ui_pipeline_integration():
    """Test the UI pipeline integration with real documents."""
    print("Testing UI Pipeline Integration...")

    # Test with real documents
    test_files = [
        "functional_spec.docx",
        "installation_guide.pdf"
    ]

    results = []

    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\nProcessing: {test_file}")
            try:
                # Test the process_document function directly
                result = process_document(test_file)
                results.append(result)

                print(f"  ✓ Success: Job ID {result['job_id']}")
                print(f"  ✓ Status: {result['status']}")
                print(f"  ✓ Output: {result['output_dir']}")

                # Check if output files exist
                output_dir = Path(result['output_dir'])
                if output_dir.exists():
                    md_file = output_dir / "generated_draft.md"
                    json_file = output_dir / "generated_draft.json"

                    if md_file.exists():
                        print(f"  ✓ Markdown draft: {md_file}")
                    if json_file.exists():
                        print(f"  ✓ JSON draft: {json_file}")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append({
                    'filename': test_file,
                    'status': 'error',
                    'error': str(e)
                })
        else:
            print(f"\nSkipping: {test_file} (not found)")

    # Save test results
    with open('ui_integration_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\nTest completed. Results saved to: ui_integration_test_results.json")
    return results

def test_flask_app():
    """Test the Flask app can start without errors."""
    print("\nTesting Flask App...")

    try:
        # Test that the app can be created
        with app.test_client() as client:
            # Test main routes
            response = client.get('/')
            assert response.status_code == 200
            print("  ✓ Main page loads")

            response = client.get('/upload')
            assert response.status_code == 200
            print("  ✓ Upload page loads")

        print("  ✓ Flask app test passed")
        return True

    except Exception as e:
        print(f"  ✗ Flask app test failed: {e}")
        return False

if __name__ == "__main__":
    print("UI Integration Test Suite")
    print("=" * 50)

    # Test Flask app
    flask_ok = test_flask_app()

    # Test pipeline integration
    pipeline_results = test_ui_pipeline_integration()

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Flask App: {'✓ PASS' if flask_ok else '✗ FAIL'}")

    successful_jobs = [r for r in pipeline_results if r.get('status') == 'completed']
    print(f"Pipeline Jobs: {len(successful_jobs)}/{len(pipeline_results)} successful")

    if successful_jobs:
        print("\nSuccessful jobs:")
        for job in successful_jobs:
            print(f"  - {job['filename']}: {job['job_id']}")

    print("\nUI is ready for testing at: http://localhost:" + os.getenv('WEB_PORT', '5476'))
    print("Run: uv run python -m ai_doc_gen.ui.app")
