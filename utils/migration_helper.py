"""
Migration Helper - Utilities for tracking and managing code migration
"""
import os
import re
import glob
from typing import List, Dict, Tuple


def find_deprecated_imports(root_dir: str = ".") -> Dict[str, List[Tuple[int, str]]]:
    """
    Find all files that still import from deprecated modules
    
    Args:
        root_dir (str): Root directory to search from
        
    Returns:
        Dict[str, List[Tuple[int, str]]]: Dictionary mapping file paths to list of (line_number, line_content) tuples
    """
    deprecated_patterns = [
        r'from\s+Final_Video\s+import',
        r'import\s+Final_Video',
        r'Final_Video\.',
    ]
    
    results = {}
    
    # Search all Python files
    for py_file in glob.glob(os.path.join(root_dir, "**/*.py"), recursive=True):
        # Skip the deprecated file itself and migration helper
        if py_file.endswith(('Final_Video.py', 'migration_helper.py')):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            matches = []
            for line_num, line in enumerate(lines, 1):
                for pattern in deprecated_patterns:
                    if re.search(pattern, line):
                        matches.append((line_num, line.strip()))
                        
            if matches:
                results[py_file] = matches
                
        except Exception as e:
            print(f"Warning: Could not read {py_file}: {e}")
            
    return results


def generate_migration_report() -> str:
    """
    Generate a comprehensive migration report
    
    Returns:
        str: Formatted migration report
    """
    deprecated_usage = find_deprecated_imports()
    
    report = []
    report.append("=" * 60)
    report.append("MIGRATION REPORT - Final_Video.py Deprecation")
    report.append("=" * 60)
    report.append("")
    
    if not deprecated_usage:
        report.append("✅ SUCCESS: No deprecated imports found!")
        report.append("All files have been migrated to use services.video_finalization")
        report.append("")
        report.append("Next steps:")
        report.append("- Monitor usage for a few days")
        report.append("- Remove Final_Video.py wrapper when ready")
        report.append("- Update build_command.txt to remove Final_Video import")
    else:
        report.append(f"⚠️  FOUND {len(deprecated_usage)} files still using deprecated imports:")
        report.append("")
        
        for file_path, matches in deprecated_usage.items():
            report.append(f"📁 {file_path}")
            for line_num, line_content in matches:
                report.append(f"   Line {line_num}: {line_content}")
            report.append("")
            
        report.append("RECOMMENDED ACTIONS:")
        report.append("1. Update the above files to use:")
        report.append("   from services.video_finalization import merge_video_subtitle")
        report.append("2. Test the updated imports")
        report.append("3. Re-run this report to verify migration")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


def check_build_configuration() -> List[str]:
    """
    Check build configuration files for deprecated references
    
    Returns:
        List[str]: List of issues found
    """
    issues = []
    
    # Check build_command.txt
    build_file = "build_command.txt"
    if os.path.exists(build_file):
        try:
            with open(build_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'Final_Video' in content:
                issues.append(f"build_command.txt still references Final_Video")
                issues.append("  Consider removing --hidden-import=Final_Video after migration")
                
        except Exception as e:
            issues.append(f"Could not read {build_file}: {e}")
    
    # Check spec files
    for spec_file in glob.glob("*.spec"):
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'Final_Video' in content:
                issues.append(f"{spec_file} still references Final_Video")
                
        except Exception as e:
            issues.append(f"Could not read {spec_file}: {e}")
    
    return issues


def get_migration_status() -> Dict[str, any]:
    """
    Get comprehensive migration status
    
    Returns:
        Dict[str, any]: Migration status information
    """
    deprecated_usage = find_deprecated_imports()
    build_issues = check_build_configuration()
    
    status = {
        "migration_complete": len(deprecated_usage) == 0,
        "files_with_deprecated_imports": len(deprecated_usage),
        "deprecated_usage_details": deprecated_usage,
        "build_configuration_issues": build_issues,
        "ready_for_cleanup": len(deprecated_usage) == 0 and len(build_issues) == 0
    }
    
    return status


if __name__ == "__main__":
    # Generate and print migration report
    print(generate_migration_report())
    
    # Check build configuration
    build_issues = check_build_configuration()
    if build_issues:
        print("\nBUILD CONFIGURATION ISSUES:")
        for issue in build_issues:
            print(f"  {issue}")
