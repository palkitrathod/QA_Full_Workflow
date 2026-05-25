import argparse
import sys
from dotenv import load_dotenv

# Load environment variables before importing tools
load_dotenv()

from tools.orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(description="QA Workflow AI Agent - Automated Pipeline")
    
    # Input modes (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--jira", type=str, help="JIRA Ticket ID (Mode A)")
    group.add_argument("--document", type=str, help="Path to PRD/BRD document (Mode B)")
    
    # Run type
    parser.add_argument("--regression", action="store_true", help="Run as regression (skips human review)")
    
    # Debug/Test
    parser.add_argument("--dry-run", action="store_true", help="Run up to script generation without execution or external writes")
    
    args = parser.parse_args()
    
    input_mode = "jira" if args.jira else "document"
    run_type = "regression" if args.regression else "new_feature"
    source_id = args.jira if args.jira else None
    doc_path = args.document if args.document else None
    
    try:
        orchestrator = Orchestrator(
            input_mode=input_mode,
            run_type=run_type,
            source_id=source_id,
            document_path=doc_path
        )
        orchestrator.run_pipeline(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n[ABORT] Pipeline aborted by user.")
        sys.exit(130)

if __name__ == "__main__":
    main()
