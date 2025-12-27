#!/usr/bin/env python3
"""Verify PractAI setup and configuration."""

import sys
from pathlib import Path

def verify_imports():
    """Verify all required modules can be imported."""
    print("🔍 Verifying imports...")

    try:
        import langchain
        print("  ✓ langchain")
    except ImportError as e:
        print(f"  ✗ langchain: {e}")
        return False

    try:
        import langgraph
        print("  ✓ langgraph")
    except ImportError as e:
        print(f"  ✗ langgraph: {e}")
        return False

    try:
        import fastapi
        print("  ✓ fastapi")
    except ImportError as e:
        print(f"  ✗ fastapi: {e}")
        return False

    try:
        import pydantic
        print("  ✓ pydantic")
    except ImportError as e:
        print(f"  ✗ pydantic: {e}")
        return False

    try:
        import yaml
        print("  ✓ yaml")
    except ImportError as e:
        print(f"  ✗ yaml: {e}")
        return False

    return True


def verify_structure():
    """Verify project structure."""
    print("\n🔍 Verifying project structure...")

    required_files = [
        "config/supervisors.yaml",
        "config/loader.py",
        "config/llm_provider.py",
        "models/schemas.py",
        "agents/supervisor.py",
        "agents/visibility.py",
        "agents/meeting.py",
        "api/main.py",
        "frontend/index.html",
        ".env",
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (missing)")
            all_exist = False

    return all_exist


def verify_config():
    """Verify configuration files."""
    print("\n🔍 Verifying configuration...")

    try:
        from config.loader import load_supervisor_configs
        supervisors = load_supervisor_configs("config/supervisors.yaml")
        print(f"  ✓ Loaded {len(supervisors)} supervisor configurations")

        for sup in supervisors:
            print(f"    - {sup.name} ({sup.role})")

        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def verify_env():
    """Verify environment variables."""
    print("\n🔍 Verifying environment...")

    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm_provider = os.getenv("LLM_PROVIDER", "not set")
    cross_talk = os.getenv("CROSS_TALK_PROBABILITY", "not set")
    checkpoint = os.getenv("VISIBILITY_CHECKPOINT_INTERVAL", "not set")

    print(f"  • LLM Provider: {llm_provider}")
    print(f"  • Cross-talk probability: {cross_talk}")
    print(f"  • Visibility checkpoint interval: {checkpoint}")

    if llm_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key and api_key != "your_openai_key_here":
            print("  ✓ OpenAI API key is set")
            return True
        else:
            print("  ⚠️  OpenAI API key not set (update .env file)")
            return False

    return True


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("PractAI Setup Verification")
    print("=" * 60)

    checks = [
        ("Imports", verify_imports),
        ("Structure", verify_structure),
        ("Configuration", verify_config),
        ("Environment", verify_env),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed with error: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✅ All checks passed! PractAI is ready to run.")
        print("\nNext steps:")
        print("  1. Update .env with your API key")
        print("  2. Run: python api/main.py")
        print("  3. Open: http://localhost:8000")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
