#!/usr/bin/env python3
"""Quick test script for the deployed AgentCore complaints agent."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


SAMPLE_COMPLAINT = """
Customer: Hi, I'm calling about my credit card account. I'm extremely frustrated right now.
Agent: I'm sorry to hear that. What seems to be the problem?
Customer: I was charged an overdraft fee even though I had sufficient funds in my account! 
This is unacceptable. I've been a loyal customer for years and this is how you treat me.
Agent: I sincerely apologize for this experience. Let me look into your account.
Customer: I want this fee reversed immediately. This is the worst banking experience I've ever had. 
I'm so disappointed with your institution. I'm considering closing all my accounts.
Agent: I completely understand your frustration. Let me review the transaction and resolve this for you.
""".strip()

SAMPLE_NORMAL = """
Customer: Hello, I'm calling to check on the status of my mortgage application.
Agent: Of course! Can I have your application reference number please?
Customer: Yes, it's APP-78234.
Agent: Thank you. I can see your application is in the final review stage and should be approved by Friday.
Customer: That's great, thank you for the update!
Agent: You're welcome. Is there anything else I can help you with today?
Customer: No, that's all. Have a great day!
Agent: You too! Thank you for calling.
""".strip()


def invoke_agent(transcript: str, config_override: dict = None, local: bool = False) -> dict:
    payload = {"transcript": transcript}
    if config_override:
        payload["config_override"] = config_override
    
    payload_json = json.dumps(payload)
    
    cmd = ["agentcore", "invoke"]
    if local:
        cmd.append("--local")
    cmd.append(payload_json)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    combined_output = result.stdout + result.stderr
    
    if result.returncode != 0:
        print(f"\n❌ Invocation failed (exit code {result.returncode})", file=sys.stderr)
        print(combined_output, file=sys.stderr)
        sys.exit(1)
    
    response_marker = "Response:\n"
    if response_marker in combined_output:
        json_start = combined_output.find(response_marker) + len(response_marker)
        json_str = combined_output[json_start:].strip()
        json_str = ' '.join(json_str.split())
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    return {"raw_output": combined_output}


def print_result(response: dict):
    print("\n" + "=" * 60)
    print("AGENT RESPONSE")
    print("=" * 60)
    
    if "error" in response or response.get("status") == "error":
        print(f"\n❌ Error: {response.get('error_message', response.get('error', 'Unknown error'))}")
        return
    
    result = response.get("result", response)
    
    is_complaint = result.get("is_complaint", False)
    summary = result.get("summary", "No summary")
    
    status_icon = "🚨" if is_complaint else "✅"
    print(f"\n{status_icon} Is Complaint: {is_complaint}")
    print(f"\n📝 Summary: {summary}")
    
    if is_complaint and result.get("complaint"):
        complaint = result["complaint"]
        print("\n--- Complaint Details ---")
        print(f"Classification: {complaint.get('classification_result', 'N/A')}")
        print(f"Matched Criteria: {complaint.get('matched_criteria', [])}")
        
        if result.get("complaint_response"):
            cr = result["complaint_response"]
            print(f"\nSeverity: {cr.get('severity', 'N/A')}")
            print(f"Category: {cr.get('category', 'N/A')}")
            
            if cr.get("actions_taken"):
                print("\nActions Taken:")
                for action in cr["actions_taken"]:
                    print(f"  • {action}")
            
            if cr.get("next_steps"):
                print("\nNext Steps:")
                for step in cr["next_steps"]:
                    print(f"  • {step}")
    
    print("\n" + "=" * 60)


def check_status():
    result = subprocess.run(
        ["agentcore", "status"],
        capture_output=True,
        text=True
    )
    print(result.stdout or result.stderr or "Status check complete")


def main():
    parser = argparse.ArgumentParser(
        description="Test the deployed AgentCore complaints agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/test_deployed.py --complaint     # Test with complaint sample
  python3 scripts/test_deployed.py --normal        # Test with non-complaint sample
  python3 scripts/test_deployed.py -f input.txt    # Test with file content
  python3 scripts/test_deployed.py "Customer: ..." # Test with inline transcript
  python3 scripts/test_deployed.py --status        # Check deployment status
  python3 scripts/test_deployed.py --raw           # Output raw JSON response
        """
    )
    
    parser.add_argument("transcript", nargs="?", help="Transcript text to analyze")
    parser.add_argument("-c", "--complaint", action="store_true", help="Use sample complaint transcript")
    parser.add_argument("-n", "--normal", action="store_true", help="Use sample non-complaint transcript")
    parser.add_argument("-f", "--file", type=Path, help="Read transcript from file")
    parser.add_argument("-s", "--status", action="store_true", help="Check agent deployment status")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON response")
    parser.add_argument("--config", type=Path, help="JSON file with config_override")
    parser.add_argument("-l", "--local", action="store_true", help="Invoke local container instead of deployed agent")
    
    args = parser.parse_args()
    
    if args.status:
        check_status()
        return
    
    transcript = None
    if args.complaint:
        transcript = SAMPLE_COMPLAINT
        print("Using sample COMPLAINT transcript")
    elif args.normal:
        transcript = SAMPLE_NORMAL
        print("Using sample NON-COMPLAINT transcript")
    elif args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        transcript = args.file.read_text()
        print(f"Using transcript from: {args.file}")
    elif args.transcript:
        transcript = args.transcript
        print("Using provided transcript")
    else:
        parser.print_help()
        sys.exit(0)
    
    config_override = None
    if args.config:
        if not args.config.exists():
            print(f"Error: Config file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        config_override = json.loads(args.config.read_text())
    
    print(f"\nTranscript preview: {transcript[:150]}...")
    print("\nInvoking agent...")
    
    response = invoke_agent(transcript, config_override, local=args.local)
    
    if args.raw:
        print(json.dumps(response, indent=2))
    else:
        print_result(response)


if __name__ == "__main__":
    main()
