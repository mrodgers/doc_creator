import json
import argparse

def load_specs(path, key="value"):
    data = json.load(open(path))
    specs = {}
    for entry in data:
        name = entry.get("spec_item")
        val  = entry.get(key, "")
        if name:
            specs[name] = val.strip()
    return specs

def main():
    parser = argparse.ArgumentParser(description="Diff corrected vs. ground-truth specs")
    parser.add_argument("--corrected",  required=True, help="Path to corrected_specs.json")
    parser.add_argument("--ground_truth",required=True, help="Path to ground_truth_specs.json")
    parser.add_argument("--key",         default="value",   help="Field name to read in corrected file")
    args = parser.parse_args()

    corrected = load_specs(args.corrected, key=args.key)
    ground    = load_specs(args.ground_truth)

    print("Mismatched specs:")
    print("-----------------")
    count = 0
    for item, gt_val in ground.items():
        corr_val = corrected.get(item, "<MISSING>")
        if corr_val.lower() != gt_val.lower():
            count += 1
            print(f"- {item}:")
            print(f"    ground_truth: {gt_val!r}")
            print(f"    corrected   : {corr_val!r}\n")

    if count == 0:
        print("All values match perfectly!")
    else:
        print(f"Total mismatches: {count} of {len(ground)} specs")

if __name__ == "__main__":
    main() 