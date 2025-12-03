================================================================================
EPUB READER PERFORMANCE REPORT
================================================================================

## EPUB Loading Performance
File: scratch/EPUBS/The Mamba Mentality How I Play (Bryant, Kobe) (Z-Library).epub
Size: 201.40 MB
Title: The Mamba Mentality
Authors: Kobe Bryant
Chapters: 21

Load Time: 3.86 ms
Memory After Load: 21.73 MB
Memory Increase: 0.66 MB

Target Check (< 100ms load): ✅ PASS
Target Check (< 200MB memory): ✅ PASS

## Chapter Loading Performance
Sampled: 10 / 21 chapters
Min Time: 0.72 ms
Max Time: 1.13 ms
Avg Time: 0.81 ms
Median Time: 0.75 ms

Target Check (< 100ms avg): ✅ PASS

## Image Resolution Performance
Chapters Checked: 6
Chapters with Images: 5
Total Images Found: 7
Min Resolution Time: 0.79 ms
Max Resolution Time: 25.13 ms
Avg Resolution Time: 6.95 ms
Target Check (< 100ms avg): ✅ PASS

## Memory Usage Over Time
Chapters Loaded: 20
Min Memory: 86.45 MB
Max Memory: 540.95 MB
Avg Memory: 183.11 MB
Memory Growth: 144.20 MB

Target Check (< 200MB max): ⚠️  HIGH

================================================================================
## Overall Assessment

⚠️  SOME PERFORMANCE TARGETS NOT MET

Recommendations:
- Memory usage is high. Consider implementing LRU cache for chapters.

================================================================================