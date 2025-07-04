#!/usr/bin/env python3
"""
Detailed analysis of subtitle timing synchronization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_subtitle_timing_detailed():
    print("🔍 DETAILED SUBTITLE TIMING ANALYSIS")
    print("="*80)
    
    # Test files from previous sync test
    test_files = {
        "Adam (Kokoro)": "test_outputs/sync_test_adam_subtitles.ass",
        "Guy (Edge)": "test_outputs/sync_test_guy_subtitles.ass", 
        "Aria (Edge)": "test_outputs/sync_test_aria_subtitles.ass",
        "Heart (Kokoro)": "test_outputs/sync_test_heart_subtitles.ass"
    }
    
    original_text = "At exactly 7:42 a.m. on April 3rd, 2025, trading was temporarily halted on the Tokyo Stock Exchange due to an unexpected 0.87% drop in the Nikkei 225 within the first 12 minutes of market opening."
    
    print(f"📝 Original Text: {original_text}")
    print(f"📊 Word Count: {len(original_text.split())} words")
    
    timing_analysis = {}
    
    for voice_name, subtitle_file in test_files.items():
        print(f"\n🎤 Analyzing {voice_name}")
        print("-" * 60)
        
        analysis = analyze_single_subtitle_file(subtitle_file, original_text)
        timing_analysis[voice_name] = analysis
        
        if analysis['success']:
            print(f"   📊 Lines: {analysis['total_lines']}")
            print(f"   ⏱️  Duration: {analysis['first_start']:.2f}s - {analysis['last_end']:.2f}s ({analysis['total_duration']:.2f}s)")
            print(f"   📈 Avg line duration: {analysis['avg_duration']:.2f}s")
            print(f"   🎯 Words per second: {analysis['words_per_second']:.1f}")
            
            if analysis['timing_issues']:
                print(f"   ⚠️  Timing issues: {', '.join(analysis['timing_issues'])}")
            else:
                print(f"   ✅ No timing issues detected")
        else:
            print(f"   ❌ Analysis failed: {analysis['error']}")
    
    # Comparative analysis
    print(f"\n📊 COMPARATIVE TIMING ANALYSIS")
    print("="*80)
    generate_timing_comparison(timing_analysis)

def analyze_single_subtitle_file(subtitle_file: str, original_text: str):
    """Analyze timing patterns in a single subtitle file"""
    
    try:
        if not os.path.exists(subtitle_file):
            return {'success': False, 'error': f'File not found: {subtitle_file}'}
        
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract dialogue lines
        dialogue_lines = [line for line in content.split('\n') if line.startswith('Dialogue:')]
        
        if not dialogue_lines:
            return {'success': False, 'error': 'No dialogue lines found'}
        
        # Parse timing data
        timings = []
        all_subtitle_text = []
        
        for line in dialogue_lines:
            parts = line.split(',')
            if len(parts) >= 10:
                start_time = parse_ass_time(parts[1])
                end_time = parse_ass_time(parts[2])
                text = ','.join(parts[9:]).strip()
                
                timings.append({
                    'start': start_time,
                    'end': end_time,
                    'duration': end_time - start_time,
                    'text': text
                })
                all_subtitle_text.append(text)
        
        if not timings:
            return {'success': False, 'error': 'No valid timings found'}
        
        # Calculate metrics
        first_start = min(t['start'] for t in timings)
        last_end = max(t['end'] for t in timings)
        total_duration = last_end - first_start
        avg_duration = sum(t['duration'] for t in timings) / len(timings)
        
        # Word count analysis
        subtitle_word_count = len(' '.join(all_subtitle_text).split())
        original_word_count = len(original_text.split())
        words_per_second = subtitle_word_count / total_duration if total_duration > 0 else 0
        
        # Check for timing issues
        timing_issues = []
        
        # Check for overlaps
        for i in range(len(timings) - 1):
            if timings[i]['end'] > timings[i + 1]['start']:
                timing_issues.append(f"Overlap at line {i+1}-{i+2}")
        
        # Check for large gaps
        for i in range(len(timings) - 1):
            gap = timings[i + 1]['start'] - timings[i]['end']
            if gap > 1.0:  # Gap > 1 second
                timing_issues.append(f"Large gap ({gap:.2f}s) after line {i+1}")
        
        # Check for very short/long lines
        for i, timing in enumerate(timings):
            if timing['duration'] < 0.3:
                timing_issues.append(f"Very short line {i+1} ({timing['duration']:.2f}s)")
            elif timing['duration'] > 5.0:
                timing_issues.append(f"Very long line {i+1} ({timing['duration']:.2f}s)")
        
        # Text preservation check
        subtitle_text_combined = ' '.join(all_subtitle_text)
        
        # Check for key terms preservation
        key_terms = ["7:42 a.m.", "April 3rd", "2025", "0.87%", "Nikkei 225", "12 minutes"]
        preserved_terms = [term for term in key_terms if term in subtitle_text_combined]
        term_preservation_rate = len(preserved_terms) / len(key_terms) * 100
        
        return {
            'success': True,
            'total_lines': len(timings),
            'first_start': first_start,
            'last_end': last_end,
            'total_duration': total_duration,
            'avg_duration': avg_duration,
            'subtitle_word_count': subtitle_word_count,
            'original_word_count': original_word_count,
            'words_per_second': words_per_second,
            'timing_issues': timing_issues,
            'preserved_terms': preserved_terms,
            'term_preservation_rate': term_preservation_rate,
            'timings': timings,
            'subtitle_text': subtitle_text_combined
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_ass_time(time_str: str) -> float:
    """Parse ASS time format (H:MM:SS.CC) to seconds"""
    try:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        centiseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
        return total_seconds
    except:
        return 0.0

def generate_timing_comparison(timing_analysis):
    """Generate comparative analysis across all voices"""
    
    successful_analyses = {k: v for k, v in timing_analysis.items() if v.get('success')}
    
    if not successful_analyses:
        print("❌ No successful analyses to compare")
        return
    
    print(f"📈 TIMING METRICS COMPARISON:")
    print(f"{'Voice':<15} {'Lines':<6} {'Duration':<10} {'Avg/Line':<9} {'WPS':<6} {'Issues':<8} {'Terms':<6}")
    print("-" * 70)
    
    for voice, analysis in successful_analyses.items():
        issues_count = len(analysis['timing_issues'])
        term_rate = analysis['term_preservation_rate']
        
        print(f"{voice:<15} {analysis['total_lines']:<6} "
              f"{analysis['total_duration']:<10.2f} {analysis['avg_duration']:<9.2f} "
              f"{analysis['words_per_second']:<6.1f} {issues_count:<8} {term_rate:<6.0f}%")
    
    # Find best and worst performers
    if len(successful_analyses) > 1:
        # Best timing consistency (fewest issues)
        best_timing = min(successful_analyses.items(), key=lambda x: len(x[1]['timing_issues']))
        worst_timing = max(successful_analyses.items(), key=lambda x: len(x[1]['timing_issues']))
        
        # Best term preservation
        best_terms = max(successful_analyses.items(), key=lambda x: x[1]['term_preservation_rate'])
        
        print(f"\n🏆 PERFORMANCE HIGHLIGHTS:")
        print(f"   Best Timing: {best_timing[0]} ({len(best_timing[1]['timing_issues'])} issues)")
        print(f"   Worst Timing: {worst_timing[0]} ({len(worst_timing[1]['timing_issues'])} issues)")
        print(f"   Best Terms: {best_terms[0]} ({best_terms[1]['term_preservation_rate']:.0f}% preserved)")
    
    # Detailed timing issues breakdown
    print(f"\n⚠️  DETAILED TIMING ISSUES:")
    for voice, analysis in successful_analyses.items():
        if analysis['timing_issues']:
            print(f"   {voice}:")
            for issue in analysis['timing_issues']:
                print(f"      • {issue}")
        else:
            print(f"   {voice}: ✅ No issues")
    
    # Sample timing comparison (first 3 lines)
    print(f"\n📋 SAMPLE TIMING COMPARISON (First 3 Lines):")
    for voice, analysis in successful_analyses.items():
        print(f"\n   {voice}:")
        for i, timing in enumerate(analysis['timings'][:3]):
            print(f"      Line {i+1}: {timing['start']:.2f}s-{timing['end']:.2f}s ({timing['duration']:.2f}s) \"{timing['text']}\"")

if __name__ == "__main__":
    analyze_subtitle_timing_detailed()
