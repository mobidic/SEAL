#!/usr/bin/env python3
"""
Script to list all samples from runs matching a regex pattern,
and find their corresponding BAM/CRAM files in the specified path.

Usage:
    python find_samples_and_bams_by_run_regex.py <regex> <path_runs>

Examples:
    python find_samples_and_bams_by_run_regex.py "^RUN_2023.*" /data/runs
    python find_samples_and_bams_by_run_regex.py ".*_QC$" /path/to/runs
"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

import os
import re
import glob

from seal import app, db
from seal.models import Sample, Run

def find_samples_and_bams(regex_pattern, path_runs):
    """
    Find all samples from runs matching regex and their BAM/CRAM files.

    Args:
        regex_pattern (str): Regex pattern to match against run names
        path_runs (str): Base path where runs are stored

    Returns:
        dict: {run_name: {sample_name: [bam_cram_files]}}
    """
    try:
        # Compile regex (case insensitive)
        pattern = re.compile(regex_pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Error in regex: {e}")
        return {}

    with app.app_context():
        # 1. Find all runs matching the regex
        matching_runs = Run.query.filter(
            Run.name.op('~*')(regex_pattern)
        ).all()

        if not matching_runs:
            print(f"Warning: No runs found with regex: '{regex_pattern}'")
            return {}

        # 2. For each run, get all samples and find their BAM/CRAM files
        results = {}
        regex_pattern = r"_old"
        compiled_pattern = re.compile(regex_pattern)

        for run in matching_runs:
            run_path = os.path.join(path_runs, run.name, "MobiDL")
            if not os.path.exists(run_path):
                print(f"Warning: Path not found: {run_path}")
                continue

            samples = Sample.query.filter_by(run=run).all()
            run_results = {}
            for sample in samples:
                # Find all BAM and CRAM files for this sample
                all_files = glob.glob(os.path.join(run_path, f"[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]/*/{sample.samplename}/panelCapture/", f"{sample.samplename}*am"), recursive=True)

                filtered_files = [
                    f for f in all_files 
                    if not compiled_pattern.search(f)
                ]
                # Remove path, keep only filenames
                run_results[f"{sample.samplename} - {sample.id}"] = filtered_files
                if len(filtered_files) != 1:
                    print(sample)
                else:
                    sample.wf_path = os.path.dirname(filtered_files[0])
                db.session.commit()
            results[run.name] = run_results

        return results

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python find_samples_and_bams_by_run_regex.py <regex> <path_runs>")
        print("\nExamples:")
        print("  python find_samples_and_bams_by_run_regex.py '^RUN_2023.*' /data/runs")
        print("  python find_samples_and_bams_by_run_regex.py '.*_QC$' /path/to/runs")
        sys.exit(1)

    regex_pattern = sys.argv[1]
    path_runs = sys.argv[2]

    # Validate path exists
    if not os.path.exists(path_runs):
        print(f"Error: Path does not exist: {path_runs}")
        sys.exit(1)

    print(f"Searching for runs with regex: '{regex_pattern}'")
    print(f"Base path: {path_runs}\n")

    results = find_samples_and_bams(regex_pattern, path_runs)

    if not results:
        sys.exit(0)

    # Display results
    total_samples = sum(len(samples) for samples in results.values())
    total_files = sum(len(files) for samples in results.values() for files in samples.values())
    print(f"Found {len(results)} run(s) with {total_samples} samples and {total_files} BAM/CRAM files:\n")
    count = 0
    for run_name, samples in sorted(results.items()):
        print(f"Run: {run_name} ({len(samples)} samples)")
        for sample, files in sorted(samples.items()):
            if files:
                if(len(files) != 1):
                    print(f"  {sample}")
                    count +=1
                    for file in files:
                        print(f"    - {file}")
                # else:
                #     for file in files:
                #         print(f"    - {file}")
            else:
                count += 1
                print(f"  {sample}: No BAM/CRAM files found")
        print()

    # Summary
    print(f"Summary:")
    print(f"  - Matching runs: {len(results)}")
    print(f"  - Total samples: {total_samples}")
    print(f"  - Total BAM/CRAM files: {total_files}")
    print(f"  - Total no bam/cram or multiple: {count}")

if __name__ == '__main__':
    main()