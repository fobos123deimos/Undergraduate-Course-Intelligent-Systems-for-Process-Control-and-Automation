"""Run original course laboratories from any working directory."""
from pathlib import Path
import argparse
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from intelligent_control.experiments import run_unit, SLUGS

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--unit',type=int,choices=sorted(SLUGS))
    parser.add_argument('--all',action='store_true')
    args=parser.parse_args()
    if not args.all and args.unit is None:parser.error('Choose --unit N or --all')
    records={}
    for unit in sorted(SLUGS) if args.all else [args.unit]:
        result=run_unit(unit,ROOT/'laboratories'/SLUGS[unit]/'results')
        records[str(unit)]=result['summary']
        print(f'Unit {unit:02d} completed ({result["summary"]["elapsed_seconds"]:.2f} s)')
    if args.all:
        (ROOT/'docs').mkdir(exist_ok=True)
        (ROOT/'docs'/'execution.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n',encoding='utf-8')

if __name__=='__main__':main()
